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
from pathlib import Path
import shutil
import time
from typing import Dict, List, Any, Optional, Tuple

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
        self.config = config
        self.db = get_database_manager()
        self.game_installer = GameInstaller(config)
        
        # Initialize by terminating Steam if running
        self._terminate_steam_on_startup()
        
        # Update missing game names for existing databases (migration)
        self._perform_database_migration()
    
    def _terminate_steam_on_startup(self) -> None:
        """Terminate Steam processes during application startup."""
        print("[INFO] Checking for running Steam processes...")
        if is_steam_running():
            print("[INFO] Steam is running, terminating...")
            try:
                result = terminate_steam()
                if result['success']:
                    if result['terminated_processes'] > 0:
                        print(f"[INFO] Terminated {result['terminated_processes']} Steam process(es) at startup")
                    else:
                        print("[INFO] No Steam processes to terminate at startup")
                else:
                    print(f"[WARNING] Failed to terminate Steam at startup: {'; '.join(result['errors'])}")
            except Exception as e:
                print(f"[ERROR] Error terminating Steam at startup: {e}")
        else:
            print("[INFO] Steam is not running")
    
    def _perform_database_migration(self) -> None:
        """Perform database migration to update missing game names."""
        try:
            updated_count = self.db.update_missing_game_names()
            if updated_count > 0:
                print(f"[INFO] Updated {updated_count} game names during database migration")
        except Exception as e:
            print(f"[WARNING] Failed to update missing game names: {e}")
    
    # =============================================================================
    # --- DATABASE OPERATIONS ---
    # =============================================================================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dict containing database statistics with success flag
        """
        try:
            stats = self.db.get_database_stats()
            return {
                'success': True,
                'stats': stats,
                'formatted_text': f"Games: {stats['installed_appids']} installed | Depots: {stats['total_depots']} | With Keys: {stats['depots_with_keys']}"
            }
        except Exception as e:
            print(f"[ERROR] Failed to get database stats: {e}")
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
        try:
            games = self.db.get_installed_games()
            return {
                'success': True,
                'games': games,
                'count': len(games)
            }
        except Exception as e:
            print(f"[ERROR] Failed to get installed games: {e}")
            return {
                'success': False,
                'error': str(e),
                'games': [],
                'count': 0
            }
    
    # =============================================================================
    # --- STEAM PROCESS MANAGEMENT ---
    # =============================================================================
    
    def check_steam_status(self) -> Dict[str, Any]:
        """
        Check if Steam is currently running.
        
        Returns:
            Dict with Steam status information
        """
        try:
            running = is_steam_running()
            return {
                'success': True,
                'is_running': running,
                'message': "Steam is running" if running else "Steam is not running"
            }
        except Exception as e:
            print(f"[ERROR] Failed to check Steam status: {e}")
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
        try:
            result = terminate_steam()
            if result['success']:
                message = f"Terminated {result['terminated_processes']} Steam process(es)" if result['terminated_processes'] > 0 else "No Steam processes to terminate"
                return {
                    'success': True,
                    'terminated_processes': result['terminated_processes'],
                    'message': message
                }
            else:
                error_msg = '; '.join(result['errors'])
                return {
                    'success': False,
                    'error': error_msg,
                    'message': f"Failed to terminate Steam: {error_msg}"
                }
        except Exception as e:
            print(f"[ERROR] Failed to terminate Steam: {e}")
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
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            if not is_steam_running():
                return {
                    'success': True,
                    'terminated': True,
                    'elapsed_time': int(time.time() - start_time),
                    'message': "Steam fully terminated"
                }
            
            time.sleep(check_interval)
        
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
        results = {
            'success': False,
            'messages': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Step 1: Check if Steam is running
            if is_steam_running():
                results['messages'].append("Steam is running. Terminating existing processes...")
                
                # Step 2: Terminate Steam
                terminate_result = self.terminate_steam_processes()
                if terminate_result['success']:
                    results['messages'].append(terminate_result['message'])
                else:
                    results['errors'].append(terminate_result['message'])
                    return results
                
                # Step 3: Wait for processes to terminate
                results['messages'].append("Waiting for Steam to fully terminate...")
                wait_result = self.wait_for_steam_termination()
                if wait_result['terminated']:
                    results['messages'].append(wait_result['message'])
                else:
                    results['warnings'].append(wait_result['message'])
            
            # Step 4: Launch Steam via DLLInjector
            results['messages'].append("Launching Steam via DLLInjector...")
            launch_result = run_steam_with_dll_injector(self.config)
            
            if launch_result['success']:
                results['success'] = True
                results['messages'].append("Steam launched successfully! 🚀")
            else:
                error_msg = '; '.join(launch_result['errors'])
                results['errors'].append(f"Failed to launch Steam: {error_msg}")
                
        except Exception as e:
            results['errors'].append(f"Error launching Steam: {e}")
            print(f"[ERROR] Failed to launch Steam: {e}")
        
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
        # Find .lua files
        lua_files = [p for p in file_paths if p.lower().endswith('.lua')]
        
        if len(lua_files) != 1:
            return {
                'success': False,
                'error': f"Error: {len(lua_files) if len(lua_files) > 1 else 'No'} .lua file{'s' if len(lua_files) > 1 else ''} dropped. Please drop exactly one.",
                'app_id': None,
                'lua_path': None
            }
        
        # Extract AppID from filename
        lua_path = Path(lua_files[0])
        app_id = lua_path.stem
        
        if not app_id.isdigit():
            return {
                'success': False,
                'error': f"Invalid Lua filename: '{lua_path.name}'. Name must be a numeric AppID.",
                'app_id': None,
                'lua_path': str(lua_path)
            }
        
        return {
            'success': True,
            'app_id': app_id,
            'lua_path': str(lua_path),
            'all_files': file_paths,
            'valid_files': [p for p in file_paths if Path(p).suffix.lower() in ('.lua', '.manifest')]
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
        try:
            script_directory = Path(__file__).parent
            destination_directory = script_directory / "data" / app_id
            destination_directory.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            errors = []
            
            for path_str in file_paths:
                path = Path(path_str)
                if path.suffix.lower() in ('.lua', '.manifest'):
                    try:
                        dest_path = destination_directory / path.name
                        shutil.copy2(path, dest_path)
                        copied_files.append(str(dest_path))
                    except Exception as e:
                        error_msg = f"Error copying '{path.name}': {e}"
                        errors.append(error_msg)
            
            if errors:
                # Clean up on any failure
                shutil.rmtree(destination_directory, ignore_errors=True)
                return {
                    'success': False,
                    'errors': errors,
                    'destination_directory': str(destination_directory)
                }
            
            return {
                'success': True,
                'destination_directory': str(destination_directory),
                'copied_files': copied_files,
                'files_copied': len(copied_files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Failed to organize files: {e}"],
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
        # Step 1: Validate files
        validation_result = self.validate_dropped_files(file_paths)
        if not validation_result['success']:
            return {
                'success': False,
                'error': validation_result['error'],
                'stage': 'validation'
            }
        
        app_id = validation_result['app_id']
        
        # Step 2: Check if this is an update
        is_update = self.db.is_appid_exists(app_id)
        
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
                result['stages_completed'].append('update_detection')
                uninstall_result = self.game_installer.uninstall_game(app_id)
                if uninstall_result['success']:
                    result['stages_completed'].append('old_version_removed')
                    print(f"[INFO] Successfully uninstalled existing AppID {app_id} for update.")
                else:
                    # Allow continuing but show warnings
                    result['warnings'].extend(uninstall_result['errors'])
                    print(f"[WARNING] Uninstall errors for AppID {app_id}: {uninstall_result['errors']}")
            
            # Step 4: Organize files
            organize_result = self.organize_game_files(app_id, validation_result['valid_files'])
            if not organize_result['success']:
                result['errors'].extend(organize_result['errors'])
                return result
            
            result['stages_completed'].append('files_organized')
            destination_directory = organize_result['destination_directory']
            
            # Step 5: Install the game
            install_result = self.game_installer.install_game(app_id, destination_directory)
            
            if install_result['success']:
                result['success'] = True
                result['stages_completed'].append('game_installed')
                result['stats'] = install_result['stats']
                result['action_verb'] = "Updated" if is_update else "Installed"
                
                # Add any warnings from installation
                if install_result['warnings']:
                    result['warnings'].extend(install_result['warnings'])
                
                return result
            else:
                # Installation failed, clean up
                result['errors'].extend(install_result['errors'])
                result['stages_completed'].append('installation_failed')
                
                # Clean up the data folder
                if Path(destination_directory).exists():
                    shutil.rmtree(destination_directory, ignore_errors=True)
                
                return result
                
        except Exception as e:
            result['errors'].append(f"Unexpected error during installation: {e}")
            print(f"[ERROR] Installation error for AppID {app_id}: {e}")
            
            # Clean up if destination directory was created
            if 'destination_directory' in locals() and Path(destination_directory).exists():
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
        # Validate AppID
        if not app_id or not app_id.strip():
            return {
                'success': False,
                'error': "AppID cannot be empty",
                'app_id': app_id
            }
        
        app_id = app_id.strip()
        
        if not app_id.isdigit():
            return {
                'success': False,
                'error': f"Invalid AppID: '{app_id}'. Must be numeric.",
                'app_id': app_id
            }
        
        try:
            result = uninstall_specific_appid(self.config, app_id, verbose=True)
            
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
                
                return {
                    'success': True,
                    'app_id': app_id,
                    'stats': stats,
                    'summary': summary,
                    'warnings': result.get('warnings', [])
                }
            else:
                error_msg = '; '.join(result['errors'])
                return {
                    'success': False,
                    'app_id': app_id,
                    'error': error_msg,
                    'errors': result['errors']
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to uninstall AppID {app_id}: {e}")
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
        try:
            result = clear_all_data(self.config, verbose=True)
            
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
                
                return {
                    'success': True,
                    'stats': stats,
                    'summary': summary,
                    'warnings': result.get('warnings', [])
                }
            else:
                error_msg = '; '.join(result['errors'])
                return {
                    'success': False,
                    'error': error_msg,
                    'errors': result['errors']
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to clear application data: {e}")
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
        if not query or not query.strip():
            return {
                'success': False,
                'error': "Search query cannot be empty",
                'games': [],
                'count': 0
            }
        
        try:
            games = search_games(query.strip(), max_results=max_results)
            
            return {
                'success': True,
                'games': games,
                'count': len(games),
                'query': query.strip()
            }
            
        except Exception as e:
            print(f"[ERROR] Steam game search failed: {e}")
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
    def setup_initial_configuration() -> Optional[configparser.ConfigParser]:
        """
        Handle first-time setup configuration.
        
        Returns:
            ConfigParser object if setup successful, None if cancelled
        """
        from SuperSexySteam import PathEntryDialog
        import customtkinter as ctk
        import sys
        
        setup_root = ctk.CTk()
        setup_root.withdraw()
        
        print("[INFO] config.ini not found. Starting first-time setup.")
        
        # Steam path setup
        steam_dialog = PathEntryDialog(
            setup_root, 
            "Steam Path Setup", 
            "Please enter your Steam installation directory.", 
            "Leave empty for C:\\Program Files (x86)\\Steam"
        )
        steam_path = steam_dialog.get_input()
        if steam_path is None:
            setup_root.destroy()
            return None
        if steam_path == "":
            steam_path = "C:\\Program Files (x86)\\Steam"
        
        # GreenLuma path setup
        gl_dialog = PathEntryDialog(
            setup_root, 
            "GreenLuma Path Setup", 
            "Please enter your GreenLuma directory.", 
            "Leave empty for default (script's folder)"
        )
        gl_path = gl_dialog.get_input()
        if gl_path is None:
            setup_root.destroy()
            return None
        if gl_path == "":
            base_dir = Path(__file__).parent
            gl_path = base_dir / "GreenLuma"
            gl_path.mkdir(exist_ok=True)
        
        # Create and save configuration
        config = configparser.ConfigParser()
        config['Paths'] = {
            'steam_path': steam_path, 
            'greenluma_path': str(gl_path)
        }
        
        config_file = Path('config.ini')
        with config_file.open('w') as f:
            config.write(f)
        
        # Configure the GreenLuma DLLInjector.ini with the paths
        configure_greenluma_injector(steam_path, str(gl_path))
        
        setup_root.destroy()
        return config
    
    @staticmethod
    def load_configuration() -> Optional[configparser.ConfigParser]:
        """
        Load existing configuration or run setup if needed.
        
        Returns:
            ConfigParser object if successful, None if setup cancelled
        """
        config_file = Path('config.ini')
        config = configparser.ConfigParser()
        
        if not config_file.exists():
            return SuperSexySteamLogic.setup_initial_configuration()
        else:
            config.read(config_file)
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
        try:
            steam_status = self.check_steam_status()
            db_stats = self.get_database_stats()
            
            return {
                'success': True,
                'steam_status': steam_status,
                'database_stats': db_stats,
                'app_ready': True
            }
        except Exception as e:
            print(f"[ERROR] Failed to get app info: {e}")
            return {
                'success': False,
                'error': str(e),
                'app_ready': False
            }