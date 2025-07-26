# greenluma_manager.py
#
# A standalone module for managing GreenLuma integration.
# This module handles AppList management, DLL injector configuration,
# and all GreenLuma-related operations for SuperSexySteam.

import os
import configparser


# =============================================================================
# --- GREENLUMA APPLIST MANAGEMENT ---
# =============================================================================

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
    Gets statistics about the current GreenLuma AppList using database information
    to accurately categorize AppIDs vs DepotIDs.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        verbose (bool): Whether to print information.

    Returns:
        dict: Statistics with keys: 'total_files', 'appids', 'depots', 'other'
    """
    from database_manager import get_database_manager
    
    stats = {'total_files': 0, 'appids': 0, 'depots': 0, 'other': 0}
    
    applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
    if not os.path.isdir(applist_dir):
        if verbose:
            print(f"[Info] GreenLuma AppList directory not found or empty: {applist_dir}")
            print(f"[Info] This is normal for a fresh installation or test environment")
        return stats

    try:
        # Get database information for accurate categorization
        db = get_database_manager()
        installed_appids = set(db.get_all_installed_appids())
        all_depots = db.get_all_depots_for_installed_apps()
        depot_ids = set(depot['depot_id'] for depot in all_depots)
        
        all_files = os.listdir(applist_dir)
        txt_files = [f for f in all_files if f.endswith('.txt')]
        stats['total_files'] = len(txt_files)
        
        if not txt_files:
            if verbose:
                print(f"[Info] No AppList files found in {applist_dir}")
                print(f"[Info] This is expected for a new installation or test environment")
            return stats
        
        for filename in txt_files:
            filepath = os.path.join(applist_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.isdigit():
                        # Use database to accurately categorize IDs
                        if content in installed_appids:
                            stats['appids'] += 1
                        elif content in depot_ids:
                            stats['depots'] += 1
                        else:
                            # ID not found in database - could be legacy or external
                            stats['other'] += 1
                    else:
                        stats['other'] += 1
            except Exception:
                stats['other'] += 1
        
        if verbose:
            if stats['total_files'] > 0:
                print(f"GreenLuma AppList stats: {stats['total_files']} files total")
                print(f"  - AppIDs: {stats['appids']}")
                print(f"  - DepotIDs: {stats['depots']}")
                print(f"  - Other/Unknown entries: {stats['other']}")
            else:
                print(f"[Info] GreenLuma AppList directory exists but contains no .txt files")
        
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
    with the correct Steam executable path and GreenLuma DLL path using configparser.
    
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
        # Initialize the config parser. 
        # allow_no_value=True helps handle INI files that might have keys without values.
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(injector_ini_path)
        
        # Ensure the [DLLInjector] section exists
        if 'DLLInjector' not in config:
            config.add_section('DLLInjector')

        # Construct the full paths required for the INI file
        steam_exe_path = os.path.join(steam_path, 'Steam.exe')
        greenluma_dll_path = os.path.join(greenluma_path, 'NormalMode', 'GreenLuma_2025_x86.dll')
        
        # Set the values in the [DLLInjector] section
        config.set('DLLInjector', 'UseFullPathsFromIni', '1')
        config.set('DLLInjector', 'Exe', steam_exe_path)
        config.set('DLLInjector', 'Dll', greenluma_dll_path)

        # Write the updated configuration back to the file
        with open(injector_ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
            
        if verbose:
            print(f"  Successfully configured DLLInjector.ini")
            print(f"  Steam executable: {steam_exe_path}")
            print(f"  GreenLuma DLL: {greenluma_dll_path}")
            print(f"  UseFullPathsFromIni: 1")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to write DLLInjector.ini using configparser: {e}")
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

def process_single_appid_for_greenluma(gl_path, app_id, depots, verbose=True):
    """
    Add a single AppID and its depots to the GreenLuma AppList.
    Automatically removes duplicates before adding new entries to maintain a clean AppList.
    
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
        'warnings': [],
        'stats': {
            'appids_added': 0, 
            'depots_added': 0, 
            'files_created': 0, 
            'skipped_duplicates': 0,
            'duplicates_cleaned': 0
        }
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
        
        # Step 1: Automatically clean up any existing duplicates
        if verbose:
            print(f"  Checking for existing duplicates...")
        
        duplicate_check = check_for_duplicate_ids_in_applist(gl_path, verbose=False)
        if duplicate_check['has_duplicates']:
            if verbose:
                print(f"  Found {duplicate_check['duplicate_count']} duplicate files, cleaning up...")
            
            cleanup_result = remove_duplicate_ids_from_applist(gl_path, verbose=False)
            if cleanup_result['success']:
                result['stats']['duplicates_cleaned'] = cleanup_result['stats']['duplicates_removed']
                if verbose and cleanup_result['stats']['duplicates_removed'] > 0:
                    print(f"  Removed {cleanup_result['stats']['duplicates_removed']} duplicate files")
            else:
                result['warnings'].extend(cleanup_result.get('errors', []))
        
        # Step 2: Scan existing files to check for duplicates of what we're about to add
        existing_ids = set()
        try:
            existing_files = os.listdir(applist_dir)
            indices = []
            
            for filename in existing_files:
                if filename.endswith('.txt'):
                    filepath = os.path.join(applist_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content.isdigit():
                            existing_ids.add(content)
                        
                        # Track indices for next available index calculation
                        file_index = os.path.splitext(filename)[0]
                        if file_index.isdigit():
                            indices.append(int(file_index))
                    except Exception:
                        # Skip files we can't read
                        pass
            
            next_index = max(indices) + 1 if indices else 0
        except Exception as e:
            result['errors'].append(f"Could not scan existing files: {e}")
            return result
        
        # Step 3: Add AppID if it doesn't already exist
        if app_id in existing_ids:
            if verbose:
                print(f"  - AppID {app_id} already exists in AppList, skipping")
            result['warnings'].append(f"AppID {app_id} already exists")
            result['stats']['skipped_duplicates'] += 1
        else:
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
                next_index += 1
            except Exception as e:
                result['errors'].append(f"Failed to write AppID file: {e}")
                return result
        
        # Step 4: Add depots (only if they don't already exist)
        for depot in depots:
            depot_id = depot['depot_id']
            if depot_id in existing_ids:
                if verbose:
                    print(f"  - DepotID {depot_id} already exists in AppList, skipping")
                result['stats']['skipped_duplicates'] += 1
                continue
                
            depot_filename = f"{next_index}.txt"
            depot_filepath = os.path.join(applist_dir, depot_filename)
            try:
                with open(depot_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{depot_id}\n")
                result['stats']['depots_added'] += 1
                result['stats']['files_created'] += 1
                if verbose:
                    print(f"  - Created {depot_filename} with DepotID {depot_id}")
                next_index += 1
            except Exception as e:
                result['errors'].append(f"Failed to write depot file for {depot_id}: {e}")
                # Continue with other depots even if one fails
        
        result['success'] = True
        if verbose:
            stats = result['stats']
            cleanup_msg = f", cleaned {stats['duplicates_cleaned']} duplicates" if stats['duplicates_cleaned'] > 0 else ""
            print(f"  Successfully processed AppID {app_id}: {stats['appids_added']} AppIDs + {stats['depots_added']} depots added, {stats['skipped_duplicates']} duplicates skipped ({stats['files_created']} files created{cleanup_msg})")
        
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
# --- GREENLUMA DUPLICATE MANAGEMENT ---
# =============================================================================

def remove_duplicate_ids_from_applist(gl_path, verbose=True):
    """
    Detects and removes duplicate IDs from the GreenLuma AppList folder.
    Keeps the first occurrence of each ID and removes subsequent duplicates,
    then renumbers all files sequentially.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Result with success status, errors, statistics, and duplicate details
    """
    result = {
        'success': False,
        'errors': [],
        'stats': {
            'total_files_scanned': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'files_after_cleanup': 0
        },
        'duplicates': {}  # {id: [list of filenames that contained this id]}
    }
    
    try:
        if verbose:
            print(f"\nScanning GreenLuma AppList for duplicates: {gl_path}")
        
        applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
        if not os.path.isdir(applist_dir):
            if verbose:
                print(f"[Info] GreenLuma AppList directory not found: {applist_dir}")
                print(f"[Info] This is normal for a fresh installation")
            result['success'] = True
            return result

        # Read all files and track which IDs we've seen
        seen_ids = {}  # {id: first_filename_that_had_it}
        duplicate_files = []  # [(filename, filepath, id)]
        valid_files = []  # [(filename, filepath, id)]
        
        try:
            existing_files = os.listdir(applist_dir)
            txt_files = [f for f in existing_files if f.endswith('.txt')]
            result['stats']['total_files_scanned'] = len(txt_files)
            
            if verbose and txt_files:
                print(f"  Scanning {len(txt_files)} AppList files...")
            elif verbose:
                print(f"  No .txt files found in AppList directory")
                result['success'] = True
                return result
            
            # Sort files by index to process in order
            txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else 999999)
            
            for filename in txt_files:
                filepath = os.path.join(applist_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content.isdigit():
                        if content in seen_ids:
                            # This is a duplicate
                            duplicate_files.append((filename, filepath, content))
                            if content not in result['duplicates']:
                                result['duplicates'][content] = []
                            result['duplicates'][content].append(filename)
                            result['stats']['duplicates_found'] += 1
                            if verbose:
                                print(f"    DUPLICATE: {filename} contains {content} (first seen in {seen_ids[content]})")
                        else:
                            # First time seeing this ID
                            seen_ids[content] = filename
                            valid_files.append((filename, filepath, content))
                            if content not in result['duplicates']:
                                result['duplicates'][content] = []
                            result['duplicates'][content].append(filename)
                    else:
                        # Invalid content, treat as valid file but warn
                        valid_files.append((filename, filepath, content))
                        if verbose:
                            print(f"    WARNING: {filename} contains non-numeric content: {content}")
                        
                except Exception as e:
                    if verbose:
                        print(f"    ERROR: Could not read file {filename}: {e}")
                    # Keep files we can't read
                    valid_files.append((filename, filepath, ""))
        except Exception as e:
            result['errors'].append(f"Failed to scan AppList directory: {e}")
            return result

        # Remove duplicate files
        for filename, filepath, content in duplicate_files:
            try:
                os.remove(filepath)
                result['stats']['duplicates_removed'] += 1
                if verbose:
                    print(f"    REMOVED: {filename} (duplicate of ID {content})")
            except Exception as e:
                result['errors'].append(f"Failed to remove duplicate file {filename}: {e}")

        # Renumber remaining files to maintain sequential order (0, 1, 2, 3...)
        if valid_files:
            # Sort by original index to maintain order
            valid_files.sort(key=lambda x: int(os.path.splitext(x[0])[0]) if os.path.splitext(x[0])[0].isdigit() else 999999)
            
            # Rename files to sequential indices
            for i, (old_filename, old_filepath, content) in enumerate(valid_files):
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
                            print(f"    RENUMBERED: {old_filename} -> {new_filename}")
                            
                    except Exception as e:
                        result['errors'].append(f"Failed to renumber {old_filename} to {new_filename}: {e}")
        
        result['stats']['files_after_cleanup'] = len(valid_files)
        result['success'] = True
        
        if verbose:
            stats = result['stats']
            print(f"\n  Duplicate cleanup completed:")
            print(f"    Files scanned: {stats['total_files_scanned']}")
            print(f"    Duplicates found: {stats['duplicates_found']}")
            print(f"    Duplicates removed: {stats['duplicates_removed']}")
            print(f"    Files remaining: {stats['files_after_cleanup']}")
            
            if result['duplicates']:
                print(f"\n  Duplicate summary:")
                for app_id, filenames in result['duplicates'].items():
                    if len(filenames) > 1:
                        print(f"    ID {app_id}: found in {len(filenames)} files ({', '.join(filenames)})")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result


def check_for_duplicate_ids_in_applist(gl_path, verbose=True):
    """
    Checks for duplicate IDs in the GreenLuma AppList folder without removing them.
    Useful for diagnostics and reporting.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Result with duplicate information and statistics
    """
    result = {
        'has_duplicates': False,
        'total_files': 0,
        'unique_ids': 0,
        'duplicate_count': 0,
        'duplicates': {}  # {id: [list of filenames that contain this id]}
    }
    
    try:
        applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
        if not os.path.isdir(applist_dir):
            if verbose:
                print(f"[Info] GreenLuma AppList directory not found: {applist_dir}")
            return result

        # Read all files and track IDs
        id_to_files = {}  # {id: [list of filenames]}
        
        existing_files = os.listdir(applist_dir)
        txt_files = [f for f in existing_files if f.endswith('.txt')]
        result['total_files'] = len(txt_files)
        
        if not txt_files:
            if verbose:
                print(f"[Info] No .txt files found in AppList directory")
            return result
        
        if verbose:
            print(f"Checking {len(txt_files)} AppList files for duplicates...")
        
        # Sort files by index for consistent reporting
        txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else 999999)
        
        for filename in txt_files:
            filepath = os.path.join(applist_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content.isdigit():
                    if content not in id_to_files:
                        id_to_files[content] = []
                    id_to_files[content].append(filename)
                    
            except Exception as e:
                if verbose:
                    print(f"  WARNING: Could not read file {filename}: {e}")
        
        # Analyze for duplicates
        result['unique_ids'] = len(id_to_files)
        
        for app_id, filenames in id_to_files.items():
            if len(filenames) > 1:
                result['has_duplicates'] = True
                result['duplicate_count'] += len(filenames) - 1  # Number of extra files
                result['duplicates'][app_id] = filenames
                if verbose:
                    print(f"  DUPLICATE: ID {app_id} found in {len(filenames)} files: {', '.join(filenames)}")
        
        if verbose:
            if result['has_duplicates']:
                print(f"\nDuplicate Summary:")
                print(f"  Total files: {result['total_files']}")
                print(f"  Unique IDs: {result['unique_ids']}")
                print(f"  Duplicate files: {result['duplicate_count']}")
                print(f"  IDs with duplicates: {len(result['duplicates'])}")
            else:
                print(f"  No duplicates found! All {result['total_files']} files contain unique IDs.")
        
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to check for duplicates: {e}")
    
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
        print("  check_duplicates       - Check for duplicate IDs in AppList (no removal)")
        print("Examples:")
        print("  python greenluma_manager.py \"C:\\GreenLuma\" validate")
        print("  python greenluma_manager.py \"C:\\GreenLuma\" configure \"C:\\Steam\"")
        print("  python greenluma_manager.py \"C:\\GreenLuma\" check_duplicates")
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
        print("Available commands: validate, stats, clear, configure")


if __name__ == "__main__":
    """
    Standard script entry point for standalone execution.
    """
    main()