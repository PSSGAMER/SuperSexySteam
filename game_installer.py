# game_installer.py
#
# A module for installing and uninstalling games in SuperSexySteam.
# Handles the complete workflow for adding new games and removing existing ones.

import os
import shutil
from typing import Dict, List, Optional
from database_manager import get_database_manager
from lua_parser import parse_lua_for_all_depots
from greenluma_manager import process_single_appid_for_greenluma, remove_appid_from_greenluma
from vdf_updater import add_depots_to_config_vdf, remove_depots_from_config_vdf
from depot_cache_manager import copy_manifests_for_appid, remove_manifests_for_appid
from acfgen import generate_acf_for_appid, remove_acf_for_appid


class GameInstaller:
    """
    Handles the installation and uninstallation of games in SuperSexySteam.
    Coordinates between all the different modules to ensure complete operations.
    """
    
    def __init__(self, config):
        """
        Initialize the game installer with configuration.
        
        Args:
            config: ConfigParser instance with application configuration
        """
        self.config = config
        self.db = get_database_manager()
        
    def install_game(self, app_id: str, data_folder: str) -> Dict[str, any]:
        """
        Install a game by processing its lua file and performing all necessary operations.
        
        Args:
            app_id (str): The Steam AppID to install
            data_folder (str): Path to the folder containing the game's lua and manifest files
            
        Returns:
            Dict[str, any]: Result dictionary with success status, errors, and statistics
        """
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'stats': {
                'depots_processed': 0,
                'manifests_copied': 0,
                'greenluma_updated': False,
                'config_vdf_updated': False,
                'acf_generated': False
            }
        }
        
        try:
            print(f"[INFO] Starting installation for AppID {app_id}")
            
            # Step 1: Parse the lua file to extract depot information
            lua_file = os.path.join(data_folder, f"{app_id}.lua")
            if not os.path.exists(lua_file):
                result['errors'].append(f"Lua file not found: {lua_file}")
                return result
            
            depots = parse_lua_for_all_depots(lua_file)
            if not depots:
                result['errors'].append(f"No depots found in lua file: {lua_file}")
                return result
            
            result['stats']['depots_processed'] = len(depots)
            print(f"[INFO] Found {len(depots)} depots in lua file")
            
            # Step 2: Add to database
            if not self.db.add_appid_with_depots(app_id, depots):
                result['errors'].append("Failed to add AppID and depots to database")
                return result
            
            print(f"[INFO] Added AppID {app_id} with {len(depots)} depots to database")
            
            # Step 3: Update GreenLuma
            greenluma_path = self.config.get('Paths', 'greenluma_path', fallback='')
            if greenluma_path and os.path.isdir(greenluma_path):
                try:
                    greenluma_result = process_single_appid_for_greenluma(greenluma_path, app_id, depots)
                    if greenluma_result['success']:
                        result['stats']['greenluma_updated'] = True
                        print(f"[INFO] GreenLuma updated for AppID {app_id}")
                    else:
                        result['warnings'].extend(greenluma_result.get('errors', []))
                except Exception as e:
                    result['warnings'].append(f"GreenLuma update failed: {e}")
            else:
                result['warnings'].append("Invalid GreenLuma path, skipping GreenLuma update")
            
            # Step 4: Update config.vdf
            steam_path = self.config.get('Paths', 'steam_path', fallback='')
            if steam_path and os.path.isdir(steam_path):
                try:
                    config_vdf_path = os.path.join(steam_path, 'config', 'config.vdf')
                    # Only add depots that have decryption keys
                    depots_with_keys = [d for d in depots if 'depot_key' in d]
                    if depots_with_keys:
                        vdf_success = add_depots_to_config_vdf(config_vdf_path, depots_with_keys)
                        if vdf_success:
                            result['stats']['config_vdf_updated'] = True
                            print(f"[INFO] Config.vdf updated with {len(depots_with_keys)} depot keys")
                        else:
                            result['warnings'].append("Failed to update config.vdf")
                    else:
                        print(f"[INFO] No depot keys to add to config.vdf for AppID {app_id}")
                except Exception as e:
                    result['warnings'].append(f"Config.vdf update failed: {e}")
            else:
                result['warnings'].append("Invalid Steam path, skipping config.vdf update")
            
            # Step 5: Copy manifest files to depot cache
            if steam_path and os.path.isdir(steam_path):
                try:
                    manifest_stats = copy_manifests_for_appid(steam_path, app_id, data_folder)
                    result['stats']['manifests_copied'] = manifest_stats.get('copied_count', 0)
                    if manifest_stats.get('copied_count', 0) > 0:
                        print(f"[INFO] Copied {manifest_stats['copied_count']} manifest files to depot cache")
                    else:
                        print(f"[INFO] No manifest files found to copy for AppID {app_id}")
                except Exception as e:
                    result['warnings'].append(f"Depot cache update failed: {e}")
            
            # Step 6: Generate ACF file
            if steam_path and os.path.isdir(steam_path):
                try:
                    acf_success = generate_acf_for_appid(steam_path, app_id)
                    if acf_success:
                        result['stats']['acf_generated'] = True
                        print(f"[INFO] ACF file generated for AppID {app_id}")
                    else:
                        result['warnings'].append("Failed to generate ACF file")
                except Exception as e:
                    result['warnings'].append(f"ACF generation failed: {e}")
            
            result['success'] = True
            print(f"[SUCCESS] Installation completed for AppID {app_id}")
            
        except Exception as e:
            result['errors'].append(f"Unexpected error during installation: {e}")
            print(f"[ERROR] Installation failed for AppID {app_id}: {e}")
        
        return result
    
    def uninstall_game(self, app_id: str) -> Dict[str, any]:
        """
        Uninstall a game by removing all its traces from the system.
        
        Args:
            app_id (str): The Steam AppID to uninstall
            
        Returns:
            Dict[str, any]: Result dictionary with success status, errors, and statistics
        """
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'stats': {
                'depots_removed': 0,
                'manifests_removed': 0,
                'greenluma_updated': False,
                'config_vdf_updated': False,
                'acf_removed': False
            }
        }
        
        try:
            print(f"[INFO] Starting uninstallation for AppID {app_id}")
            
            # Check if AppID exists in database
            if not self.db.is_appid_exists(app_id):
                result['errors'].append(f"AppID {app_id} not found in database")
                return result
            
            # Get depot information before removal
            depots = self.db.get_appid_depots(app_id)
            result['stats']['depots_removed'] = len(depots)
            
            # Step 1: Remove from GreenLuma
            greenluma_path = self.config.get('Paths', 'greenluma_path', fallback='')
            if greenluma_path and os.path.isdir(greenluma_path):
                try:
                    greenluma_result = remove_appid_from_greenluma(greenluma_path, app_id, depots)
                    if greenluma_result['success']:
                        result['stats']['greenluma_updated'] = True
                        print(f"[INFO] Removed AppID {app_id} from GreenLuma")
                    else:
                        result['warnings'].extend(greenluma_result.get('errors', []))
                except Exception as e:
                    result['warnings'].append(f"GreenLuma removal failed: {e}")
            
            # Step 2: Remove from config.vdf
            steam_path = self.config.get('Paths', 'steam_path', fallback='')
            if steam_path and os.path.isdir(steam_path):
                try:
                    config_vdf_path = os.path.join(steam_path, 'config', 'config.vdf')
                    depots_with_keys = [d for d in depots if 'depot_key' in d]
                    if depots_with_keys:
                        vdf_success = remove_depots_from_config_vdf(config_vdf_path, depots_with_keys)
                        if vdf_success:
                            result['stats']['config_vdf_updated'] = True
                            print(f"[INFO] Removed {len(depots_with_keys)} depot keys from config.vdf")
                        else:
                            result['warnings'].append("Failed to update config.vdf")
                except Exception as e:
                    result['warnings'].append(f"Config.vdf update failed: {e}")
            
            # Step 3: Remove manifest files from depot cache
            if steam_path and os.path.isdir(steam_path):
                try:
                    manifest_stats = remove_manifests_for_appid(steam_path, app_id)
                    result['stats']['manifests_removed'] = manifest_stats.get('removed_count', 0)
                    if manifest_stats.get('removed_count', 0) > 0:
                        print(f"[INFO] Removed {manifest_stats['removed_count']} manifest files from depot cache")
                except Exception as e:
                    result['warnings'].append(f"Depot cache cleanup failed: {e}")
            
            # Step 4: Remove ACF file
            if steam_path and os.path.isdir(steam_path):
                try:
                    acf_success = remove_acf_for_appid(steam_path, app_id)
                    if acf_success:
                        result['stats']['acf_removed'] = True
                        print(f"[INFO] Removed ACF file for AppID {app_id}")
                    else:
                        result['warnings'].append("Failed to remove ACF file")
                except Exception as e:
                    result['warnings'].append(f"ACF removal failed: {e}")
            
            # Step 5: Remove from database (do this last)
            if not self.db.remove_appid(app_id):
                result['errors'].append("Failed to remove AppID from database")
                return result
            
            print(f"[INFO] Removed AppID {app_id} from database")
            
            result['success'] = True
            print(f"[SUCCESS] Uninstallation completed for AppID {app_id}")
            
        except Exception as e:
            result['errors'].append(f"Unexpected error during uninstallation: {e}")
            print(f"[ERROR] Uninstallation failed for AppID {app_id}: {e}")
        
        return result


# =============================================================================
# --- CONVENIENCE FUNCTIONS ---
# =============================================================================

def install_game_from_data_folder(config, app_id: str, data_folder: str) -> Dict[str, any]:
    """
    Convenience function to install a game from a data folder.
    
    Args:
        config: Application configuration
        app_id (str): Steam AppID
        data_folder (str): Path to folder containing lua and manifest files
        
    Returns:
        Dict[str, any]: Installation result
    """
    installer = GameInstaller(config)
    return installer.install_game(app_id, data_folder)


def uninstall_game_by_appid(config, app_id: str) -> Dict[str, any]:
    """
    Convenience function to uninstall a game by AppID.
    
    Args:
        config: Application configuration  
        app_id (str): Steam AppID
        
    Returns:
        Dict[str, any]: Uninstallation result
    """
    installer = GameInstaller(config)
    return installer.uninstall_game(app_id)


if __name__ == "__main__":
    # Test the installer
    print("Game installer module loaded successfully!")
