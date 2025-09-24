# steam_manager.py
#
# A dedicated module for managing the Steam client process.
# This includes checking if Steam is running, terminating it gracefully,
# and launching it with the GreenLuma DLL injector.

import psutil
import time
import subprocess
import configparser
from pathlib import Path
import logging
import vdf
import shutil
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def get_steam_path_from_registry() -> Optional[str]:
    """
    Query the Windows registry to find Steam's installation path.
    
    This function attempts to read the Steam InstallPath from the registry,
    similar to the JavaScript version that uses 'reg query'.
    
    Returns:
        Optional[str]: The Steam installation path if found and valid, None otherwise.
    """
    logger.debug("Attempting to detect Steam path from Windows registry")
    
    try:
        # This command queries the registry for Steam's InstallPath value
        command = 'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Valve\\Steam" /v InstallPath'
        logger.debug(f"Running registry query command: {command}")
        
        # Execute the registry query command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.debug(f"Registry query failed with return code {result.returncode}")
            logger.debug(f"stderr: {result.stderr}")
            return None
            
        stdout = result.stdout
        logger.debug(f"Registry query output: {stdout}")
        
        # The output is messy, so we need to parse it to get just the path
        # Expected format: "    InstallPath    REG_SZ    C:\Program Files (x86)\Steam"
        lines = stdout.split('\n')
        for line in lines:
            if 'InstallPath' in line and 'REG_SZ' in line:
                # Split by whitespace and get the path (last part)
                parts = line.split()
                if len(parts) >= 3:
                    # The path is everything after REG_SZ
                    reg_sz_index = -1
                    for i, part in enumerate(parts):
                        if part == 'REG_SZ':
                            reg_sz_index = i
                            break
                    
                    if reg_sz_index >= 0 and reg_sz_index + 1 < len(parts):
                        # Join all parts after REG_SZ to handle paths with spaces
                        steam_path = ' '.join(parts[reg_sz_index + 1:]).strip()
                        logger.debug(f"Extracted Steam path from registry: {steam_path}")
                        
                        # Verify the path actually exists and contains steam.exe using pathlib
                        steam_path_obj = Path(steam_path)
                        if steam_path_obj.exists():
                            steam_exe_path = steam_path_obj / 'steam.exe'
                            if steam_exe_path.exists():
                                logger.info(f"Registry found valid Steam installation at: {steam_path}")
                                return steam_path
                            else:
                                logger.warning(f"Registry path exists but steam.exe not found: {steam_exe_path}")
                        else:
                            logger.warning(f"Registry path does not exist: {steam_path}")
        
        logger.debug("Could not parse Steam path from registry output")
        return None
        
    except subprocess.TimeoutExpired:
        logger.warning("Registry query timed out")
        return None
    except Exception as e:
        logger.debug(f"Failed to query registry for Steam path: {e}")
        return None


def get_steam_path_with_fallbacks() -> str:
    """
    Get Steam installation path using multiple detection methods with fallbacks.
    
    Detection order:
    1. Windows registry query (most reliable)
    2. Common installation paths (fallbacks)
    
    Returns:
        str: The detected or fallback Steam installation path.
    """
    logger.info("Detecting Steam installation path")
    
    # Method 1: Try registry detection first
    registry_path = get_steam_path_from_registry()
    if registry_path:
        logger.info(f"Steam path detected from registry: {registry_path}")
        return registry_path
    
    # Method 2: Try common fallback paths using pathlib
    logger.debug("Registry detection failed, trying common installation paths")
    fallback_paths = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path.home() / "Steam",  # Some users install Steam in their home directory
    ]
    
    for path in fallback_paths:
        logger.debug(f"Checking fallback path: {path}")
        if path.exists() and path.is_dir():
            steam_exe_path = path / 'steam.exe'
            if steam_exe_path.exists() and steam_exe_path.is_file():
                logger.info(f"Steam found at fallback path: {path}")
                return str(path)
            else:
                logger.debug(f"Path exists but steam.exe not found: {steam_exe_path}")
        else:
            logger.debug(f"Fallback path does not exist: {path}")
    
    # Method 3: Ultimate fallback - return the most common path even if it doesn't exist
    default_path = r"C:\Program Files (x86)\Steam"
    logger.warning(f"Could not detect Steam installation, using default path: {default_path}")
    return default_path


