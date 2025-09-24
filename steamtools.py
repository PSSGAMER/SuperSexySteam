# steamtools.py
#
# A module for Steam-specific file operations and utilities.
# Handles copying manifest and lua files to Steam directories for game installation.

import logging
from pathlib import Path
import shutil
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


def copy_manifests_to_depotcache(steam_path: str, app_id: str, data_folder: str) -> Dict[str, any]:
    """
    Copy manifest files from data folder to Steam's depotcache directory.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID being installed
        data_folder (str): Path to folder containing manifest files
        
    Returns:
        Dict[str, any]: Result dictionary with success status and statistics
    """
    logger.info(f"Copying manifest files to depotcache for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    logger.debug(f"Data folder: {data_folder}")
    
    result = {
        'success': False,
        'copied_count': 0,
        'errors': [],
        'warnings': [],
        'copied_files': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        data_folder_obj = Path(data_folder)
        
        # Validate paths
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
            
        if not data_folder_obj.exists():
            error_msg = f"Data folder does not exist: {data_folder}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        # Ensure depotcache directory exists
        depotcache_path = steam_path_obj / 'config' / 'depotcache'
        depotcache_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Depotcache directory: {depotcache_path}")
        
        # Find all manifest files in data folder
        manifest_files = list(data_folder_obj.glob("*.manifest"))
        logger.info(f"Found {len(manifest_files)} manifest files to copy")
        
        if not manifest_files:
            logger.info("No manifest files found to copy")
            result['success'] = True
            return result
        
        # Copy each manifest file
        for manifest_file in manifest_files:
            try:
                dest_file = depotcache_path / manifest_file.name
                logger.debug(f"Copying {manifest_file.name} to {dest_file}")
                
                # Copy the file
                shutil.copy2(manifest_file, dest_file)
                result['copied_count'] += 1
                result['copied_files'].append(manifest_file.name)
                logger.debug(f"Successfully copied: {manifest_file.name}")
                
            except Exception as e:
                warning_msg = f"Failed to copy manifest file {manifest_file.name}: {e}"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
        
        if result['copied_count'] > 0:
            result['success'] = True
            logger.info(f"Successfully copied {result['copied_count']} manifest files to depotcache")
        else:
            logger.warning("No manifest files were successfully copied")
            
    except Exception as e:
        error_msg = f"Unexpected error copying manifest files: {e}"
        logger.error(error_msg)
        logger.debug("Manifest copy exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def copy_lua_to_stplug_in(steam_path: str, app_id: str, data_folder: str) -> Dict[str, any]:
    """
    Copy lua file from data folder to Steam's stplug-in directory.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID being installed
        data_folder (str): Path to folder containing lua file
        
    Returns:
        Dict[str, any]: Result dictionary with success status and details
    """
    logger.info(f"Copying lua file to stplug-in for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    logger.debug(f"Data folder: {data_folder}")
    
    result = {
        'success': False,
        'copied_file': None,
        'errors': [],
        'warnings': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        data_folder_obj = Path(data_folder)
        
        # Validate paths
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
            
        if not data_folder_obj.exists():
            error_msg = f"Data folder does not exist: {data_folder}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        # Ensure stplug-in directory exists
        stplug_in_path = steam_path_obj / 'config' / 'stplug-in'
        stplug_in_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"stplug-in directory: {stplug_in_path}")
        
        # Find lua file for this AppID
        lua_file = data_folder_obj / f"{app_id}.lua"
        if not lua_file.exists():
            # Try to find any lua file in the folder
            lua_files = list(data_folder_obj.glob("*.lua"))
            if lua_files:
                lua_file = lua_files[0]
                logger.debug(f"Using first lua file found: {lua_file.name}")
            else:
                error_msg = f"No lua file found in data folder: {data_folder}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
        
        # Copy the lua file
        dest_file = stplug_in_path / lua_file.name
        logger.debug(f"Copying {lua_file.name} to {dest_file}")
        
        try:
            shutil.copy2(lua_file, dest_file)
            result['copied_file'] = lua_file.name
            result['success'] = True
            logger.info(f"Successfully copied lua file: {lua_file.name}")
            
        except Exception as e:
            error_msg = f"Failed to copy lua file {lua_file.name}: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            
    except Exception as e:
        error_msg = f"Unexpected error copying lua file: {e}"
        logger.error(error_msg)
        logger.debug("Lua copy exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def remove_manifests_from_depotcache(steam_path: str, app_id: str) -> Dict[str, any]:
    """
    Remove manifest files from Steam's depotcache directory for a specific AppID.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID to remove manifests for
        
    Returns:
        Dict[str, any]: Result dictionary with success status and statistics
    """
    logger.info(f"Removing manifest files from depotcache for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    
    result = {
        'success': False,
        'removed_count': 0,
        'errors': [],
        'warnings': [],
        'removed_files': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Validate steam path
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        depotcache_path = steam_path_obj / 'config' / 'depotcache'
        
        if not depotcache_path.exists():
            logger.info("Depotcache directory does not exist, nothing to remove")
            result['success'] = True
            return result
        
        # Get depot IDs for this AppID from database to find related manifest files
        from database_manager import get_database_manager
        db = get_database_manager()
        manifest_filenames = db.get_manifests_for_appid(app_id)
        
        if not manifest_filenames:
            logger.info(f"No manifest filenames found for AppID {app_id}, nothing to remove")
            result['success'] = True
            return result
        
        # Remove each manifest file by filename
        for filename in manifest_filenames:
            manifest_file = depotcache_path / filename
            if manifest_file.exists():
                try:
                    manifest_file.unlink()
                    result['removed_count'] += 1
                    result['removed_files'].append(filename)
                    logger.debug(f"Removed manifest file: {filename}")
                    
                except Exception as e:
                    warning_msg = f"Failed to remove manifest file {filename}: {e}"
                    logger.warning(warning_msg)
                    result['warnings'].append(warning_msg)
            else:
                logger.debug(f"Manifest file not found in depotcache: {filename}")
        
        result['success'] = True
        if result['removed_count'] > 0:
            logger.info(f"Successfully removed {result['removed_count']} manifest files from depotcache")
        else:
            logger.info("No manifest files found to remove from depotcache")
            
    except Exception as e:
        error_msg = f"Unexpected error removing manifest files: {e}"
        logger.error(error_msg)
        logger.debug("Manifest removal exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def remove_lua_from_stplug_in(steam_path: str, app_id: str) -> Dict[str, any]:
    """
    Remove lua file from Steam's stplug-in directory for a specific AppID.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID to remove lua file for
        
    Returns:
        Dict[str, any]: Result dictionary with success status and details
    """
    logger.info(f"Removing lua file from stplug-in for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    
    result = {
        'success': False,
        'removed_file': None,
        'errors': [],
        'warnings': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Validate steam path
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        stplug_in_path = steam_path_obj / 'config' / 'stplug-in'
        
        if not stplug_in_path.exists():
            logger.info("stplug-in directory does not exist, nothing to remove")
            result['success'] = True
            return result
        
        # Find and remove the lua file
        lua_file = stplug_in_path / f"{app_id}.lua"
        
        if lua_file.exists():
            try:
                lua_file.unlink()
                result['removed_file'] = lua_file.name
                result['success'] = True
                logger.info(f"Successfully removed lua file: {lua_file.name}")
                
            except Exception as e:
                error_msg = f"Failed to remove lua file {lua_file.name}: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
        else:
            logger.info(f"Lua file not found in stplug-in: {lua_file.name}")
            result['success'] = True
            
    except Exception as e:
        error_msg = f"Unexpected error removing lua file: {e}"
        logger.error(error_msg)
        logger.debug("Lua removal exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def clear_all_manifests_from_depotcache(steam_path: str) -> Dict[str, any]:
    """
    Clear all manifest files from Steam's depotcache directory.
    This removes all .manifest files, not just those tracked by SuperSexySteam.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Result dictionary with success status and statistics
    """
    logger.info("Clearing all manifest files from depotcache")
    logger.debug(f"Steam path: {steam_path}")
    
    result = {
        'success': False,
        'removed_count': 0,
        'errors': [],
        'warnings': [],
        'removed_files': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Validate steam path
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        depotcache_path = steam_path_obj / 'config' / 'depotcache'
        
        if not depotcache_path.exists():
            logger.info("Depotcache directory does not exist, nothing to clear")
            result['success'] = True
            return result
        
        # Find all manifest files
        manifest_files = list(depotcache_path.glob("*.manifest"))
        logger.info(f"Found {len(manifest_files)} manifest files to remove")
        
        # Remove each manifest file
        for manifest_file in manifest_files:
            try:
                manifest_file.unlink()
                result['removed_count'] += 1
                result['removed_files'].append(manifest_file.name)
                logger.debug(f"Removed manifest file: {manifest_file.name}")
                
            except Exception as e:
                warning_msg = f"Failed to remove manifest file {manifest_file.name}: {e}"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
        
        result['success'] = True
        if result['removed_count'] > 0:
            logger.info(f"Successfully removed {result['removed_count']} manifest files from depotcache")
        else:
            logger.info("No manifest files found to remove from depotcache")
            
    except Exception as e:
        error_msg = f"Unexpected error clearing manifest files: {e}"
        logger.error(error_msg)
        logger.debug("Manifest clearing exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def clear_all_lua_from_stplug_in(steam_path: str) -> Dict[str, any]:
    """
    Clear all lua files from Steam's stplug-in directory.
    This removes all .lua files, not just those tracked by SuperSexySteam.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Result dictionary with success status and statistics
    """
    logger.info("Clearing all lua files from stplug-in")
    logger.debug(f"Steam path: {steam_path}")
    
    result = {
        'success': False,
        'removed_count': 0,
        'errors': [],
        'warnings': [],
        'removed_files': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        
        # Validate steam path
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        stplug_in_path = steam_path_obj / 'config' / 'stplug-in'
        
        if not stplug_in_path.exists():
            logger.info("stplug-in directory does not exist, nothing to clear")
            result['success'] = True
            return result
        
        # Find all lua files
        lua_files = list(stplug_in_path.glob("*.lua"))
        logger.info(f"Found {len(lua_files)} lua files to remove")
        
        # Remove each lua file
        for lua_file in lua_files:
            try:
                lua_file.unlink()
                result['removed_count'] += 1
                result['removed_files'].append(lua_file.name)
                logger.debug(f"Removed lua file: {lua_file.name}")
                
            except Exception as e:
                warning_msg = f"Failed to remove lua file {lua_file.name}: {e}"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
        
        result['success'] = True
        if result['removed_count'] > 0:
            logger.info(f"Successfully removed {result['removed_count']} lua files from stplug-in")
        else:
            logger.info("No lua files found to remove from stplug-in")
            
    except Exception as e:
        error_msg = f"Unexpected error clearing lua files: {e}"
        logger.error(error_msg)
        logger.debug("Lua clearing exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def validate_steam_directories(steam_path: str) -> Dict[str, any]:
    """
    Validate that required Steam directories exist and create them if necessary.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Validation result with directory status
    """
    logger.info("Validating Steam directories")
    logger.debug(f"Steam path: {steam_path}")
    
    result = {
        'success': False,
        'directories': {},
        'created': [],
        'errors': []
    }
    
    try:
        steam_path_obj = Path(steam_path)
        
        if not steam_path_obj.exists():
            error_msg = f"Steam path does not exist: {steam_path}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
        
        # Check and create required directories
        required_dirs = {
            'config': steam_path_obj / 'config',
            'depotcache': steam_path_obj / 'config' / 'depotcache',
            'stplug-in': steam_path_obj / 'config' / 'stplug-in'
        }
        
        for dir_name, dir_path in required_dirs.items():
            if dir_path.exists():
                result['directories'][dir_name] = 'exists'
                logger.debug(f"Directory exists: {dir_path}")
            else:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    result['directories'][dir_name] = 'created'
                    result['created'].append(str(dir_path))
                    logger.info(f"Created directory: {dir_path}")
                except Exception as e:
                    result['directories'][dir_name] = 'failed'
                    error_msg = f"Failed to create directory {dir_path}: {e}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
        
        # Success if no errors occurred
        result['success'] = len(result['errors']) == 0
        
        if result['success']:
            logger.info("Steam directories validated successfully")
            if result['created']:
                logger.info(f"Created {len(result['created'])} directories")
        else:
            logger.error(f"Steam directory validation failed with {len(result['errors'])} errors")
            
    except Exception as e:
        error_msg = f"Unexpected error validating Steam directories: {e}"
        logger.error(error_msg)
        logger.debug("Directory validation exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result