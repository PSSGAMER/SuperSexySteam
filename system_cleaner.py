# system_cleaner.py
#
# A module for comprehensive system cleaning and uninstallation operations.
# Provides functions to completely clear all data or uninstall specific AppIDs.

import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
from database_manager import get_database_manager
from vdf_updater import remove_depots_from_config_vdf, get_existing_depot_keys
from depot_cache_manager import remove_manifests_for_appid, clear_all_depot_cache
from acfgen import remove_acf_for_appid, remove_all_tracked_acf_files
from greenluma_manager import remove_appid_from_greenluma, clear_greenluma_applist

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def clear_all_data(config) -> Dict[str, any]:
    """
    Completely clear all SuperSexySteam data from the system.
    This includes:
    - Database deletion
    - Data folder deletion
    - All depot keys from config.vdf
    - All files from depotcache
    - All .acf files for tracked AppIDs
    - All files from GreenLuma AppList folder
    
    Args:
        config: Application configuration
        
    Returns:
        Dict[str, any]: Result with success status, statistics, and any errors
    """
    logger.info("Starting comprehensive data cleanup")
    
    result = {
        'success': False,
        'errors': [],
        'warnings': [],
        'stats': {
            'database_cleared': False,
            'data_folder_cleared': False,
            'depot_keys_removed': 0,
            'depotcache_files_removed': 0,
            'acf_files_removed': 0,
            'greenluma_files_removed': 0
        }
    }
    
    try:
        # Step 1: Get all data before clearing database
        db = get_database_manager()
        installed_appids = db.get_all_installed_appids()
        all_depots = db.get_all_depots_for_installed_apps()
        
        logger.info(f"Found {len(installed_appids)} installed AppIDs and {len(all_depots)} depots")
        
        # Step 2: Clear Steam config.vdf depot keys
        steam_path_str = config.get('Paths', 'steam_path', fallback='')
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    config_vdf_path = steam_path / 'config' / 'config.vdf'
                    if config_vdf_path.exists():
                        # Get existing depot keys to see what we're removing
                        existing_keys = get_existing_depot_keys(str(config_vdf_path))
                        
                        # Remove all depot keys that belong to tracked AppIDs
                        depots_to_remove = [d for d in all_depots if 'decryption_key' in d]
                        if depots_to_remove:
                            if remove_depots_from_config_vdf(str(config_vdf_path), depots_to_remove):
                                result['stats']['depot_keys_removed'] = len(depots_to_remove)
                                logger.info(f"Removed {len(depots_to_remove)} depot keys from config.vdf")
                            else:
                                result['warnings'].append("Failed to remove depot keys from config.vdf")
                        else:
                            logger.info("No depot keys to remove from config.vdf")
                except Exception as e:
                    result['warnings'].append(f"Config.vdf cleanup failed: {e}")
                    logger.warning(f"Config.vdf cleanup failed: {e}")
            else:
                result['warnings'].append("Steam path not configured or invalid")
        else:
            result['warnings'].append("Steam path not configured or invalid")
        
        # Step 3: Clear all depot cache files
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    depot_stats = clear_all_depot_cache(str(steam_path))
                    result['stats']['depotcache_files_removed'] = depot_stats.get('removed_count', 0)
                    logger.info(f"Removed {depot_stats['removed_count']} manifest files from depot cache")
                except Exception as e:
                    result['warnings'].append(f"Depot cache cleanup failed: {e}")
                    logger.warning(f"Depot cache cleanup failed: {e}")
        
        # Step 4: Remove ACF files for tracked AppIDs
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    acf_stats = remove_all_tracked_acf_files(str(steam_path), installed_appids)
                    result['stats']['acf_files_removed'] = acf_stats.get('removed_count', 0)
                    logger.info(f"Removed {acf_stats['removed_count']} ACF files")
                except Exception as e:
                    result['warnings'].append(f"ACF cleanup failed: {e}")
                    logger.warning(f"ACF cleanup failed: {e}")
        
        # Step 5: Clear GreenLuma AppList
        greenluma_path_str = config.get('Paths', 'greenluma_path', fallback='')
        if greenluma_path_str:
            greenluma_path = Path(greenluma_path_str)
            if greenluma_path.is_dir():
                try:
                    removed_count = clear_greenluma_applist(str(greenluma_path))
                    if removed_count >= 0:
                        result['stats']['greenluma_files_removed'] = removed_count
                        logger.info(f"Removed {removed_count} files from GreenLuma AppList")
                    else:
                        result['warnings'].append("Failed to clear GreenLuma AppList")
                except Exception as e:
                    result['warnings'].append(f"GreenLuma cleanup failed: {e}")
                    logger.warning(f"GreenLuma cleanup failed: {e}")
            else:
                result['warnings'].append("GreenLuma path not configured or invalid")
        else:
            result['warnings'].append("GreenLuma path not configured or invalid")
        
        # Step 6: Clear data folder
        try:
            script_dir = Path(__file__).parent
            data_folder = script_dir / "data"
            
            if data_folder.exists():
                shutil.rmtree(data_folder)
                result['stats']['data_folder_cleared'] = True
                logger.info("Removed data folder and all its contents")
            else:
                logger.info("Data folder does not exist")
                result['stats']['data_folder_cleared'] = True
        except Exception as e:
            result['warnings'].append(f"Data folder cleanup failed: {e}")
            logger.warning(f"Data folder cleanup failed: {e}")
        
        # Step 7: Clear database (do this last)
        try:
            db_file = Path('supersexysteam.db')
            if db_file.exists():
                db_file.unlink()
                result['stats']['database_cleared'] = True
                logger.info("Removed database file")
            else:
                logger.info("Database file does not exist")
                result['stats']['database_cleared'] = True
        except Exception as e:
            result['errors'].append(f"Database cleanup failed: {e}")
            logger.error(f"Database cleanup failed: {e}")
            logger.debug("Database cleanup error details:", exc_info=True)
            return result
        
        result['success'] = True
        logger.info("Comprehensive data cleanup completed successfully")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error during cleanup: {e}")
        logger.error(f"Cleanup failed: {e}")
        logger.debug("Cleanup error details:", exc_info=True)
    
    return result