def is_steam_path_valid(steam_path: str) -> bool:
    """
    Validate if a given path is a valid Steam installation using pathlib.
    
    Args:
        steam_path (str): Path to validate as Steam installation.
        
    Returns:
        bool: True if the path contains a valid Steam installation, False otherwise.
    """
    if not steam_path:
        return False
        
    try:
        path = Path(steam_path)
        if not path.exists() or not path.is_dir():
            return False
            
        steam_exe = path / 'steam.exe'
        return steam_exe.exists() and steam_exe.is_file()
        
    except Exception as e:
        logger.debug(f"Error validating Steam path '{steam_path}': {e}")
        return False

def is_steam_running():
    """
    Check if Steam.exe is currently running.
    
    Returns:
        bool: True if Steam is running, False otherwise.
    """
    try:
        logger.debug("Checking if Steam is running")
        steam_found = False
        
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == 'steam.exe':
                steam_found = True
                logger.debug(f"Found Steam process with PID: {process.info['pid']}")
                break
        
        if steam_found:
            logger.info("Steam is currently running")
        else:
            logger.info("Steam is not running")
            
        return steam_found
    except Exception as e:
        logger.error(f"Failed to check Steam status: {e}")
        logger.debug("Steam status check error details:", exc_info=True)
        return False


def terminate_steam():
    """
    Enhanced terminate_steam function with better process handling.
    
    Returns:
        dict: Result dictionary with success status and details.
    """
    logger.info("Starting Steam termination process")
    
    result = {
        'success': False,
        'terminated_processes': 0,
        'errors': []
    }
    
    try:
        steam_processes = []
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == 'steam.exe':
                steam_processes.append(process)
                logger.debug(f"Found Steam process with PID: {process.pid}")
        
        if not steam_processes:
            result['success'] = True
            logger.info("No Steam processes found to terminate")
            return result
        
        logger.info(f"Found {len(steam_processes)} Steam processes to terminate")
        
        # First, try graceful termination
        for process in steam_processes:
            try:
                logger.debug(f"Gracefully terminating Steam process (PID: {process.pid})")
                process.terminate()
                result['terminated_processes'] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Could not terminate process (PID: {process.pid}): {e}")
                continue
            except Exception as e:
                error_msg = f"Failed to terminate Steam process (PID: {process.pid}): {e}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Wait a short time for graceful termination
        logger.debug("Waiting 1 second for graceful termination")
        time.sleep(1)
        
        # Force kill any remaining processes
        remaining_processes = []
        for process in steam_processes:
            try:
                if process.is_running():
                    remaining_processes.append(process)
            except psutil.NoSuchProcess:
                continue
        
        if remaining_processes:
            logger.info(f"Force killing {len(remaining_processes)} remaining Steam processes")
            for process in remaining_processes:
                try:
                    logger.debug(f"Force killing Steam process (PID: {process.pid})")
                    process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    error_msg = f"Failed to force kill Steam process (PID: {process.pid}): {e}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
        
        # Final verification will be done by the polling function
        result['success'] = True
        logger.info(f"Termination commands sent to {result['terminated_processes']} Steam process(es)")
            
    except Exception as e:
        error_msg = f"Unexpected error while terminating Steam: {e}"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        logger.debug("Steam termination error details:", exc_info=True)
    
    return result


