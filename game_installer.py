# game_installer.py
#
# A module for installing and uninstalling games in SuperSexySteam.
# Handles the complete workflow for adding new games and removing existing ones.

from pathlib import Path
import shutil
from typing import Dict, List, Optional
from database_manager import get_database_manager
from lua_parser import parse_lua_for_all_depots
from greenluma_manager import process_single_appid_for_greenluma, remove_appid_from_greenluma
from vdf_updater import add_depots_to_config_vdf, remove_depots_from_config_vdf
from depot_cache_manager import copy_manifests_for_appid, remove_manifests_for_appid
from acfgen import generate_acf_for_appid, remove_acf_for_appid
from steam_game_search import get_game_name_by_appid


class GameInstaller:
    """
    Handles the installation and uninstallation of games in SuperSexySteam.
    Coordinates between all the different modules to ensure complete operations.
    """
    
    def __init__(self, config):
        """
        Initialize the game installer with configuration and perform initial path checks.
        
        Args:
            config: ConfigParser instance with application configuration
        """
        self.config = config
        self.db = get_database_manager()
        
        # --- Centralized Path Validation ---
        # Get paths from config once and validate them.
        steam_path_str = self.config.get('Paths', 'steam_path', fallback='')
        greenluma_path_str = self.config.get('Paths', 'greenluma_path', fallback='')
        
        self.steam_path = Path(steam_path_str) if steam_path_str else Path()
        self.greenluma_path = Path(greenluma_path_str) if greenluma_path_str else Path()
        
        self.is_steam_path_valid = self.steam_path.exists() and self.steam_path.is_dir()
        self.is_greenluma_path_valid = self.greenluma_path.exists() and self.greenluma_path.is_dir()
        
        if not self.is_steam_path_valid:
            print(f"[WARNING] Steam path is not configured or invalid: '{self.steam_path}'")
        if not self.is_greenluma_path_valid:
            print(f"[WARNING] GreenLuma path is not configured or invalid: '{self.greenluma_path}'")

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
            data_folder_path = Path(data_folder)
            lua_file = data_folder_path / f"{app_id}.lua"
            
            if not lua_file.exists():
                result['errors'].append(f"Lua file not found: {lua_file}")
                return result
            
            lua_result = parse_lua_for_all_depots(str(lua_file))
            if not lua_result or not lua_result.get('depots'):
                result['errors'].append(f"No depots found in lua file: {lua_file}")
                return result
            
            depots = lua_result['depots']
            result['stats']['depots_processed'] = len(depots)
            print(f"[INFO] Found {len(depots)} depots in lua file")
            
            # Step 2: Fetch game name from Steam API
            game_name = get_game_name_by_appid(app_id)
            print(f"[INFO] Retrieved game name: {game_name}")
            
            # Step 3: Add to database with game name
            if not self.db.add_appid_with_depots(app_id, depots, game_name):
                result['errors'].append("Failed to add AppID and depots to database")
                return result
            
            print(f"[INFO] Added AppID {app_id} ({game_name}) with {len(depots)} depots to database")
            
            # Step 4: Update GreenLuma
            if self.is_greenluma_path_valid:
                try:
                    greenluma_result = process_single_appid_for_greenluma(str(self.greenluma_path), app_id, depots)
                    if greenluma_result['success']:
                        result['stats']['greenluma_updated'] = True
                        print(f"[INFO] GreenLuma updated for AppID {app_id}")
                    else:
                        result['warnings'].extend(greenluma_result.get('errors', []))
                except Exception as e:
                    result['warnings'].append(f"GreenLuma update failed: {e}")
            else:
                result['warnings'].append("Invalid GreenLuma path, skipping GreenLuma update")
            
            # Step 5: Update config.vdf
            if self.is_steam_path_valid:
                try:
                    config_vdf_path = self.steam_path / 'config' / 'config.vdf'
                    # Only add depots that have decryption keys
                    depots_with_keys = [d for d in depots if 'depot_key' in d]
                    if depots_with_keys:
                        vdf_success = add_depots_to_config_vdf(str(config_vdf_path), depots_with_keys)
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
            
            # Step 6: Copy manifest files to depot cache
            if self.is_steam_path_valid:
                try:
                    manifest_stats = copy_manifests_for_appid(str(self.steam_path), app_id, data_folder)
                    result['stats']['manifests_copied'] = manifest_stats.get('copied_count', 0)
                    if manifest_stats.get('copied_count', 0) > 0:
                        print(f"[INFO] Copied {manifest_stats['copied_count']} manifest files to depot cache")
                    else:
                        print(f"[INFO] No manifest files found to copy for AppID {app_id}")
                except Exception as e:
                    result['warnings'].append(f"Depot cache update failed: {e}")
            
            # Step 7: Generate ACF file
            if self.is_steam_path_valid:
                try:
                    acf_success = generate_acf_for_appid(str(self.steam_path), app_id)
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
            if self.is_greenluma_path_valid:
                try:
                    greenluma_result = remove_appid_from_greenluma(str(self.greenluma_path), app_id, depots)
                    if greenluma_result['success']:
                        result['stats']['greenluma_updated'] = True
                        print(f"[INFO] Removed AppID {app_id} from GreenLuma")
                    else:
                        result['warnings'].extend(greenluma_result.get('errors', []))
                except Exception as e:
                    result['warnings'].append(f"GreenLuma removal failed: {e}")
            
            # Step 2: Remove from config.vdf
            if self.is_steam_path_valid:
                try:
                    config_vdf_path = self.steam_path / 'config' / 'config.vdf'
                    depots_with_keys = [d for d in depots if 'depot_key' in d]
                    if depots_with_keys:
                        vdf_success = remove_depots_from_config_vdf(str(config_vdf_path), depots_with_keys)
                        if vdf_success:
                            result['stats']['config_vdf_updated'] = True
                            print(f"[INFO] Removed {len(depots_with_keys)} depot keys from config.vdf")
                        else:
                            result['warnings'].append("Failed to update config.vdf")
                except Exception as e:
                    result['warnings'].append(f"Config.vdf update failed: {e}")
            
            # Step 3: Remove manifest files from depot cache
            if self.is_steam_path_valid:
                try:
                    manifest_stats = remove_manifests_for_appid(str(self.steam_path), app_id)
                    result['stats']['manifests_removed'] = manifest_stats.get('removed_count', 0)
                    if manifest_stats.get('removed_count', 0) > 0:
                        print(f"[INFO] Removed {manifest_stats['removed_count']} manifest files from depot cache")
                except Exception as e:
                    result['warnings'].append(f"Depot cache cleanup failed: {e}")
            
            # Step 4: Remove ACF file
            if self.is_steam_path_valid:
                try:
                    acf_success = remove_acf_for_appid(str(self.steam_path), app_id)
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
    
    def validate_installation(self, app_id: str) -> Dict[str, any]:
        """
        Validate that a game is properly installed across all systems.
        
        Args:
            app_id (str): The Steam AppID to validate
            
        Returns:
            Dict[str, any]: Validation result with detailed status
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'components': {
                'database': False,
                'greenluma': False,
                'config_vdf': False,
                'manifests': False,
                'acf': False
            }
        }
        
        try:
            # Check database
            if self.db.is_appid_exists(app_id):
                result['components']['database'] = True
            else:
                result['errors'].append("AppID not found in database")
                result['valid'] = False
            
            # Check GreenLuma
            if self.is_greenluma_path_valid:
                applist_dir = self.greenluma_path / 'NormalMode' / 'AppList'
                applist_file = applist_dir / f"{app_id}.txt"
                if applist_file.exists():
                    result['components']['greenluma'] = True
                else:
                    result['warnings'].append("AppID not found in GreenLuma AppList")
            
            # Check Steam config.vdf
            if self.is_steam_path_valid:
                from vdf_updater import get_existing_depot_keys
                config_vdf_path = self.steam_path / 'config' / 'config.vdf'
                if config_vdf_path.exists():
                    existing_keys = get_existing_depot_keys(str(config_vdf_path), verbose=False)
                    if existing_keys:
                        result['components']['config_vdf'] = True
                    else:
                        result['warnings'].append("No depot keys found in config.vdf")
            
            # Check manifests
            if self.is_steam_path_valid:
                depotcache_path = self.steam_path / 'steamapps' / 'depotcache'
                if depotcache_path.is_dir():
                    manifest_count = len([f for f in depotcache_path.iterdir() 
                                        if f.suffix == '.manifest'])
                    if manifest_count > 0:
                        result['components']['manifests'] = True
                    else:
                        result['warnings'].append("No manifest files found in depotcache")
            
            # Check ACF file
            if self.is_steam_path_valid:
                steamapps_path = self.steam_path / 'steamapps'
                acf_file = steamapps_path / f"appmanifest_{app_id}.acf"
                if acf_file.exists():
                    result['components']['acf'] = True
                else:
                    result['warnings'].append("ACF file not found")
            
        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
            result['valid'] = False
        
        return result
    
    def get_installation_status(self, app_id: str = None) -> Dict[str, any]:
        """
        Get detailed installation status for one or all games.
        
        Args:
            app_id (str, optional): Specific AppID to check, or None for all
            
        Returns:
            Dict[str, any]: Installation status information
        """
        status = {
            'total_games': 0,
            'installed_games': 0,
            'games': [],
            'summary': {
                'database_entries': 0,
                'greenluma_entries': 0,
                'config_vdf_depots': 0,
                'manifest_files': 0,
                'acf_files': 0
            }
        }
        
        try:
            if app_id:
                # Single game status
                if self.db.is_appid_exists(app_id):
                    game_info = {
                        'app_id': app_id,
                        'is_installed': True,
                        'depots': self.db.get_appid_depots(app_id),
                        'validation': self.validate_installation(app_id)
                    }
                    status['games'].append(game_info)
                    status['total_games'] = 1
                    status['installed_games'] = 1
                else:
                    status['total_games'] = 1
                    status['installed_games'] = 0
            else:
                # All games status
                all_appids = self.db.get_all_installed_appids()
                status['total_games'] = len(all_appids)
                status['installed_games'] = len(all_appids)
                
                for appid in all_appids:
                    game_info = {
                        'app_id': appid,
                        'is_installed': True,
                        'depots': self.db.get_appid_depots(appid),
                        'validation': self.validate_installation(appid)
                    }
                    status['games'].append(game_info)
            
            # Generate summary statistics
            status['summary']['database_entries'] = len(status['games'])
            
            # Count valid components across all games
            for game in status['games']:
                validation = game.get('validation', {})
                components = validation.get('components', {})
                
                if components.get('greenluma'):
                    status['summary']['greenluma_entries'] += 1
                if components.get('config_vdf'):
                    status['summary']['config_vdf_depots'] += len(game.get('depots', []))
                if components.get('manifests'):
                    status['summary']['manifest_files'] += 1
                if components.get('acf'):
                    status['summary']['acf_files'] += 1
        
        except Exception as e:
            status['error'] = f"Failed to get installation status: {e}"
        
        return status


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