def uninstall_specific_appid(config, app_id: str) -> Dict[str, any]:
    """
    Uninstall a specific AppID from the system.
    This includes:
    - Removing depot keys from config.vdf for this AppID
    - Removing specific manifest files from depotcache
    - Removing the specific AppID folder from data directory
    - Removing the specific .acf file
    - Removing the specific database entry
    - Removing app .txt files from GreenLuma AppList folder
    
    Args:
        config: Application configuration
        app_id (str): The Steam AppID to uninstall
        
    Returns:
        Dict[str, any]: Result with success status, statistics, and any errors
    """
    logger.info(f"Starting uninstallation for AppID {app_id}")
    
    result = {
        'success': False,
        'errors': [],
        'warnings': [],
        'stats': {
            'depot_keys_removed': 0,
            'manifest_files_removed': 0,
            'data_folder_removed': False,
            'acf_file_removed': False,
            'database_entry_removed': False,
            'greenluma_files_removed': 0
        }
    }
    
    try:
        # Step 1: Check if AppID exists in database
        db = get_database_manager()
        if not db.is_appid_exists(app_id):
            error_msg = f"AppID {app_id} not found in database"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        # Get depot and manifest information before removal
        depots = db.get_appid_depots(app_id)
        manifest_filenames = db.get_manifests_for_appid(app_id)
        logger.info(f"Found {len(depots)} depots and {len(manifest_filenames)} manifests for AppID {app_id}")
        
        # Step 2: Remove depot keys from config.vdf
        steam_path_str = config.get('Paths', 'steam_path', fallback='')
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    config_vdf_path = steam_path / 'config' / 'config.vdf'
                    depots_with_keys = [d for d in depots if 'depot_key' in d]
                    if depots_with_keys:
                        if remove_depots_from_config_vdf(str(config_vdf_path), depots_with_keys):
                            result['stats']['depot_keys_removed'] = len(depots_with_keys)
                            logger.info(f"Removed {len(depots_with_keys)} depot keys from config.vdf")
                        else:
                            result['warnings'].append("Failed to update config.vdf")
                    else:
                        logger.info("No depot keys to remove from config.vdf")
                except Exception as e:
                    result['warnings'].append(f"Config.vdf cleanup failed: {e}")
                    logger.warning(f"Config.vdf cleanup failed: {e}")
        
        # Step 3: Remove manifest files from depot cache
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    manifest_stats = remove_manifests_for_appid(str(steam_path), manifest_filenames)
                    result['stats']['manifest_files_removed'] = manifest_stats.get('removed_count', 0)
                    if manifest_stats.get('removed_count', 0) > 0:
                        logger.info(f"Removed {manifest_stats['removed_count']} manifest files from depot cache")
                except Exception as e:
                    result['warnings'].append(f"Depot cache cleanup failed: {e}")
                    logger.warning(f"Depot cache cleanup failed: {e}")
        
        # Step 4: Remove specific AppID folder from data directory
        try:
            script_dir = Path(__file__).parent
            appid_data_folder = script_dir / "data" / app_id
            
            if appid_data_folder.exists():
                shutil.rmtree(appid_data_folder)
                result['stats']['data_folder_removed'] = True
                logger.info(f"Removed data folder for AppID {app_id}")
            else:
                logger.info(f"Data folder for AppID {app_id} does not exist")
                result['stats']['data_folder_removed'] = True
        except Exception as e:
            result['warnings'].append(f"Data folder cleanup failed: {e}")
            logger.warning(f"Data folder cleanup failed: {e}")
        
        # Step 5: Remove ACF file
        if steam_path_str:
            steam_path = Path(steam_path_str)
            if steam_path.is_dir():
                try:
                    if remove_acf_for_appid(str(steam_path), app_id):
                        result['stats']['acf_file_removed'] = True
                        logger.info(f"Removed ACF file for AppID {app_id}")
                    else:
                        result['warnings'].append("Failed to remove ACF file")
                except Exception as e:
                    result['warnings'].append(f"ACF removal failed: {e}")
                    logger.warning(f"ACF removal failed: {e}")
        
        # Step 6: Remove from GreenLuma
        greenluma_path_str = config.get('Paths', 'greenluma_path', fallback='')
        if greenluma_path_str:
            greenluma_path = Path(greenluma_path_str)
            if greenluma_path.is_dir():
                try:
                    greenluma_result = remove_appid_from_greenluma(str(greenluma_path), app_id, depots)
                    if greenluma_result['success']:
                        total_removed = greenluma_result['stats'].get('appids_removed', 0) + greenluma_result['stats'].get('depots_removed', 0)
                        result['stats']['greenluma_files_removed'] = total_removed
                        logger.info(f"Removed {total_removed} entries from GreenLuma AppList")
                    else:
                        result['warnings'].extend(greenluma_result.get('errors', []))
                except Exception as e:
                    result['warnings'].append(f"GreenLuma removal failed: {e}")
                    logger.warning(f"GreenLuma removal failed: {e}")
        
        # Step 7: Remove from database (do this last)
        try:
            if db.remove_appid(app_id):
                result['stats']['database_entry_removed'] = True
                logger.info(f"Removed AppID {app_id} from database")
            else:
                error_msg = "Failed to remove AppID from database"
                result['errors'].append(error_msg)
                logger.error(error_msg)
                return result
        except Exception as e:
            error_msg = f"Database removal failed: {e}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            logger.debug("Database removal error details:", exc_info=True)
            return result
        
        result['success'] = True
        logger.info(f"Uninstallation completed successfully for AppID {app_id}")
        
    except Exception as e:
        error_msg = f"Unexpected error during uninstallation: {e}"
        result['errors'].append(error_msg)
        logger.error(f"Uninstallation failed for AppID {app_id}: {e}")
        logger.debug("Uninstallation error details:", exc_info=True)
    
    return result


