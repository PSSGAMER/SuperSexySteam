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

def is_steam_running():
    """
    Check if Steam.exe is currently running.
    
    Returns:
        bool: True if Steam is running, False otherwise.
    """
    try:
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'].lower() == 'steam.exe':
                return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to check Steam status: {e}")
        return False


def terminate_steam():
    """
    Enhanced terminate_steam function with better process handling.
    
    Returns:
        dict: Result dictionary with success status and details.
    """
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
        
        if not steam_processes:
            result['success'] = True
            print("[INFO] No Steam processes found to terminate")
            return result
        
        # First, try graceful termination
        for process in steam_processes:
            try:
                print(f"[INFO] Gracefully terminating Steam process (PID: {process.pid})")
                process.terminate()
                result['terminated_processes'] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[WARNING] Could not terminate process (PID: {process.pid}): {e}")
                continue
            except Exception as e:
                result['errors'].append(f"Failed to terminate Steam process (PID: {process.pid}): {e}")
        
        # Wait a short time for graceful termination
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
            print(f"[INFO] Force killing {len(remaining_processes)} remaining Steam processes")
            for process in remaining_processes:
                try:
                    print(f"[INFO] Force killing Steam process (PID: {process.pid})")
                    process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    result['errors'].append(f"Failed to force kill Steam process (PID: {process.pid}): {e}")
        
        # Final verification will be done by the polling function
        result['success'] = True
        print(f"[INFO] Termination commands sent to {result['terminated_processes']} Steam process(es)")
            
    except Exception as e:
        result['errors'].append(f"Unexpected error while terminating Steam: {e}")
        print(f"[ERROR] Failed to terminate Steam: {e}")
    
    return result


def run_steam_with_dll_injector(config: configparser.ConfigParser):
    """
    Run Steam using the DLLInjector.exe from GreenLuma.
    
    Args:
        config (configparser.ConfigParser): The loaded application configuration.
        
    Returns:
        dict: Result dictionary with success status and details.
    """
    result = {
        'success': False,
        'errors': []
    }
    
    try:
        # Get GreenLuma path from config
        greenluma_path = config.get('Paths', 'greenluma_path', fallback='')
        if not greenluma_path:
            result['errors'].append("GreenLuma path not configured")
            return result
        
        # Construct path to DLLInjector.exe using pathlib
        greenluma_dir = Path(greenluma_path)
        dll_injector_path = greenluma_dir / 'NormalMode' / 'DLLInjector.exe'
        
        if not dll_injector_path.exists():
            result['errors'].append(f"DLLInjector.exe not found at: {dll_injector_path}")
            return result
        
        print(f"[INFO] Starting Steam via DLLInjector: {dll_injector_path}")
        
        # Start DLLInjector.exe (which will launch Steam with the DLL injected)
        subprocess.Popen([str(dll_injector_path)], cwd=str(dll_injector_path.parent))
        
        result['success'] = True
        print("[INFO] Steam started successfully via DLLInjector")
        
    except Exception as e:
        result['errors'].append(f"Failed to start Steam via DLLInjector: {e}")
        print(f"[ERROR] Failed to start Steam: {e}")
    
    return result