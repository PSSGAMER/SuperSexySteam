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

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

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