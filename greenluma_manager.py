# greenluma_manager.py
#
# A standalone module for managing GreenLuma integration.
# This module handles AppList management, DLL injector configuration,
# and all GreenLuma-related operations for SuperSexySteam.

import os
import re


# =============================================================================
# --- GREENLUMA APPLIST MANAGEMENT ---
# =============================================================================

def parse_lua_for_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotIDs from addappid calls.
    It looks for any 'addappid(id, ...)' format, regardless of whether
    they have decryption keys or not.

    This function is designed to be resilient, ignoring comment lines and
    extracting all depot IDs for GreenLuma AppList processing.

    Args:
        lua_path (str): The full path to the .lua file to be parsed.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the key 'depot_id'. Returns an empty list if the file
              is not found or an error occurs.
    """
    # This regex is crafted to match any addappid line with a depot ID.
    # - `^\s*addappid\(`: Matches the start of the line and the function name.
    # - `\s*`: Allows optional whitespace after the opening parenthesis.
    # - `(\d+)`: Captures the numeric DepotID (Group 1).
    # - `\s*`: Allows optional whitespace after the depot ID.
    # - `[,\)]`: Matches either a comma (indicating more parameters) or closing parenthesis
    depot_pattern = re.compile(r'^\s*addappid\(\s*(\d+)\s*[,\)]')

    extracted_depots = []
    try:
        with open(lua_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Ignore comment lines to avoid parsing them.
                if line.strip().startswith('--'):
                    continue

                match = depot_pattern.match(line)
                if match:
                    depot_id = match.group(1)
                    extracted_depots.append({
                        'depot_id': depot_id
                    })
    except FileNotFoundError:
        print(f"  [Warning] Could not find file during parsing: {lua_path}")
    except Exception as e:
        print(f"  [Error] Failed to read or parse {os.path.basename(lua_path)}: {e}")

    return extracted_depots


def update_greenluma_applist(gl_path, new_appids, new_depots, verbose=True):
    """
    Adds new AppIDs and their associated DepotIDs to the GreenLuma AppList folder.

    It works by finding the highest numbered existing .txt file and creating
    new files sequentially from that point. First, it writes all the new AppIDs,
    then it writes all the depots associated with those new AppIDs.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        new_appids (list): A list of AppID strings to add.
        new_depots (list): A list of depot dictionaries from the new apps.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Statistics about the operation with keys: 'appids_added', 'depots_added', 'files_created'
    """
    stats = {'appids_added': 0, 'depots_added': 0, 'files_created': 0}
    
    if verbose:
        print(f"\nProcessing GreenLuma AppList: {gl_path}")
    
    applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
    if not os.path.isdir(applist_dir):
        if verbose:
            print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
        try:
            os.makedirs(applist_dir, exist_ok=True)
            if verbose:
                print(f"[Info] Created missing AppList directory: {applist_dir}")
        except Exception as e:
            if verbose:
                print(f"[Error] Could not create AppList directory: {e}")
            return stats

    # Find the next available index for a new file.
    try:
        existing_files = os.listdir(applist_dir)
        indices = [int(os.path.splitext(f)[0]) for f in existing_files 
                  if os.path.splitext(f)[0].isdigit() and f.endswith('.txt')]
        current_index = max(indices) + 1 if indices else 0
        if verbose:
            print(f"  Found {len(indices)} existing entries. Starting new entries from index {current_index}.")
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to scan AppList directory: {e}")
        return stats

    # Write all new AppIDs to sequentially numbered files.
    if new_appids:
        if verbose:
            print(f"  Writing {len(new_appids)} new AppIDs...")
        for app_id in new_appids:
            filepath = os.path.join(applist_dir, f"{current_index}.txt")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(app_id)
                if verbose:
                    print(f"    - Created {os.path.basename(filepath)} with AppID: {app_id}")
                current_index += 1
                stats['appids_added'] += 1
                stats['files_created'] += 1
            except Exception as e:
                if verbose:
                    print(f"[Error] Could not write file {filepath}: {e}")

    # Write all depots from those new apps to sequentially numbered files.
    new_depot_ids = [d['depot_id'] for d in new_depots]
    if new_depot_ids:
        if verbose:
            print(f"  Writing {len(new_depot_ids)} new DepotIDs...")
        for depot_id in new_depot_ids:
            filepath = os.path.join(applist_dir, f"{current_index}.txt")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(depot_id)
                if verbose:
                    print(f"    - Created {os.path.basename(filepath)} with DepotID: {depot_id}")
                current_index += 1
                stats['depots_added'] += 1
                stats['files_created'] += 1
            except Exception as e:
                if verbose:
                    print(f"[Error] Could not write file {filepath}: {e}")

    if verbose:
        print("  Finished updating GreenLuma AppList.")
    
    return stats


def clear_greenluma_applist(gl_path, verbose=True):
    """
    Clears all entries from the GreenLuma AppList folder.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        int: Number of files deleted, or -1 on error.
    """
    if verbose:
        print(f"\nClearing GreenLuma AppList: {gl_path}")
    
    applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
    if not os.path.isdir(applist_dir):
        if verbose:
            print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
        return 0

    deleted_count = 0
    try:
        for filename in os.listdir(applist_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(applist_dir, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    if verbose:
                        print(f"  - Deleted {filename}")
                except Exception as e:
                    if verbose:
                        print(f"[Error] Could not delete {filename}: {e}")
        
        if verbose:
            print(f"  Cleared {deleted_count} AppList entries.")
        
        return deleted_count
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to clear AppList: {e}")
        return -1


def get_greenluma_applist_stats(gl_path, verbose=True):
    """
    Gets statistics about the current GreenLuma AppList.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        verbose (bool): Whether to print information.

    Returns:
        dict: Statistics with keys: 'total_files', 'appids', 'depots', 'other'
    """
    stats = {'total_files': 0, 'appids': 0, 'depots': 0, 'other': 0}
    
    applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
    if not os.path.isdir(applist_dir):
        if verbose:
            print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
        return stats

    try:
        for filename in os.listdir(applist_dir):
            if filename.endswith('.txt'):
                stats['total_files'] += 1
                filepath = os.path.join(applist_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content.isdigit():
                            # Heuristic: shorter numbers are likely AppIDs, longer ones are DepotIDs
                            if len(content) <= 7:  # Typical AppID length
                                stats['appids'] += 1
                            else:  # Likely DepotID
                                stats['depots'] += 1
                        else:
                            stats['other'] += 1
                except Exception:
                    stats['other'] += 1
        
        if verbose:
            print(f"GreenLuma AppList stats: {stats['total_files']} files total")
            print(f"  - Estimated AppIDs: {stats['appids']}")
            print(f"  - Estimated DepotIDs: {stats['depots']}")
            print(f"  - Other entries: {stats['other']}")
        
        return stats
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to get AppList stats: {e}")
        return stats


# =============================================================================
# --- GREENLUMA DLL INJECTOR CONFIGURATION ---
# =============================================================================

def configure_greenluma_injector(steam_path, greenluma_path, verbose=True):
    """
    Configures the DLLInjector.ini file in the GreenLuma NormalMode directory
    with the correct Steam executable path and GreenLuma DLL path.
    
    Args:
        steam_path (str): The path to the Steam installation directory.
        greenluma_path (str): The path to the GreenLuma directory.
        verbose (bool): Whether to print progress information.

    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    if verbose:
        print(f"\nConfiguring GreenLuma DLLInjector.ini...")
    
    # Construct the full path to the DLLInjector.ini file
    injector_ini_path = os.path.join(greenluma_path, 'NormalMode', 'DLLInjector.ini')
    
    if not os.path.exists(injector_ini_path):
        if verbose:
            print(f"[Error] DLLInjector.ini not found at: {injector_ini_path}")
        return False
    
    try:
        # Construct the paths using Windows-style backslashes
        # Point to the specific executable and DLL files
        # Escape backslashes for regex use
        steam_exe_path = (steam_path.replace('/', '\\') + '\\Steam.exe').replace('\\', '\\\\')
        greenluma_dll_path = (greenluma_path.replace('/', '\\') + '\\NormalMode\\GreenLuma_2025_x86.dll').replace('\\', '\\\\')
        
        # Read the current file content as text to preserve formatting and comments
        with open(injector_ini_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the specific lines we need to modify using string replacement
        # Update UseFullPathsFromIni
        content = re.sub(r'^UseFullPathsFromIni\s*=\s*.*$', f'UseFullPathsFromIni = 1', content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Update Exe path - point to Steam executable
        content = re.sub(r'^Exe\s*=\s*.*$', f'Exe = {steam_exe_path}', content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Update Dll path - point to GreenLuma DLL file  
        content = re.sub(r'^Dll\s*=\s*.*$', f'Dll = {greenluma_dll_path}', content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Write the updated content back to the file
        with open(injector_ini_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if verbose:
            print(f"  Successfully configured DLLInjector.ini")
            print(f"  Steam executable: {steam_exe_path}")
            print(f"  GreenLuma DLL: {greenluma_dll_path}")
            print(f"  UseFullPathsFromIni: 1")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to write DLLInjector.ini: {e}")
        return False


def validate_greenluma_installation(greenluma_path, verbose=True):
    """
    Validates that a GreenLuma installation exists and has the expected structure.

    Args:
        greenluma_path (str): The path to the GreenLuma installation.
        verbose (bool): Whether to print validation information.

    Returns:
        dict: Validation results with keys: 'valid', 'missing_components', 'found_components'
    """
    if verbose:
        print(f"Validating GreenLuma installation: {greenluma_path}")
    
    result = {
        'valid': False,
        'missing_components': [],
        'found_components': []
    }
    
    if not os.path.isdir(greenluma_path):
        if verbose:
            print("[Error] GreenLuma path does not exist or is not a directory.")
        result['missing_components'].append('base_directory')
        return result
    
    # Check for required components
    required_components = {
        'NormalMode': os.path.join(greenluma_path, 'NormalMode'),
        'DLLInjector.exe': os.path.join(greenluma_path, 'NormalMode', 'DLLInjector.exe'),
        'DLLInjector.ini': os.path.join(greenluma_path, 'NormalMode', 'DLLInjector.ini'),
        'GreenLuma_DLL_x86': os.path.join(greenluma_path, 'NormalMode', 'GreenLuma_2025_x86.dll'),
        'GreenLuma_DLL_x64': os.path.join(greenluma_path, 'NormalMode', 'GreenLuma_2025_x64.dll'),
        'AppList': os.path.join(greenluma_path, 'NormalMode', 'AppList')
    }
    
    for component_name, component_path in required_components.items():
        if os.path.exists(component_path):
            result['found_components'].append(component_name)
            if verbose:
                print(f"  ✓ Found {component_name}")
        else:
            result['missing_components'].append(component_name)
            if verbose:
                print(f"  ✗ Missing {component_name}")
    
    # Create AppList directory if it's missing but other components exist
    if 'AppList' in result['missing_components'] and len(result['found_components']) > 2:
        try:
            applist_path = required_components['AppList']
            os.makedirs(applist_path, exist_ok=True)
            result['missing_components'].remove('AppList')
            result['found_components'].append('AppList')
            if verbose:
                print(f"  ✓ Created missing AppList directory")
        except Exception as e:
            if verbose:
                print(f"  ✗ Failed to create AppList directory: {e}")
    
    # Consider installation valid if most core components are present
    core_components = ['NormalMode', 'DLLInjector.exe', 'DLLInjector.ini']
    core_found = sum(1 for comp in core_components if comp in result['found_components'])
    result['valid'] = core_found >= len(core_components)
    
    if verbose:
        if result['valid']:
            print("[Success] GreenLuma installation appears to be valid.")
        else:
            print("[Error] GreenLuma installation is incomplete or invalid.")
    
    return result


# =============================================================================
# --- GREENLUMA INTEGRATION ORCHESTRATOR ---
# =============================================================================

def process_appids_for_greenluma(greenluma_path, new_appids, data_dir='data', verbose=True):
    """
    Complete orchestrator function that processes AppIDs for GreenLuma integration.
    
    Args:
        greenluma_path (str): Path to GreenLuma installation.
        new_appids (list): List of new AppID strings to process.
        data_dir (str): Directory containing the lua files. Defaults to 'data'.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Results with keys: 'success', 'stats', 'errors'
    """
    result = {
        'success': False,
        'stats': {'appids_added': 0, 'depots_added': 0, 'files_created': 0},
        'errors': []
    }
    
    if verbose:
        print(f"\n=== Processing {len(new_appids)} AppIDs for GreenLuma ===")
    
    # Validate GreenLuma installation
    validation = validate_greenluma_installation(greenluma_path, verbose=False)
    if not validation['valid']:
        error_msg = f"Invalid GreenLuma installation: {', '.join(validation['missing_components'])}"
        result['errors'].append(error_msg)
        if verbose:
            print(f"[Error] {error_msg}")
        return result
    
    # Parse depot data from new AppIDs
    all_new_depots = []
    processed_appids = []
    
    for app_id in new_appids:
        lua_path = os.path.join(data_dir, app_id, f"{app_id}.lua")
        if os.path.exists(lua_path):
            depots = parse_lua_for_depots(lua_path)
            all_new_depots.extend(depots)
            processed_appids.append(app_id)
            if verbose:
                print(f"  Processed AppID {app_id}: found {len(depots)} depots")
        else:
            error_msg = f"Lua file not found for AppID {app_id}: {lua_path}"
            result['errors'].append(error_msg)
            if verbose:
                print(f"  [Warning] {error_msg}")
    
    if not processed_appids:
        error_msg = "No valid AppIDs could be processed"
        result['errors'].append(error_msg)
        if verbose:
            print(f"[Error] {error_msg}")
        return result
    
    # Update GreenLuma AppList
    try:
        stats = update_greenluma_applist(greenluma_path, processed_appids, all_new_depots, verbose)
        result['stats'] = stats
        result['success'] = True
        
        if verbose:
            print(f"\n=== GreenLuma Processing Complete ===")
            print(f"AppIDs added: {stats['appids_added']}")
            print(f"Depots added: {stats['depots_added']}")
            print(f"Total files created: {stats['files_created']}")
        
    except Exception as e:
        error_msg = f"Failed to update GreenLuma AppList: {e}"
        result['errors'].append(error_msg)
        if verbose:
            print(f"[Error] {error_msg}")
    
    return result


def process_single_appid_for_greenluma(gl_path, app_id, depots, verbose=True):
    """
    Add a single AppID and its depots to the GreenLuma AppList.
    
    Args:
        gl_path (str): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to add
        depots (list): List of depot dictionaries for this AppID
        verbose (bool): Whether to print progress information
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    result = {
        'success': False,
        'errors': [],
        'stats': {'appids_added': 0, 'depots_added': 0, 'files_created': 0}
    }
    
    try:
        if verbose:
            print(f"\nAdding AppID {app_id} to GreenLuma AppList: {gl_path}")
        
        applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
        if not os.path.isdir(applist_dir):
            try:
                os.makedirs(applist_dir, exist_ok=True)
                if verbose:
                    print(f"[Info] Created missing AppList directory: {applist_dir}")
            except Exception as e:
                result['errors'].append(f"Could not create AppList directory: {e}")
                return result
        
        # Find the next available index
        try:
            existing_files = os.listdir(applist_dir)
            indices = [int(os.path.splitext(f)[0]) for f in existing_files 
                      if f.endswith('.txt') and os.path.splitext(f)[0].isdigit()]
            next_index = max(indices) + 1 if indices else 0
        except Exception as e:
            result['errors'].append(f"Could not determine next file index: {e}")
            return result
        
        # Write AppID
        appid_filename = f"{next_index}.txt"
        appid_filepath = os.path.join(applist_dir, appid_filename)
        try:
            with open(appid_filepath, 'w', encoding='utf-8') as f:
                f.write(f"{app_id}\n")
            result['stats']['appids_added'] = 1
            result['stats']['files_created'] += 1
            if verbose:
                print(f"  - Created {appid_filename} with AppID {app_id}")
        except Exception as e:
            result['errors'].append(f"Failed to write AppID file: {e}")
            return result
        
        # Write depots
        for depot in depots:
            next_index += 1
            depot_filename = f"{next_index}.txt"
            depot_filepath = os.path.join(applist_dir, depot_filename)
            try:
                with open(depot_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{depot['depot_id']}\n")
                result['stats']['depots_added'] += 1
                result['stats']['files_created'] += 1
                if verbose:
                    print(f"  - Created {depot_filename} with DepotID {depot['depot_id']}")
            except Exception as e:
                result['errors'].append(f"Failed to write depot file for {depot['depot_id']}: {e}")
                # Continue with other depots even if one fails
        
        result['success'] = True
        if verbose:
            stats = result['stats']
            print(f"  Successfully added AppID {app_id} with {stats['depots_added']} depots ({stats['files_created']} files created)")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result


def remove_appid_from_greenluma(gl_path, app_id, depots, verbose=True):
    """
    Remove a specific AppID and its depots from the GreenLuma AppList.
    
    Args:
        gl_path (str): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to remove
        depots (list): List of depot dictionaries for this AppID
        verbose (bool): Whether to print progress information
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    result = {
        'success': False,
        'errors': [],
        'stats': {'appids_removed': 0, 'depots_removed': 0, 'files_removed': 0}
    }
    
    try:
        if verbose:
            print(f"\nRemoving AppID {app_id} from GreenLuma AppList: {gl_path}")
        
        applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
        if not os.path.isdir(applist_dir):
            if verbose:
                print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
            result['success'] = True  # Nothing to remove is considered success
            return result
        
        # Collect all IDs to remove (AppID + all depot IDs)
        ids_to_remove = {app_id}
        for depot in depots:
            ids_to_remove.add(depot['depot_id'])
        
        # Read all existing files and identify which ones to remove
        files_to_remove = []
        remaining_files = []
        
        try:
            existing_files = os.listdir(applist_dir)
            txt_files = [f for f in existing_files if f.endswith('.txt')]
            
            for filename in txt_files:
                filepath = os.path.join(applist_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content in ids_to_remove:
                        files_to_remove.append((filename, filepath, content))
                        if content == app_id:
                            result['stats']['appids_removed'] += 1
                        else:
                            result['stats']['depots_removed'] += 1
                    else:
                        remaining_files.append((filename, filepath, content))
                        
                except Exception as e:
                    if verbose:
                        print(f"[Warning] Could not read file {filename}: {e}")
                    # Keep files we can't read
                    remaining_files.append((filename, filepath, ""))
        
        except Exception as e:
            result['errors'].append(f"Failed to scan AppList directory: {e}")
            return result
        
        # Remove the identified files
        for filename, filepath, content in files_to_remove:
            try:
                os.remove(filepath)
                result['stats']['files_removed'] += 1
                if verbose:
                    print(f"  - Removed {filename} (contained {content})")
            except Exception as e:
                result['errors'].append(f"Failed to remove file {filename}: {e}")
        
        # Renumber remaining files to maintain sequential order (0, 1, 2, 3...)
        if remaining_files:
            # Sort by original index to maintain order
            remaining_files.sort(key=lambda x: int(os.path.splitext(x[0])[0]) if os.path.splitext(x[0])[0].isdigit() else 999999)
            
            # Rename files to sequential indices
            for i, (old_filename, old_filepath, content) in enumerate(remaining_files):
                new_filename = f"{i}.txt"
                new_filepath = os.path.join(applist_dir, new_filename)
                
                if old_filename != new_filename:
                    try:
                        # Create new file with correct name
                        with open(new_filepath, 'w', encoding='utf-8') as f:
                            f.write(f"{content}\n")
                        
                        # Remove old file if it's different
                        if old_filepath != new_filepath:
                            os.remove(old_filepath)
                        
                        if verbose:
                            print(f"  - Renumbered {old_filename} -> {new_filename}")
                            
                    except Exception as e:
                        result['errors'].append(f"Failed to renumber {old_filename} to {new_filename}: {e}")
        
        result['success'] = True
        if verbose:
            stats = result['stats']
            print(f"  Successfully removed AppID {app_id}: {stats['appids_removed']} AppIDs, {stats['depots_removed']} depots ({stats['files_removed']} files removed)")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result


# =============================================================================
# --- MAIN EXECUTION FOR STANDALONE USE ---
# =============================================================================

def main():
    """
    Main function for standalone execution.
    Provides command line interface for GreenLuma management.
    """
    import sys
    
    print("--- greenluma_manager.py: GreenLuma Integration Management ---")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python greenluma_manager.py <greenluma_path> [command] [options]")
        print("Commands:")
        print("  validate              - Validate GreenLuma installation")
        print("  stats                 - Show AppList statistics")
        print("  clear                 - Clear all AppList entries")
        print("  configure <steam_path> - Configure DLL injector")
        print("Examples:")
        print("  python greenluma_manager.py \"C:\\GreenLuma\" validate")
        print("  python greenluma_manager.py \"C:\\GreenLuma\" configure \"C:\\Steam\"")
        return
    
    greenluma_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'validate'
    
    if command == 'validate':
        validate_greenluma_installation(greenluma_path)
    
    elif command == 'stats':
        get_greenluma_applist_stats(greenluma_path)
    
    elif command == 'clear':
        count = clear_greenluma_applist(greenluma_path)
        if count >= 0:
            print(f"[Success] Cleared {count} AppList entries.")
    
    elif command == 'configure':
        if len(sys.argv) < 4:
            print("[Error] Steam path required for configure command.")
            print("Usage: python greenluma_manager.py <greenluma_path> configure <steam_path>")
            return
        
        steam_path = sys.argv[3]
        success = configure_greenluma_injector(steam_path, greenluma_path)
        if success:
            print("[Success] DLL injector configured successfully.")
        else:
            print("[Error] Failed to configure DLL injector.")
    
    else:
        print(f"[Error] Unknown command: {command}")


if __name__ == "__main__":
    """
    Standard script entry point for standalone execution.
    """
    main()
