# game_installer.py
#
# A module for installing and uninstalling games in SuperSexySteam.
# Handles the complete workflow for adding new games and removing existing ones.

import logging
from pathlib import Path
import shutil
from typing import Dict, List, Optional
from database_manager import get_database_manager
from lua_parser import parse_lua_for_all_depots, parse_all_lua_files_structured
from greenluma_manager import process_single_appid_for_greenluma, remove_appid_from_greenluma
from vdf_updater import add_depots_to_config_vdf, remove_depots_from_config_vdf
from depot_cache_manager import copy_manifests_for_appid, remove_manifests_for_appid
from acfgen import generate_acf_for_appid
from steam_game_search import get_game_name_by_appid
from steamtools import copy_manifests_to_depotcache, copy_lua_to_stplug_in
# Import the centralized uninstaller
from system_cleaner import uninstall_specific_appid

# Configure logging
logger = logging.getLogger(__name__)


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
        logger.info("Initializing GameInstaller")
        self.config = config
        self.db = get_database_manager()
        
        # --- Centralized Path Validation ---
        # Get paths from config once and validate them.
        steam_path_str = self.config.get('Paths', 'steam_path', fallback='')
        greenluma_path_str = self.config.get('Paths', 'greenluma_path', fallback='')
        
        logger.debug(f"Steam path from config: '{steam_path_str}'")
        logger.debug(f"GreenLuma path from config: '{greenluma_path_str}'")
        
        self.steam_path = Path(steam_path_str) if steam_path_str else Path()
        self.greenluma_path = Path(greenluma_path_str) if greenluma_path_str else Path()
        
        self.is_steam_path_valid = self.steam_path.exists() and self.steam_path.is_dir()
        self.is_greenluma_path_valid = self.greenluma_path.exists() and self.greenluma_path.is_dir()
        
        if not self.is_steam_path_valid:
            logger.warning(f"Steam path is not configured or invalid: '{self.steam_path}'")
        else:
            logger.info(f"Steam path validated: {self.steam_path}")
            
        if not self.is_greenluma_path_valid:
            logger.warning(f"GreenLuma path is not configured or invalid: '{self.greenluma_path}'")
        else:
            logger.info(f"GreenLuma path validated: {self.greenluma_path}")
            
        logger.info("GameInstaller initialization complete")

    def install_game(self, app_id: str, data_folder: str) -> Dict[str, any]:
        """
        Install a game by processing its lua file and performing all necessary operations.
        
        Args:
            app_id (str): The Steam AppID to install
            data_folder (str): Path to the folder containing the game's lua and manifest files
            
        Returns:
            Dict[str, any]: Result dictionary with success status, errors, and statistics
        """
        logger.info(f"Starting installation for AppID {app_id}")
        logger.debug(f"Data folder: {data_folder}")
        
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'stats': {
                'depots_processed': 0,
                'manifests_copied': 0,
                'manifests_tracked': 0,
                'greenluma_updated': False,
                'config_vdf_updated': False,
                'acf_generated': False
            }
        }
        
        try:
            # Step 1: Fetch game name from Steam API first
            logger.debug(f"Fetching game name for AppID {app_id}")
            game_name = get_game_name_by_appid(app_id)
            logger.info(f"Retrieved game name: {game_name}")
            
            # Step 2: Parse the lua file to extract depot information (with game name for proper depot naming)
            data_folder_path = Path(data_folder)
            lua_file = data_folder_path / f"{app_id}.lua"
            logger.debug(f"Looking for lua file: {lua_file}")
            
            if not lua_file.exists():
                error_msg = f"Lua file not found: {lua_file}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            logger.debug(f"Parsing lua file with game name '{game_name}': {lua_file}")
            lua_result = parse_lua_for_all_depots(str(lua_file), game_name)
            if not lua_result or not lua_result.get('depots'):
                error_msg = f"No depots found in lua file: {lua_file}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            depots = lua_result['depots']
            result['stats']['depots_processed'] = len(depots)
            logger.info(f"Found {len(depots)} depots in lua file")
            logger.debug(f"Depot IDs: {[d.get('depot_id', 'unknown') for d in depots]}")

            # Step 3: Collect manifest file names for database tracking
            logger.debug(f"Collecting manifest files from: {data_folder_path}")
            manifest_files = list(data_folder_path.glob("*.manifest"))
            manifest_filenames = [f.name for f in manifest_files]
            result['stats']['manifests_tracked'] = len(manifest_filenames)
            logger.info(f"Found {len(manifest_filenames)} manifest files to track in database")
            logger.debug(f"Manifest files: {manifest_filenames}")

            # Step 4: Add to database with game name, depots, and manifest filenames
            logger.debug(f"Adding AppID {app_id} to database with {len(depots)} depots and {len(manifest_filenames)} manifests")
            if not self.db.add_appid_with_depots(app_id, depots, manifest_filenames, game_name):
                error_msg = "Failed to add AppID, depots, and manifests to database"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            logger.info(f"Added AppID {app_id} ({game_name}) with {len(depots)} depots and {len(manifest_filenames)} manifests to database")
            
            # Step 4.5: Show depot selection popup for optional depot removal
            result['show_depot_popup'] = True
            result['popup_data'] = {
                'app_id': app_id,
                'game_name': game_name,
                'depots': depots,
                'data_folder': data_folder
            }
            
            # Set success to "waiting" to indicate installation is paused, not failed
            result['success'] = "waiting"
            
            # Return here to show depot popup - remaining steps will continue after user selection
            logger.info(f"Installation paused at depot selection for AppID {app_id}")
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error during installation: {e}"
            logger.error(error_msg)
            logger.debug("Installation exception:", exc_info=True)
            result['errors'].append(error_msg)
        
        return result
    
    def continue_installation(self, app_id: str, data_folder: str) -> Dict[str, any]:
        """
        Continue installation after depot selection popup is handled.
        This completes steps 5-9 of the installation process.
        
        Args:
            app_id (str): The Steam AppID being installed
            data_folder (str): Path to the folder containing the game's lua and manifest files
            
        Returns:
            Dict[str, any]: Result dictionary with success status, errors, and statistics
        """
        logger.info(f"Continuing installation for AppID {app_id} after depot selection")
        logger.debug(f"Data folder: {data_folder}")
        
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'stats': {
                'depots_processed': 0,
                'manifests_copied': 0,
                'manifests_tracked': 0,
                'greenluma_updated': False,
                'config_vdf_updated': False,
                'acf_generated': False,
                'steam_manifests_copied': 0,
                'steam_lua_copied': False
            }
        }
        
        try:
            # Parse lua file again to get current depot state (after potential removals)
            all_apps = parse_all_lua_files_structured(data_folder)
            if not all_apps or len(all_apps) == 0:
                error_msg = "Failed to parse lua files for continuation"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            app_data = all_apps[0]  # Get first app
            depots = app_data['depots']
            result['stats']['depots_processed'] = len(depots)
            
            logger.info(f"Continuing with {len(depots)} depots after selection")
            
            # Step 5: Update GreenLuma
            if self.is_greenluma_path_valid:
                # Check if GreenLuma is disabled in config
                disable_greenluma = self.config.getboolean('Settings', 'disable_greenluma', fallback=False)
                if disable_greenluma:
                    logger.info(f"GreenLuma is disabled in config, skipping GreenLuma operations for AppID {app_id}")
                    result['stats']['greenluma_skipped'] = True
                else:
                    try:
                        logger.debug(f"Updating GreenLuma for AppID {app_id}")
                        greenluma_result = process_single_appid_for_greenluma(str(self.greenluma_path), app_id, depots)
                        if greenluma_result['success']:
                            result['stats']['greenluma_updated'] = True
                            logger.info(f"GreenLuma updated successfully for AppID {app_id}")
                        else:
                            warning_msg = f"GreenLuma update warnings: {greenluma_result.get('errors', [])}"
                            logger.warning(warning_msg)
                            result['warnings'].extend(greenluma_result.get('errors', []))
                    except Exception as e:
                        warning_msg = f"GreenLuma update failed: {e}"
                        logger.warning(warning_msg)
                        logger.debug("GreenLuma update exception:", exc_info=True)
                        result['warnings'].append(warning_msg)
            else:
                warning_msg = "Invalid GreenLuma path, skipping GreenLuma update"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
            
            # Step 6: Update config.vdf
            if self.is_steam_path_valid:
                # Check if VDF parsing is disabled in config
                disable_vdf_parsing = self.config.getboolean('Settings', 'disable_vdf_parsing', fallback=False)
                if disable_vdf_parsing:
                    logger.info(f"VDF parsing is disabled in config, skipping config.vdf update for AppID {app_id}")
                    result['stats']['vdf_parsing_skipped'] = True
                else:
                    try:
                        config_vdf_path = self.steam_path / 'config' / 'config.vdf'
                        logger.debug(f"Updating config.vdf at: {config_vdf_path}")
                        
                        # Only add depots that have decryption keys
                        depots_with_keys = [d for d in depots if 'depot_key' in d]
                        logger.debug(f"Found {len(depots_with_keys)} depots with keys out of {len(depots)} total")
                        
                        if depots_with_keys:
                            vdf_success = add_depots_to_config_vdf(str(config_vdf_path), depots_with_keys)
                            if vdf_success:
                                result['stats']['config_vdf_updated'] = True
                                logger.info(f"Config.vdf updated with {len(depots_with_keys)} depot keys")
                            else:
                                warning_msg = "Failed to update config.vdf"
                                logger.warning(warning_msg)
                                result['warnings'].append(warning_msg)
                        else:
                            logger.info(f"No depot keys to add to config.vdf for AppID {app_id}")
                    except Exception as e:
                        warning_msg = f"Config.vdf update failed: {e}"
                        logger.warning(warning_msg)
                        logger.debug("Config.vdf update exception:", exc_info=True)
                        result['warnings'].append(warning_msg)
            else:
                warning_msg = "Invalid Steam path, skipping config.vdf update"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
            
            # Step 7: Copy manifest files to depot cache
            if self.is_steam_path_valid:
                # Check if depot cache manager is disabled in config
                disable_depotcache_manager = self.config.getboolean('Settings', 'disable_depotcache_manager', fallback=False)
                if disable_depotcache_manager:
                    logger.info(f"Depot cache manager is disabled in config, skipping depot cache operations for AppID {app_id}")
                    result['stats']['depotcache_manager_skipped'] = True
                else:
                    try:
                        logger.debug(f"Copying manifest files to depot cache for AppID {app_id}")
                        manifest_stats = copy_manifests_for_appid(str(self.steam_path), app_id, data_folder)
                        result['stats']['manifests_copied'] = manifest_stats.get('copied_count', 0)
                        if manifest_stats.get('copied_count', 0) > 0:
                            logger.info(f"Copied {manifest_stats['copied_count']} manifest files to depot cache")
                        else:
                            logger.info(f"No manifest files found to copy for AppID {app_id}")
                    except Exception as e:
                        warning_msg = f"Depot cache update failed: {e}"
                        logger.warning(warning_msg)
                        logger.debug("Depot cache update exception:", exc_info=True)
                        result['warnings'].append(warning_msg)
            
            # Step 8: Generate ACF file
            if self.is_steam_path_valid:
                # Check if ACF generation is disabled in config
                disable_acfgen = self.config.getboolean('Settings', 'disable_acfgen', fallback=False)
                if disable_acfgen:
                    logger.info(f"ACF generation is disabled in config, skipping for AppID {app_id}")
                    result['stats']['acf_skipped'] = True
                else:
                    try:
                        logger.debug(f"Generating ACF file for AppID {app_id}")
                        acf_success = generate_acf_for_appid(str(self.steam_path), app_id)
                        if acf_success:
                            result['stats']['acf_generated'] = True
                            logger.info(f"ACF file generated successfully for AppID {app_id}")
                        else:
                            warning_msg = "Failed to generate ACF file"
                            logger.warning(warning_msg)
                            result['warnings'].append(warning_msg)
                    except Exception as e:
                        warning_msg = f"ACF generation failed: {e}"
                        logger.warning(warning_msg)
                        logger.debug("ACF generation exception:", exc_info=True)
                        result['warnings'].append(warning_msg)
            
            # Step 9: Copy files to Steam directories
            if self.is_steam_path_valid:
                # Check if steamtools is disabled in config
                disable_steamtools = self.config.getboolean('Settings', 'disable_steamtools', fallback=True)
                if disable_steamtools:
                    logger.info(f"Steamtools is disabled in config, skipping Steam file operations for AppID {app_id}")
                    result['stats']['steamtools_skipped'] = True
                else:
                    try:
                        # Copy manifest files to Steam's depotcache
                        logger.debug(f"Copying manifest files to Steam depotcache for AppID {app_id}")
                        manifest_result = copy_manifests_to_depotcache(str(self.steam_path), app_id, data_folder)
                        if manifest_result['success']:
                            result['stats']['steam_manifests_copied'] = manifest_result.get('copied_count', 0)
                            logger.info(f"Copied {manifest_result['copied_count']} manifest files to Steam depotcache")
                        else:
                            if manifest_result['errors']:
                                result['warnings'].extend(manifest_result['errors'])
                            
                        # Copy lua file to Steam's stplug-in
                        logger.debug(f"Copying lua file to Steam stplug-in for AppID {app_id}")
                        lua_result = copy_lua_to_stplug_in(str(self.steam_path), app_id, data_folder)
                        if lua_result['success']:
                            result['stats']['steam_lua_copied'] = True
                            logger.info(f"Copied lua file to Steam stplug-in: {lua_result['copied_file']}")
                        else:
                            if lua_result['errors']:
                                result['warnings'].extend(lua_result['errors'])
                                
                    except Exception as e:
                        warning_msg = f"Steam file copying failed: {e}"
                        logger.warning(warning_msg)
                        logger.debug("Steam file copying exception:", exc_info=True)
                        result['warnings'].append(warning_msg)
            
            result['success'] = True
            logger.info(f"Installation continuation completed successfully for AppID {app_id}")
            logger.debug(f"Installation stats: {result['stats']}")
            
        except Exception as e:
            error_msg = f"Unexpected error during installation continuation: {e}"
            logger.error(error_msg)
            logger.debug("Installation continuation exception:", exc_info=True)
            result['errors'].append(error_msg)
        
        return result

    def uninstall_game(self, app_id: str) -> Dict[str, any]:
        """
        Uninstall a game by calling the centralized uninstaller from system_cleaner.
        This is used as the first step of an update process. It ensures all traces,
        including the data folder, are removed before a new version is installed.
        
        Args:
            app_id (str): The Steam AppID to uninstall
            
        Returns:
            Dict[str, any]: Result dictionary from the system_cleaner
        """
        logger.info(f"Delegating uninstallation of AppID {app_id} to system_cleaner for update")
        logger.debug(f"This unified function handles all aspects of uninstallation")
        # This unified function handles all aspects of uninstallation.
        # remove_data_folder is True because an update implies replacing the old data.
        return uninstall_specific_appid(self.config, app_id)
    
    def remove_depot_from_game(self, app_id: str, depot_id: str, data_folder: str) -> Dict[str, any]:
        """
        Remove a specific depot from an installed game.
        This includes removing from lua file, manifest files, and database.
        
        Args:
            app_id (str): The Steam AppID
            depot_id (str): The depot ID to remove
            data_folder (str): Path to the data folder containing lua and manifest files
            
        Returns:
            Dict[str, any]: Result dictionary with success status and details
        """
        logger.info(f"Removing depot {depot_id} from AppID {app_id}")
        
        result = {
            'success': False,
            'depot_id': depot_id,
            'errors': [],
            'warnings': [],
            'actions_completed': []
        }
        
        try:
            # First, get depot info from database to check if it has a decryption key
            depot_info = self.db.get_depot_info(app_id, depot_id)
            if not depot_info:
                error_msg = f"Depot {depot_id} not found in database for AppID {app_id}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            has_decryption_key = 'depot_key' in depot_info and depot_info['depot_key'] is not None
            logger.debug(f"Depot {depot_id} has decryption key: {has_decryption_key}")
            
            data_folder_path = Path(data_folder)
            
            # Step 1: Remove from lua file
            lua_files = list(data_folder_path.glob("*.lua"))
            if lua_files:
                lua_file = lua_files[0]  # Use first lua file found
                logger.debug(f"Removing depot {depot_id} from lua file: {lua_file}")
                
                if self._remove_depot_from_lua_file(str(lua_file), depot_id, has_decryption_key):
                    result['actions_completed'].append('lua_updated')
                    logger.info(f"Successfully removed depot {depot_id} from lua file")
                else:
                    warning_msg = f"Failed to remove depot {depot_id} from lua file"
                    logger.warning(warning_msg)
                    result['warnings'].append(warning_msg)
            else:
                warning_msg = f"No lua file found in {data_folder_path}"
                logger.warning(warning_msg)
                result['warnings'].append(warning_msg)
            
            # Step 2: Remove manifest files if depot had decryption key
            if has_decryption_key:
                # Find all manifest files that start with {depot_id}_
                matching_manifests = list(data_folder_path.glob(f"{depot_id}_*.manifest"))
                if matching_manifests:
                    deleted_count = 0
                    for manifest_file in matching_manifests:
                        try:
                            manifest_file.unlink()
                            deleted_count += 1
                            logger.info(f"Deleted manifest file: {manifest_file}")
                        except Exception as e:
                            warning_msg = f"Failed to delete manifest file {manifest_file}: {e}"
                            logger.warning(warning_msg)
                            result['warnings'].append(warning_msg)
                    
                    if deleted_count > 0:
                        result['actions_completed'].append('manifest_deleted')
                        if deleted_count > 1:
                            logger.info(f"Deleted {deleted_count} manifest files for depot {depot_id}")
                else:
                    logger.debug(f"No manifest files found for depot {depot_id} (pattern: {depot_id}_*.manifest)")
            
            # Step 3: Remove from database
            if self.db.remove_depot_from_appid(app_id, depot_id):
                result['actions_completed'].append('database_updated')
                logger.info(f"Successfully removed depot {depot_id} from database")
                result['success'] = True
            else:
                error_msg = f"Failed to remove depot {depot_id} from database"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            logger.info(f"Successfully removed depot {depot_id} from AppID {app_id}")
            
        except Exception as e:
            error_msg = f"Unexpected error removing depot {depot_id}: {e}"
            logger.error(error_msg)
            logger.debug("Depot removal exception:", exc_info=True)
            result['errors'].append(error_msg)
        
        return result
    
    def _remove_depot_from_lua_file(self, lua_file_path: str, depot_id: str, has_decryption_key: bool) -> bool:
        """
        Remove depot entries from lua file.
        Removes both addappid() and setManifestid() lines for the depot.
        
        Args:
            lua_file_path (str): Path to the lua file
            depot_id (str): Depot ID to remove
            has_decryption_key (bool): Whether the depot has a decryption key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            lua_path = Path(lua_file_path)
            if not lua_path.exists():
                logger.error(f"Lua file not found: {lua_file_path}")
                return False
            
            # Read the lua file
            with open(lua_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Track lines to keep
            new_lines = []
            removed_lines = 0
            
            for line in lines:
                line_stripped = line.strip()
                should_remove = False
                
                # Check for addappid line with this depot
                if (f'addappid({depot_id},' in line or f'addappid({depot_id})' in line or 
                    f'addappid("{depot_id}"' in line or f"addappid('{depot_id}'" in line):
                    should_remove = True
                    logger.debug(f"Removing addappid line for depot {depot_id}: {line_stripped}")
                
                # Check for setManifestid line if depot has decryption key
                elif has_decryption_key and (f'setManifestid({depot_id},' in line or 
                                           f'setManifestid("{depot_id}"' in line or f"setManifestid('{depot_id}'" in line):
                    should_remove = True
                    logger.debug(f"Removing setManifestid line for depot {depot_id}: {line_stripped}")
                
                if not should_remove:
                    new_lines.append(line)
                else:
                    removed_lines += 1
            
            # Write back the modified content
            with open(lua_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            logger.info(f"Removed {removed_lines} lines from lua file for depot {depot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing depot {depot_id} from lua file {lua_file_path}: {e}")
            return False
    
    def validate_installation(self, app_id: str) -> Dict[str, any]:
        """
        Validate that a game is properly installed across all systems.
        
        Args:
            app_id (str): The Steam AppID to validate
            
        Returns:
            Dict[str, any]: Validation result with detailed status
        """
        logger.info(f"Validating installation for AppID {app_id}")
        
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
            logger.debug(f"Checking database for AppID {app_id}")
            if self.db.is_appid_exists(app_id):
                result['components']['database'] = True
                logger.debug("Database component validation: PASS")
            else:
                error_msg = "AppID not found in database"
                logger.warning(f"Database component validation: FAIL - {error_msg}")
                result['errors'].append(error_msg)
                result['valid'] = False
            
            # Check GreenLuma
            if self.is_greenluma_path_valid:
                logger.debug(f"Checking GreenLuma for AppID {app_id}")
                applist_dir = self.greenluma_path / 'NormalMode' / 'AppList'
                applist_file = applist_dir / f"{app_id}.txt"
                if applist_file.exists():
                    result['components']['greenluma'] = True
                    logger.debug("GreenLuma component validation: PASS")
                else:
                    warning_msg = "AppID not found in GreenLuma AppList"
                    logger.debug(f"GreenLuma component validation: FAIL - {warning_msg}")
                    result['warnings'].append(warning_msg)
            else:
                logger.debug("Skipping GreenLuma validation - invalid path")
            
            # Check Steam config.vdf
            if self.is_steam_path_valid:
                logger.debug(f"Checking config.vdf for depot keys")
                from vdf_updater import get_existing_depot_keys
                config_vdf_path = self.steam_path / 'config' / 'config.vdf'
                if config_vdf_path.exists():
                    existing_keys = get_existing_depot_keys(str(config_vdf_path))
                    if existing_keys:
                        result['components']['config_vdf'] = True
                        logger.debug(f"Config.vdf component validation: PASS - {len(existing_keys)} keys found")
                    else:
                        warning_msg = "No depot keys found in config.vdf"
                        logger.debug(f"Config.vdf component validation: FAIL - {warning_msg}")
                        result['warnings'].append(warning_msg)
                else:
                    logger.warning(f"Config.vdf file not found: {config_vdf_path}")
            else:
                logger.debug("Skipping config.vdf validation - invalid Steam path")
            
            # Check manifests
            if self.is_steam_path_valid:
                logger.debug("Checking depot cache for manifest files")
                depotcache_path = self.steam_path / 'steamapps' / 'depotcache'
                if depotcache_path.is_dir():
                    manifest_count = len([f for f in depotcache_path.iterdir() 
                                        if f.suffix == '.manifest'])
                    if manifest_count > 0:
                        result['components']['manifests'] = True
                        logger.debug(f"Manifests component validation: PASS - {manifest_count} files found")
                    else:
                        warning_msg = "No manifest files found in depotcache"
                        logger.debug(f"Manifests component validation: FAIL - {warning_msg}")
                        result['warnings'].append(warning_msg)
                else:
                    logger.warning(f"Depot cache directory not found: {depotcache_path}")
            else:
                logger.debug("Skipping manifest validation - invalid Steam path")
            
            # Check ACF file
            if self.is_steam_path_valid:
                # Check if ACF generation is disabled in config
                disable_acfgen = self.config.getboolean('Settings', 'disable_acfgen', fallback=False)
                if disable_acfgen:
                    logger.debug("ACF validation skipped - ACF generation is disabled in config")
                    result['components']['acf'] = True  # Consider it valid since it's intentionally disabled
                else:
                    logger.debug(f"Checking ACF file for AppID {app_id}")
                    steamapps_path = self.steam_path / 'steamapps'
                    acf_file = steamapps_path / f"appmanifest_{app_id}.acf"
                    if acf_file.exists():
                        result['components']['acf'] = True
                        logger.debug("ACF component validation: PASS")
                    else:
                        warning_msg = "ACF file not found"
                        logger.debug(f"ACF component validation: FAIL - {warning_msg}")
                        result['warnings'].append(warning_msg)
            else:
                logger.debug("Skipping ACF validation - invalid Steam path")
            
        except Exception as e:
            error_msg = f"Validation error: {e}"
            logger.error(error_msg)
            logger.debug("Validation exception:", exc_info=True)
            result['errors'].append(error_msg)
            result['valid'] = False
        
        logger.info(f"Validation complete for AppID {app_id}: valid={result['valid']}, errors={len(result['errors'])}, warnings={len(result['warnings'])}")
        return result
    
    def get_installation_status(self, app_id: str = None) -> Dict[str, any]:
        """
        Get detailed installation status for one or all games.
        
        Args:
            app_id (str, optional): Specific AppID to check, or None for all
            
        Returns:
            Dict[str, any]: Installation status information
        """
        if app_id:
            logger.info(f"Getting installation status for AppID {app_id}")
        else:
            logger.info("Getting installation status for all games")
            
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
                logger.debug(f"Checking single game status for AppID {app_id}")
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
                    logger.debug(f"AppID {app_id} found in database")
                else:
                    status['total_games'] = 1
                    status['installed_games'] = 0
                    logger.debug(f"AppID {app_id} not found in database")
            else:
                # All games status
                logger.debug("Getting all installed AppIDs from database")
                all_appids = self.db.get_all_installed_appids()
                status['total_games'] = len(all_appids)
                status['installed_games'] = len(all_appids)
                logger.info(f"Found {len(all_appids)} installed games in database")
                
                for appid in all_appids:
                    logger.debug(f"Processing status for AppID {appid}")
                    game_info = {
                        'app_id': appid,
                        'is_installed': True,
                        'depots': self.db.get_appid_depots(appid),
                        'validation': self.validate_installation(appid)
                    }
                    status['games'].append(game_info)
            
            # Generate summary statistics
            status['summary']['database_entries'] = len(status['games'])
            logger.debug("Generating summary statistics")
            
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
            error_msg = f"Failed to get installation status: {e}"
            logger.error(error_msg)
            logger.debug("Installation status exception:", exc_info=True)
            status['error'] = error_msg
        
        logger.info(f"Installation status complete: {status['installed_games']}/{status['total_games']} games")
        logger.debug(f"Summary: {status['summary']}")
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
    logger.info(f"Installing game from data folder - AppID: {app_id}, Folder: {data_folder}")
    installer = GameInstaller(config)
    result = installer.install_game(app_id, data_folder)
    logger.info(f"Installation result: success={result.get('success', False)}")
    return result


