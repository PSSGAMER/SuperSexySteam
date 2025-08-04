# depot_cache_manager.py
#
# A module for managing Steam depot cache files (.manifest files).
# Handles copying manifest files from data folders to Steam's depot cache
# and removing them during uninstallation.

import logging
from pathlib import Path
import shutil
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


def copy_manifests_for_appid(steam_path: str, app_id: str, data_folder: str) -> Dict[str, int]:
    """
    Copy all manifest files for a specific AppID from data folder to Steam depot cache.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID
        data_folder (str): Path to folder containing manifest files
        
    Returns:
        Dict[str, int]: Statistics with 'copied_count' and 'skipped_count'
    """
    logger.info(f"Copying manifest files for AppID {app_id} from {data_folder}")
    logger.debug(f"Steam path: {steam_path}")
    
    stats = {'copied_count': 0, 'skipped_count': 0}
    
    try:
        # Convert to Path objects
        steam_path_obj = Path(steam_path)
        data_folder_obj = Path(data_folder)
        
        logger.debug(f"Data folder path: {data_folder_obj}")
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        logger.debug(f"Depot cache path: {depot_cache_path}")
        
        if not depot_cache_path.exists():
            try:
                logger.info(f"Creating depot cache directory: {depot_cache_path}")
                depot_cache_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created depot cache directory successfully")
            except Exception as e:
                logger.error(f"Failed to create depot cache directory: {e}")
                logger.debug("Depot cache creation exception:", exc_info=True)
                return stats
        
        # Find all manifest files in the data folder
        manifest_files = list(data_folder_obj.glob("*.manifest"))
        logger.debug(f"Found {len(manifest_files)} manifest files in data folder")
        
        if not manifest_files:
            logger.info(f"No manifest files found for AppID {app_id} in {data_folder_obj}")
            return stats
        
        # Copy each manifest file
        for manifest_file in manifest_files:
            try:
                destination = depot_cache_path / manifest_file.name
                logger.debug(f"Processing manifest file: {manifest_file.name}")
                
                # Check if file already exists and is identical
                if destination.exists():
                    if manifest_file.stat().st_size == destination.stat().st_size:
                        # Files are same size, assume they're identical
                        stats['skipped_count'] += 1
                        logger.debug(f"Skipping manifest {manifest_file.name} (already exists with same size)")
                        continue
                
                # Copy the file
                logger.debug(f"Copying {manifest_file.name} to depot cache")
                shutil.copy2(manifest_file, destination)
                stats['copied_count'] += 1
                logger.info(f"Copied manifest: {manifest_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to copy manifest {manifest_file.name}: {e}")
                logger.debug(f"Manifest copy exception for {manifest_file.name}:", exc_info=True)
        
        logger.info(f"Depot cache update complete for AppID {app_id}: {stats['copied_count']} copied, {stats['skipped_count']} skipped")
        
    except Exception as e:
        logger.error(f"Failed to update depot cache for AppID {app_id}: {e}")
        logger.debug("Depot cache update exception:", exc_info=True)
    
    return stats


def remove_manifests_for_appid(steam_path: str, manifest_filenames: List[str]) -> Dict[str, int]:
    """
    Remove specific manifest files from Steam depot cache based on a provided list of filenames.

    Args:
        steam_path (str): Path to Steam installation directory.
        manifest_filenames (List[str]): A list of manifest filenames to remove.
        
    Returns:
        Dict[str, int]: Statistics with 'removed_count'.
    """
    logger.info(f"Removing {len(manifest_filenames)} manifest files from depot cache")
    logger.debug(f"Steam path: {steam_path}")
    logger.debug(f"Manifest files to remove: {manifest_filenames}")
    
    stats = {'removed_count': 0}
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        logger.debug(f"Depot cache path: {depot_cache_path}")
        
        if not depot_cache_path.exists():
            logger.info(f"Depot cache directory does not exist: {depot_cache_path}")
            return stats
        
        if not manifest_filenames:
            logger.info("No manifest files specified for removal")
            return stats
            
        # Remove each specified manifest file
        for filename in manifest_filenames:
            manifest_file_path = depot_cache_path / filename
            logger.debug(f"Processing manifest file for removal: {filename}")
            
            if manifest_file_path.exists():
                try:
                    logger.debug(f"Removing manifest file: {manifest_file_path}")
                    manifest_file_path.unlink()
                    stats['removed_count'] += 1
                    logger.info(f"Removed manifest: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove manifest {filename}: {e}")
                    logger.debug(f"Manifest removal exception for {filename}:", exc_info=True)
            else:
                logger.warning(f"Manifest file not found in depotcache, skipping: {filename}")
        
        logger.info(f"Depot cache cleanup complete: {stats['removed_count']} specified manifest(s) removed")
        
    except Exception as e:
        logger.error(f"Failed to cleanup depot cache: {e}")
        logger.debug("Depot cache cleanup exception:", exc_info=True)
    
    return stats


