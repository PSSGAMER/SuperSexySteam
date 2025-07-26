# depot_cache_manager.py
#
# A module for managing Steam depot cache files (.manifest files).
# Handles copying manifest files from data folders to Steam's depot cache
# and removing them during uninstallation.

from pathlib import Path
import shutil
from typing import Dict, List, Optional


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
    stats = {'copied_count': 0, 'skipped_count': 0}
    
    try:
        # Convert to Path objects
        steam_path_obj = Path(steam_path)
        data_folder_obj = Path(data_folder)
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        if not depot_cache_path.exists():
            try:
                depot_cache_path.mkdir(parents=True, exist_ok=True)
                print(f"[INFO] Created depot cache directory: {depot_cache_path}")
            except Exception as e:
                print(f"[ERROR] Failed to create depot cache directory: {e}")
                return stats
        
        # Find all manifest files in the data folder
        manifest_files = list(data_folder_obj.glob("*.manifest"))
        
        if not manifest_files:
            print(f"[INFO] No manifest files found for AppID {app_id} in {data_folder_obj}")
            return stats
        
        # Copy each manifest file
        for manifest_file in manifest_files:
            try:
                destination = depot_cache_path / manifest_file.name
                
                # Check if file already exists and is identical
                if destination.exists():
                    if manifest_file.stat().st_size == destination.stat().st_size:
                        # Files are same size, assume they're identical
                        stats['skipped_count'] += 1
                        continue
                
                # Copy the file
                shutil.copy2(manifest_file, destination)
                stats['copied_count'] += 1
                print(f"[INFO] Copied manifest: {manifest_file.name}")
                
            except Exception as e:
                print(f"[ERROR] Failed to copy manifest {manifest_file.name}: {e}")
        
        print(f"[INFO] Depot cache update complete for AppID {app_id}: {stats['copied_count']} copied, {stats['skipped_count']} skipped")
        
    except Exception as e:
        print(f"[ERROR] Failed to update depot cache for AppID {app_id}: {e}")
    
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
    stats = {'removed_count': 0}
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        if not depot_cache_path.exists():
            print(f"[INFO] Depot cache directory does not exist: {depot_cache_path}")
            return stats
        
        if not manifest_filenames:
            print(f"[INFO] No manifest files specified for removal.")
            return stats
            
        # Remove each specified manifest file
        for filename in manifest_filenames:
            manifest_file_path = depot_cache_path / filename
            if manifest_file_path.exists():
                try:
                    manifest_file_path.unlink()
                    stats['removed_count'] += 1
                    print(f"[INFO] Removed manifest: {filename}")
                except Exception as e:
                    print(f"[ERROR] Failed to remove manifest {filename}: {e}")
            else:
                print(f"[WARNING] Manifest file not found in depotcache, skipping: {filename}")
        
        print(f"[INFO] Depot cache cleanup complete: {stats['removed_count']} specified manifest(s) removed.")
        
    except Exception as e:
        print(f"[ERROR] Failed to cleanup depot cache: {e}")
    
    return stats


def get_depot_cache_info(steam_path: str) -> Dict[str, any]:
    """
    Get information about the depot cache directory.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Information about depot cache
    """
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
        
        if info['exists']:
            manifest_files = list(depot_cache_path.glob("*.manifest"))
            info['manifest_count'] = len(manifest_files)
            
            total_size = 0
            for manifest_file in manifest_files:
                try:
                    total_size += manifest_file.stat().st_size
                except Exception:
                    pass  # Skip files we can't read
            
            info['total_size_mb'] = total_size / (1024 * 1024)
    
    except Exception as e:
        print(f"[ERROR] Failed to get depot cache info: {e}")
    
    return info


def clear_all_depot_cache(steam_path: str) -> Dict[str, int]:
    """
    Clear all manifest files from Steam depot cache.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, int]: Statistics with 'removed_count'
    """
    stats = {'removed_count': 0}
    
    try:
        # Convert to Path object
        steam_path_obj = Path(steam_path)
        
        # Construct depot cache path
        depot_cache_path = steam_path_obj / 'depotcache'
        if not depot_cache_path.exists():
            print(f"[INFO] Depot cache directory does not exist: {depot_cache_path}")
            return stats
        
        # Find all manifest files in depot cache
        manifest_files = list(depot_cache_path.glob("*.manifest"))
        
        if not manifest_files:
            print(f"[INFO] No manifest files found in depot cache")
            return stats
        
        # Remove all manifest files
        for manifest_file in manifest_files:
            try:
                manifest_file.unlink()
                stats['removed_count'] += 1
                print(f"[INFO] Removed manifest: {manifest_file.name}")
            except Exception as e:
                print(f"[ERROR] Failed to remove manifest {manifest_file.name}: {e}")
        
        print(f"[INFO] Depot cache cleanup complete: {stats['removed_count']} files removed")
        
    except Exception as e:
        print(f"[ERROR] Failed to clear depot cache: {e}")
    
    return stats


if __name__ == "__main__":
    # Test the depot cache manager
    print("Depot cache manager module loaded successfully!")
    
    # Example test (commented out to avoid accidental execution)
    # steam_path = "C:\\Program Files (x86)\\Steam"
    # info = get_depot_cache_info(steam_path)
    # print(f"Depot cache info: {info}")