# app_logic.py
#
# The central brain of SuperSexySteam application.
# This module serves as the single point of contact between the GUI and all
# business logic operations. It orchestrates all functionality including:
# - Steam process management
# - Game installation/uninstallation workflows  
# - Database operations
# - File management
# - System cleanup operations
# - Game search functionality
#
# The GUI should only call functions from this module and display results.

import configparser
import logging
from pathlib import Path
import shutil
import time
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)
# Import our custom modules
from greenluma_manager import configure_greenluma_injector
from database_manager import get_database_manager
from game_installer import GameInstaller
from system_cleaner import clear_all_data, uninstall_specific_appid
from steam_game_search import search_games, find_appid
from steam_manager import is_steam_running, terminate_steam, run_steam_with_dll_injector


class SuperSexySteamLogic:
    """
    The main application logic controller.
    
    This class encapsulates all business logic and serves as the single interface
    between the GUI and the underlying system operations.
    """
    
    def __init__(self, config: configparser.ConfigParser):
        """
        Initialize the application logic with configuration.
        
        Args:
            config (configparser.ConfigParser): The loaded application configuration
        """
        logger.info("Initializing SuperSexySteam application logic")
        self.config = config
        self.db = get_database_manager()
        self.game_installer = GameInstaller(config)
        
        # Initialize by terminating Steam if running
        logger.debug("Performing startup initialization")
        self._terminate_steam_on_startup()
        
        # Update missing game names for existing databases (migration)
        logger.debug("Performing database migration")
        self._perform_database_migration()
        
        # Check and store Steam ID on first boot
        logger.debug("Checking Steam ID initialization")
        self._initialize_steam_id()
        
        logger.info("SuperSexySteam application logic initialized successfully")
    
    def _terminate_steam_on_startup(self) -> None:
        """Terminate Steam processes during application startup."""
        logger.info("Checking for running Steam processes during startup")
        if is_steam_running():
            logger.info("Steam is running, initiating termination")
            try:
                result = terminate_steam()
                if result['success']:
                    if result['terminated_processes'] > 0:
                        logger.info(f"Terminated {result['terminated_processes']} Steam process(es) at startup")
                    else:
                        logger.info("No Steam processes to terminate at startup")
                else:
                    logger.warning(f"Failed to terminate Steam at startup: {'; '.join(result['errors'])}")
            except Exception as e:
                logger.error(f"Error terminating Steam at startup: {e}")
                logger.debug("Steam termination startup exception:", exc_info=True)
        else:
            logger.info("Steam is not running during startup check")
    
    def _perform_database_migration(self) -> None:
        """Perform database migration to update missing game names."""
        logger.debug("Starting database migration for missing game names")
        try:
            updated_count = self.db.update_missing_game_names()
            if updated_count > 0:
                logger.info(f"Updated {updated_count} game names during database migration")
            else:
                logger.debug("No game names needed updating during migration")
        except Exception as e:
            logger.warning(f"Failed to update missing game names: {e}")
            logger.debug("Database migration exception:", exc_info=True)

    def _initialize_steam_id(self) -> None:
        """Initialize Steam ID by reading from config.vdf if not already stored."""
        logger.debug("Initializing Steam ID")
        try:
            # Check if Steam ID is already stored
            stored_steam_id = self.db.get_steam_id()
            if stored_steam_id:
                logger.info(f"Steam ID already stored: {stored_steam_id}")
                return

            # Try to read Steam ID from config.vdf
            steam_path = self.config.get('Paths', 'steam_path', fallback='')
            if not steam_path:
                logger.warning("Steam path not configured, cannot read Steam ID")
                return

            config_vdf_path = Path(steam_path) / 'config' / 'config.vdf'
            if not config_vdf_path.exists():
                logger.warning(f"config.vdf not found at {config_vdf_path}")
                return

            # Import VDF parser function
            from vdf_updater import get_steam_id_from_config
            
            steam_id = get_steam_id_from_config(config_vdf_path)
            if steam_id:
                # Store the Steam ID in database
                success = self.db.set_steam_id(steam_id)
                if not success:
                    logger.error("Failed to store Steam ID in database")
            else:
                logger.warning("Could not find Steam ID in config.vdf")

        except Exception as e:
            logger.error(f"Failed to initialize Steam ID: {e}")
            logger.debug("Steam ID initialization exception:", exc_info=True)
    
    # =============================================================================
    # --- DATABASE OPERATIONS ---
    # =============================================================================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dict containing database statistics with success flag
        """
        logger.debug("Retrieving database statistics")
        try:
            stats = self.db.get_database_stats()
            logger.info(f"Database stats retrieved: {stats['installed_appids']} games, {stats['total_depots']} depots, {stats['depots_with_keys']} with keys")
            return {
                'success': True,
                'stats': stats,
                'formatted_text': f"Games: {stats['installed_appids']} installed | Depots: {stats['total_depots']} | With Keys: {stats['depots_with_keys']}"
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            logger.debug("Database stats exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'formatted_text': "Error loading database statistics"
            }
    
    def get_installed_games(self) -> Dict[str, Any]:
        """
        Get list of all installed games.
        
        Returns:
            Dict containing list of installed games with success flag
        """
        logger.debug("Retrieving installed games list")
        try:
            games = self.db.get_installed_games()
            logger.info(f"Retrieved {len(games)} installed games")
            return {
                'success': True,
                'games': games,
                'count': len(games)
            }
        except Exception as e:
            logger.error(f"Failed to get installed games: {e}")
            logger.debug("Get installed games exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'games': [],
                'count': 0
            }
    
    def get_steam_id(self) -> Optional[str]:
        """
        Get the stored Steam ID.
        
        Returns:
            str or None: The stored Steam ID if available, None otherwise
        """
        logger.debug("Retrieving stored Steam ID")
        try:
            steam_id = self.db.get_steam_id()
            if steam_id:
                logger.debug(f"Retrieved Steam ID: {steam_id}")
            else:
                logger.debug("No Steam ID stored")
            return steam_id
        except Exception as e:
            logger.error(f"Failed to get Steam ID: {e}")
            logger.debug("Get Steam ID exception:", exc_info=True)
            return None
    
    # =============================================================================
    # --- STEAM PROCESS MANAGEMENT ---
    # =============================================================================
    
    def check_steam_status(self) -> Dict[str, Any]:
        """
        Check if Steam is currently running.
        
        Returns:
            Dict with Steam status information
        """
        logger.debug("Checking Steam running status")
        try:
            running = is_steam_running()
            status_msg = "Steam is running" if running else "Steam is not running"
            logger.info(status_msg)
            return {
                'success': True,
                'is_running': running,
                'message': status_msg
            }
        except Exception as e:
            logger.error(f"Failed to check Steam status: {e}")
            logger.debug("Steam status check exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'is_running': False,
                'message': f"Error checking Steam status: {e}"
            }
    
    def terminate_steam_processes(self) -> Dict[str, Any]:
        """
        Terminate all Steam processes.
        
        Returns:
            Dict with termination results
        """
        logger.info("Attempting to terminate Steam processes")
        try:
            result = terminate_steam()
            if result['success']:
                message = f"Terminated {result['terminated_processes']} Steam process(es)" if result['terminated_processes'] > 0 else "No Steam processes to terminate"
                logger.info(message)
                return {
                    'success': True,
                    'terminated_processes': result['terminated_processes'],
                    'message': message
                }
            else:
                error_msg = '; '.join(result['errors'])
                logger.error(f"Failed to terminate Steam: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'message': f"Failed to terminate Steam: {error_msg}"
                }
        except Exception as e:
            logger.error(f"Failed to terminate Steam: {e}")
            logger.debug("Steam termination exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': f"Error terminating Steam: {e}"
            }
    
    def wait_for_steam_termination(self, max_wait_seconds: int = 15, check_interval: float = 0.5) -> Dict[str, Any]:
        """
        Wait for Steam processes to fully terminate with active polling.
        
        Args:
            max_wait_seconds: Maximum time to wait for termination
            check_interval: How often to check (in seconds)
            
        Returns:
            Dict with termination wait results
        """
        logger.info(f"Waiting for Steam termination (max {max_wait_seconds}s, checking every {check_interval}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            if not is_steam_running():
                elapsed = int(time.time() - start_time)
                logger.info(f"Steam fully terminated after {elapsed} seconds")
                return {
                    'success': True,
                    'terminated': True,
                    'elapsed_time': elapsed,
                    'message': "Steam fully terminated"
                }
            
            time.sleep(check_interval)
        
        logger.warning(f"Steam termination timeout after {max_wait_seconds} seconds")
        return {
            'success': True,
            'terminated': False,
            'elapsed_time': max_wait_seconds,
            'message': "Timeout: Steam may not have fully terminated"
        }
    
    def launch_steam(self) -> Dict[str, Any]:
        """
        Launch Steam via DLLInjector with full process management.
        
        Returns:
            Dict with launch results and status messages
        """
        logger.info("Starting Steam launch process")
        results = {
            'success': False,
            'messages': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Step 1: Check if Steam is running
            logger.debug("Step 1: Checking if Steam is currently running")
            if is_steam_running():
                logger.info("Steam is running, terminating existing processes")
                results['messages'].append("Steam is running. Terminating existing processes...")
                
                # Step 2: Terminate Steam
                logger.debug("Step 2: Terminating Steam processes")
                terminate_result = self.terminate_steam_processes()
                if terminate_result['success']:
                    results['messages'].append(terminate_result['message'])
                    logger.debug("Steam termination request successful")
                else:
                    results['errors'].append(terminate_result['message'])
                    logger.error("Steam termination failed")
                    return results
                
                # Step 3: Wait for processes to terminate
                logger.debug("Step 3: Waiting for Steam to fully terminate")
                results['messages'].append("Waiting for Steam to fully terminate...")
                wait_result = self.wait_for_steam_termination()
                if wait_result['terminated']:
                    results['messages'].append(wait_result['message'])
                    logger.debug("Steam fully terminated")
                else:
                    results['warnings'].append(wait_result['message'])
                    logger.warning("Steam may not have fully terminated")
            else:
                logger.debug("Steam is not running, proceeding to launch")
            
            # Step 4: Launch Steam via DLLInjector
            logger.info("Launching Steam via DLLInjector")
            results['messages'].append("Launching Steam via DLLInjector...")
            launch_result = run_steam_with_dll_injector(self.config)
            
            if launch_result['success']:
                results['success'] = True
                results['messages'].append("Steam launched successfully! 🚀")
                logger.info("Steam launched successfully via DLLInjector")
            else:
                error_msg = '; '.join(launch_result['errors'])
                results['errors'].append(f"Failed to launch Steam: {error_msg}")
                logger.error(f"Failed to launch Steam: {error_msg}")
                
        except Exception as e:
            error_msg = f"Error launching Steam: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            logger.debug("Steam launch exception:", exc_info=True)
        
        logger.info(f"Steam launch process completed - Success: {results['success']}")
        return results
    
    # =============================================================================
    # --- GAME INSTALLATION/UNINSTALLATION ---
    # =============================================================================
    
    def validate_dropped_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Validate dropped files for game installation.
        
        Args:
            file_paths: List of file paths that were dropped
            
        Returns:
            Dict with validation results
        """
        logger.info(f"Validating {len(file_paths)} dropped files")
        logger.debug(f"Dropped files: {file_paths}")
        
        # Find .lua files
        lua_files = [p for p in file_paths if p.lower().endswith('.lua')]
        logger.debug(f"Found {len(lua_files)} .lua files")
        
        if len(lua_files) != 1:
            error_msg = f"Error: {len(lua_files) if len(lua_files) > 1 else 'No'} .lua file{'s' if len(lua_files) > 1 else ''} dropped. Please drop exactly one."
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'app_id': None,
                'lua_path': None
            }
        
        # Extract AppID from filename
        lua_path = Path(lua_files[0])
        app_id = lua_path.stem
        logger.debug(f"Extracted AppID from filename: {app_id}")
        
        if not app_id.isdigit():
            error_msg = f"Invalid Lua filename: '{lua_path.name}'. Name must be a numeric AppID."
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'app_id': None,
                'lua_path': str(lua_path)
            }
        
        valid_files = [p for p in file_paths if Path(p).suffix.lower() in ('.lua', '.manifest')]
        logger.info(f"File validation successful - AppID: {app_id}, Valid files: {len(valid_files)}")
        
        return {
            'success': True,
            'app_id': app_id,
            'lua_path': str(lua_path),
            'all_files': file_paths,
            'valid_files': valid_files
        }
    
    def organize_game_files(self, app_id: str, file_paths: List[str]) -> Dict[str, Any]:
        """
        Organize dropped files into the appropriate data directory structure.
        
        Args:
            app_id: The AppID for the game
            file_paths: List of valid file paths to organize
            
        Returns:
            Dict with organization results
        """
        logger.info(f"Organizing {len(file_paths)} files for AppID {app_id}")
        try:
            script_directory = Path(__file__).parent
            destination_directory = script_directory / "data" / app_id
            logger.debug(f"Creating destination directory: {destination_directory}")
            destination_directory.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            errors = []
            
            for path_str in file_paths:
                path = Path(path_str)
                if path.suffix.lower() in ('.lua', '.manifest'):
                    try:
                        dest_path = destination_directory / path.name
                        logger.debug(f"Copying {path.name} to {dest_path}")
                        shutil.copy2(path, dest_path)
                        copied_files.append(str(dest_path))
                    except Exception as e:
                        error_msg = f"Error copying '{path.name}': {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
            
            if errors:
                # Clean up on any failure
                logger.warning("File copy errors occurred, cleaning up destination directory")
                shutil.rmtree(destination_directory, ignore_errors=True)
                return {
                    'success': False,
                    'errors': errors,
                    'destination_directory': str(destination_directory)
                }
            
            logger.info(f"Successfully organized {len(copied_files)} files for AppID {app_id}")
            return {
                'success': True,
                'destination_directory': str(destination_directory),
                'copied_files': copied_files,
                'files_copied': len(copied_files)
            }
            
        except Exception as e:
            error_msg = f"Failed to organize files: {e}"
            logger.error(error_msg)
            logger.debug("File organization exception:", exc_info=True)
            return {
                'success': False,
                'errors': [error_msg],
                'destination_directory': str(destination_directory) if 'destination_directory' in locals() else None
            }
    
    def process_game_installation(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Complete game installation workflow from dropped files.
        
        Args:
            file_paths: List of file paths that were dropped
            
        Returns:
            Dict with complete installation results
        """
        logger.info(f"Starting game installation process for {len(file_paths)} files")
        
        # Step 1: Validate files
        logger.debug("Step 1: Validating dropped files")
        validation_result = self.validate_dropped_files(file_paths)
        if not validation_result['success']:
            logger.error(f"File validation failed: {validation_result['error']}")
            return {
                'success': False,
                'error': validation_result['error'],
                'stage': 'validation'
            }
        
        app_id = validation_result['app_id']
        logger.info(f"Installing game with AppID: {app_id}")
        
        # Step 2: Check if this is an update
        logger.debug("Step 2: Checking if this is an update")
        is_update = self.db.is_appid_exists(app_id)
        logger.info(f"Installation type: {'Update' if is_update else 'New installation'}")
        
        result = {
            'success': False,
            'app_id': app_id,
            'is_update': is_update,
            'stages_completed': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Step 3: Handle existing installation (uninstall if update)
            if is_update:
                logger.info(f"Uninstalling existing AppID {app_id} for update")
                result['stages_completed'].append('update_detection')
                uninstall_result = self.game_installer.uninstall_game(app_id)
                if uninstall_result['success']:
                    result['stages_completed'].append('old_version_removed')
                    logger.info(f"Successfully uninstalled existing AppID {app_id} for update")
                else:
                    # Allow continuing but show warnings
                    result['warnings'].extend(uninstall_result['errors'])
                    logger.warning(f"Uninstall errors for AppID {app_id}: {uninstall_result['errors']}")
            
            # Step 4: Organize files
            logger.debug("Step 4: Organizing game files")
            organize_result = self.organize_game_files(app_id, validation_result['valid_files'])
            if not organize_result['success']:
                result['errors'].extend(organize_result['errors'])
                logger.error(f"Failed to organize files for AppID {app_id}")
                return result
            
            result['stages_completed'].append('files_organized')
            destination_directory = organize_result['destination_directory']
            logger.debug(f"Files organized to: {destination_directory}")
            
            # Step 5: Install the game
            logger.info(f"Installing game AppID {app_id} from {destination_directory}")
            install_result = self.game_installer.install_game(app_id, destination_directory)
            
            if install_result['success']:
                result['success'] = True
                result['stages_completed'].append('game_installed')
                result['stats'] = install_result['stats']
                result['action_verb'] = "Updated" if is_update else "Installed"
                logger.info(f"Successfully installed game AppID {app_id}")
                
                # Add any warnings from installation
                if 'warnings' in install_result:
                    result['warnings'].extend(install_result['warnings'])
                
                return result
            else:
                # Installation failed, clean up
                result['errors'].extend(install_result['errors'])
                result['stages_completed'].append('installation_failed')
                logger.error(f"Failed to install game AppID {app_id}: {install_result['errors']}")
                
                # Clean up the data folder
                if Path(destination_directory).exists():
                    logger.debug(f"Cleaning up destination directory after failed installation: {destination_directory}")
                    shutil.rmtree(destination_directory, ignore_errors=True)
                
                return result
            
        except Exception as e:
            error_msg = f"Unexpected error during installation: {e}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            logger.debug("Game installation exception:", exc_info=True)
            
            # Clean up if destination directory was created
            if 'destination_directory' in locals() and Path(destination_directory).exists():
                logger.debug(f"Cleaning up destination directory after exception: {destination_directory}")
                shutil.rmtree(destination_directory, ignore_errors=True)
            
            return result
    
    def uninstall_game(self, app_id: str) -> Dict[str, Any]:
        """
        Uninstall a specific game by AppID.
        
        Args:
            app_id: The AppID to uninstall (as string)
            
        Returns:
            Dict with uninstallation results
        """
        logger.info(f"Starting uninstallation for AppID: {app_id}")
        
        # Validate AppID
        if not app_id or not app_id.strip():
            logger.error("AppID cannot be empty for uninstallation")
            return {
                'success': False,
                'error': "AppID cannot be empty",
                'app_id': app_id
            }
        
        app_id = app_id.strip()
        
        if not app_id.isdigit():
            logger.error(f"Invalid AppID for uninstallation: '{app_id}'. Must be numeric.")
            return {
                'success': False,
                'error': f"Invalid AppID: '{app_id}'. Must be numeric.",
                'app_id': app_id
            }
        
        try:
            logger.debug(f"Calling uninstall_specific_appid for AppID {app_id}")
            result = uninstall_specific_appid(self.config, app_id)
            
            if result['success']:
                stats = result['stats']
                summary_parts = []
                
                if stats['database_entry_removed']:
                    summary_parts.append("database entry")
                if stats['data_folder_removed']:
                    summary_parts.append("data folder")
                if stats['depot_keys_removed'] > 0:
                    summary_parts.append(f"{stats['depot_keys_removed']} depot keys")
                if stats['manifest_files_removed'] > 0:
                    summary_parts.append(f"{stats['manifest_files_removed']} manifest files")
                if stats['acf_file_removed']:
                    summary_parts.append("ACF file")
                if stats['greenluma_files_removed'] > 0:
                    summary_parts.append(f"{stats['greenluma_files_removed']} GreenLuma entries")
                
                summary = f"Removed: {', '.join(summary_parts) if summary_parts else 'no components found'}"
                logger.info(f"Successfully uninstalled AppID {app_id}: {summary}")
                
                return {
                    'success': True,
                    'app_id': app_id,
                    'stats': stats,
                    'summary': summary,
                    'warnings': result.get('warnings', [])
                }
            else:
                error_msg = '; '.join(result['errors'])
                logger.error(f"Failed to uninstall AppID {app_id}: {error_msg}")
                return {
                    'success': False,
                    'app_id': app_id,
                    'error': error_msg,
                    'errors': result['errors']
                }
                
        except Exception as e:
            logger.error(f"Failed to uninstall AppID {app_id}: {e}")
            logger.debug("Uninstall exception:", exc_info=True)
            return {
                'success': False,
                'app_id': app_id,
                'error': str(e)
            }
    
    # =============================================================================
    # --- SYSTEM CLEANUP ---
    # =============================================================================
    
    def clear_all_application_data(self) -> Dict[str, Any]:
        """
        Comprehensive data clearing that removes all SuperSexySteam data.
        
        Returns:
            Dict with cleanup results
        """
        logger.info("Starting comprehensive application data clearing")
        try:
            result = clear_all_data(self.config)
            
            if result['success']:
                stats = result['stats']
                summary_parts = []
                
                if stats['database_cleared']:
                    summary_parts.append("database")
                if stats['data_folder_cleared']:
                    summary_parts.append("data folder")
                if stats['depot_keys_removed'] > 0:
                    summary_parts.append(f"{stats['depot_keys_removed']} depot keys")
                if stats['depotcache_files_removed'] > 0:
                    summary_parts.append(f"{stats['depotcache_files_removed']} manifest files")
                if stats['acf_files_removed'] > 0:
                    summary_parts.append(f"{stats['acf_files_removed']} ACF files")
                if stats['greenluma_files_removed'] > 0:
                    summary_parts.append(f"{stats['greenluma_files_removed']} GreenLuma entries")
                
                summary = f"Cleared: {', '.join(summary_parts) if summary_parts else 'no data found'}"
                logger.info(f"Successfully cleared application data: {summary}")
                
                return {
                    'success': True,
                    'stats': stats,
                    'summary': summary,
                    'warnings': result.get('warnings', [])
                }
            else:
                error_msg = '; '.join(result['errors'])
                logger.error(f"Failed to clear application data: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'errors': result['errors']
                }
                
        except Exception as e:
            logger.error(f"Failed to clear application data: {e}")
            logger.debug("Clear data exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # =============================================================================
    # --- GAME SEARCH ---
    # =============================================================================
    
    def search_steam_games(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for Steam games by name.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            Dict with search results
        """
        logger.info(f"Searching Steam games with query: '{query}' (max_results: {max_results})")
        
        if not query or not query.strip():
            logger.error("Search query cannot be empty")
            return {
                'success': False,
                'error': "Search query cannot be empty",
                'games': [],
                'count': 0
            }
        
        try:
            games = search_games(query.strip(), max_results=max_results)
            logger.info(f"Steam game search returned {len(games)} results for query: '{query.strip()}'")
            
            return {
                'success': True,
                'games': games,
                'count': len(games),
                'query': query.strip()
            }
            
        except Exception as e:
            logger.error(f"Steam game search failed: {e}")
            logger.debug("Steam game search exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'games': [],
                'count': 0,
                'query': query.strip() if query else ""
            }
    
    # =============================================================================
    # --- CONFIGURATION MANAGEMENT ---
    # =============================================================================
    
    @staticmethod
    def load_configuration() -> Optional[configparser.ConfigParser]:
        """
        Load existing configuration file.
        
        Returns:
            ConfigParser object if successful, None if config file not found
        """
        logger.debug("Loading application configuration")
        config_file = Path('config.ini')
        config = configparser.ConfigParser()
        
        if not config_file.exists():
            logger.info("Configuration file not found")
            return None
        else:
            logger.debug(f"Reading configuration from {config_file}")
            config.read(config_file)
            logger.info("Configuration loaded successfully")
            return config
    
    @staticmethod
    def create_configuration(steam_path: str, greenluma_path: str) -> configparser.ConfigParser:
        """
        Create and save a new configuration file.
        
        Args:
            steam_path: Path to Steam installation
            greenluma_path: Path to GreenLuma directory
            
        Returns:
            ConfigParser object with the new configuration
        """
        logger.info("Creating new configuration file")
        
        # Create and save configuration
        logger.debug("Creating configuration file")
        config = configparser.ConfigParser()
        config['Paths'] = {
            'steam_path': steam_path, 
            'greenluma_path': str(greenluma_path)
        }
        
        config_file = Path('config.ini')
        with config_file.open('w') as f:
            config.write(f)
        logger.info("Configuration file created successfully")
        
        # Configure the GreenLuma DLLInjector.ini with the paths
        logger.debug("Configuring GreenLuma DLLInjector")
        configure_greenluma_injector(steam_path, str(greenluma_path))
        logger.info("Configuration setup completed successfully")
        return config
    
    # =============================================================================
    # --- UTILITY METHODS ---
    # =============================================================================
    
    def get_app_info(self) -> Dict[str, Any]:
        """
        Get general application information and status.
        
        Returns:
            Dict with application information
        """
        logger.debug("Retrieving application information and status")
        try:
            steam_status = self.check_steam_status()
            db_stats = self.get_database_stats()
            
            logger.debug("Successfully retrieved application info")
            return {
                'success': True,
                'steam_status': steam_status,
                'database_stats': db_stats,
                'app_ready': True
            }
        except Exception as e:
            logger.error(f"Failed to get app info: {e}")
            logger.debug("App info exception:", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'app_ready': False
            }