def get_depot_cache_info(steam_path: str) -> Dict[str, any]:
    """
    Get information about the depot cache directory.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Information about depot cache
    """
    logger.debug(f"Getting depot cache info for Steam path: {steam_path}")
    
    info = {
        'path': '',
        'exists': False,
        'manifest_count': 0,
        'total_size_mb': 0.0
    }
    
    try:
        # Convert to Path object
        steam_path_obj = Path(steam_path)
        depot_cache_path = steam_path_obj / 'depotcache'
        
        info['path'] = str(depot_cache_path)
        info['exists'] = depot_cache_path.exists()
        
        logger.debug(f"Depot cache path: {depot_cache_path}, exists: {info['exists']}")
        
        if info['exists']:
            manifest_files = list(depot_cache_path.glob("*.manifest"))
            info['manifest_count'] = len(manifest_files)
            
            logger.debug(f"Found {info['manifest_count']} manifest files")
            
            total_size = 0
            for manifest_file in manifest_files:
                try:
                    total_size += manifest_file.stat().st_size
                except Exception as e:
                    logger.debug(f"Could not get size for {manifest_file.name}: {e}")
                    pass  # Skip files we can't read
            
            info['total_size_mb'] = total_size / (1024 * 1024)
            logger.debug(f"Total depot cache size: {info['total_size_mb']:.2f} MB")
    
    except Exception as e:
        logger.error(f"Failed to get depot cache info: {e}")
        logger.debug("Get depot cache info exception:", exc_info=True)
    
    logger.info(f"Depot cache info: {info['manifest_count']} files, {info['total_size_mb']:.2f} MB")
    return info


def clear_all_depot_cache(steam_path: str) -> Dict[str, int]:
    """
    Clear all manifest files from Steam depot cache.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, int]: Statistics with 'removed_count'
    """
    logger.info("Clearing all manifest files from depot cache")
    logger.debug(f"Steam path: {steam_path}")
    
    stats = {'removed_count': 0}
    
    try:
        # Convert to Path object
        steam_path_obj = Path(steam_path)
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        logger.debug(f"Depot cache path: {depot_cache_path}")
        
        if not depot_cache_path.exists():
            logger.info(f"Depot cache directory does not exist: {depot_cache_path}")
            return stats
        
        # Find all manifest files in depot cache
        manifest_files = list(depot_cache_path.glob("*.manifest"))
        logger.debug(f"Found {len(manifest_files)} manifest files to remove")
        
        if not manifest_files:
            logger.info("No manifest files found in depot cache")
            return stats
        
        # Remove all manifest files
        for manifest_file in manifest_files:
            try:
                logger.debug(f"Removing manifest file: {manifest_file.name}")
                manifest_file.unlink()
                stats['removed_count'] += 1
                logger.info(f"Removed manifest: {manifest_file.name}")
            except Exception as e:
                logger.error(f"Failed to remove manifest {manifest_file.name}: {e}")
                logger.debug(f"Manifest removal exception for {manifest_file.name}:", exc_info=True)
        
        logger.info(f"Depot cache cleanup complete: {stats['removed_count']} files removed")
        
    except Exception as e:
        logger.error(f"Failed to clear depot cache: {e}")
        logger.debug("Clear depot cache exception:", exc_info=True)
    
    return stats