def set_steam_offline_mode(config: configparser.ConfigParser, offline_mode: bool = False):
    """
    Set the WantsOfflineMode setting in Steam's loginusers.vdf file.
    
    Args:
        config (configparser.ConfigParser): The loaded application configuration.
        offline_mode (bool): True to enable offline mode, False to disable it.
        
    Returns:
        dict: Result dictionary with success status and details.
    """
    logger.info(f"Setting Steam offline mode to: {offline_mode}")
    
    result = {
        'success': False,
        'errors': []
    }
    
    try:
        # Get Steam path from config
        steam_path = config.get('Paths', 'steam_path', fallback='')
        logger.debug(f"Steam path from config: {steam_path}")
        
        if not steam_path:
            error_msg = "Steam path not configured"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        # Construct path to loginusers.vdf
        steam_dir = Path(steam_path)
        loginusers_path = steam_dir / 'config' / 'loginusers.vdf'
        logger.debug(f"loginusers.vdf path: {loginusers_path}")
        
        if not loginusers_path.exists():
            error_msg = f"loginusers.vdf not found at: {loginusers_path}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        # Read the loginusers.vdf file
        logger.debug("Reading loginusers.vdf")
        with loginusers_path.open('r', encoding='utf-8') as f:
            loginusers_data = vdf.load(f)
        
        # Find and update WantsOfflineMode for all users
        users_section = loginusers_data.get('users', {})
        if not users_section:
            error_msg = "No 'users' section found in loginusers.vdf"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        updated_users = 0
        offline_mode_value = "1" if offline_mode else "0"
        
        for user_id, user_data in users_section.items():
            if isinstance(user_data, dict):
                original_value = user_data.get('WantsOfflineMode', 'not set')
                user_data['WantsOfflineMode'] = offline_mode_value
                updated_users += 1
                logger.debug(f"Updated user {user_id}: WantsOfflineMode {original_value} -> {offline_mode_value}")
        
        if updated_users == 0:
            error_msg = "No user accounts found to update"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        # Create backup before modifying
        backup_path = loginusers_path.with_suffix('.vdf.bak')
        logger.debug(f"Creating backup: {backup_path}")
        shutil.copy2(loginusers_path, backup_path)
        
        # Write the updated loginusers.vdf back to disk
        logger.debug("Writing updated loginusers.vdf")
        with loginusers_path.open('w', encoding='utf-8') as f:
            vdf.dump(loginusers_data, f, pretty=True)
        
        result['success'] = True
        result['updated_users'] = updated_users
        logger.info(f"Successfully updated WantsOfflineMode to {offline_mode_value} for {updated_users} user(s)")
        
    except Exception as e:
        error_msg = f"Failed to set Steam offline mode: {e}"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        logger.debug("Set offline mode error details:", exc_info=True)
    
    return result


def run_steam_with_dll_injector(config: configparser.ConfigParser):
    """
    Run Steam using the DLLInjector.exe from GreenLuma.
    
    Args:
        config (configparser.ConfigParser): The loaded application configuration.
        
    Returns:
        dict: Result dictionary with success status and details.
    """
    logger.info("Starting Steam via DLL injector")
    
    result = {
        'success': False,
        'errors': []
    }
    
    try:
        # Set Steam to online mode (disable offline mode) before launching
        offline_result = set_steam_offline_mode(config, offline_mode=False)
        if not offline_result['success']:
            logger.warning(f"Failed to disable offline mode: {offline_result['errors']}")
            # Continue anyway, as this is not critical for Steam launching
        
        # Get GreenLuma path from config
        greenluma_path = config.get('Paths', 'greenluma_path', fallback='')
        logger.debug(f"GreenLuma path from config: {greenluma_path}")
        
        if not greenluma_path:
            error_msg = "GreenLuma path not configured"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        # Construct path to DLLInjector.exe using pathlib
        greenluma_dir = Path(greenluma_path)
        dll_injector_path = greenluma_dir / 'NormalMode' / 'DLLInjector.exe'
        logger.debug(f"DLL injector path: {dll_injector_path}")
        
        if not dll_injector_path.exists():
            error_msg = f"DLLInjector.exe not found at: {dll_injector_path}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
        
        logger.info(f"Starting Steam via DLLInjector: {dll_injector_path}")
        
        # Start DLLInjector.exe (which will launch Steam with the DLL injected)
        subprocess.Popen([str(dll_injector_path)], cwd=str(dll_injector_path.parent))
        
        result['success'] = True
        logger.info("Steam started successfully via DLLInjector")
        
    except Exception as e:
        error_msg = f"Failed to start Steam via DLLInjector: {e}"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        logger.debug("DLL injector error details:", exc_info=True)
    
    return result