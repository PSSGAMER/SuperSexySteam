# greenluma_manager.py
#
# A standalone module for managing GreenLuma integration.
# This module handles AppList management, DLL injector configuration,
# and all GreenLuma-related operations for SuperSexySteam.

import configparser
from pathlib import Path
from typing import Dict


# =============================================================================
# --- GREENLUMA APPLIST MANAGEMENT ---
# =============================================================================

def clear_greenluma_applist(gl_path, verbose=True):
    """
    Clears all entries from the GreenLuma AppList folder.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        int: Number of files deleted, or -1 on error.
    """
    gl_path = Path(gl_path)
    
    if verbose:
        print(f"\nClearing GreenLuma AppList: {gl_path}")
    
    applist_dir = gl_path / 'NormalMode' / 'AppList'
    if not applist_dir.is_dir():
        if verbose:
            print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
        return 0

    deleted_count = 0
    try:
        for txt_file in applist_dir.glob('*.txt'):
            try:
                txt_file.unlink()
                deleted_count += 1
                if verbose:
                    print(f"  - Deleted {txt_file.name}")
            except Exception as e:
                if verbose:
                    print(f"[Error] Could not delete {txt_file.name}: {e}")
        
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
        gl_path (str or Path): The path to the main GreenLuma folder.
        verbose (bool): Whether to print information.

    Returns:
        dict: Statistics with keys: 'total_files', 'appids', 'depots', 'other'
    """
    from database_manager import get_database_manager
    
    gl_path = Path(gl_path)
    stats = {'total_files': 0, 'appids': 0, 'depots': 0, 'other': 0}
    
    applist_dir = gl_path / 'NormalMode' / 'AppList'
    if not applist_dir.is_dir():
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
        
        txt_files = list(applist_dir.glob('*.txt'))
        stats['total_files'] = len(txt_files)
        
        if not txt_files:
            if verbose:
                print(f"[Info] No AppList files found in {applist_dir}")
                print(f"[Info] This is expected for a new installation or test environment")
            return stats
        
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
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
        steam_path (str or Path): The path to the Steam installation directory.
        greenluma_path (str or Path): The path to the GreenLuma directory.
        verbose (bool): Whether to print progress information.

    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    steam_path = Path(steam_path)
    greenluma_path = Path(greenluma_path)
    
    if verbose:
        print(f"\nConfiguring GreenLuma DLLInjector.ini...")
    
    # Construct the full path to the DLLInjector.ini file
    injector_ini_path = greenluma_path / 'NormalMode' / 'DLLInjector.ini'
    
    if not injector_ini_path.exists():
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
        steam_exe_path = steam_path / 'Steam.exe'
        greenluma_dll_path = greenluma_path / 'NormalMode' / 'GreenLuma_2025_x86.dll'
        
        # Set the values in the [DLLInjector] section (convert Path objects to strings for INI)
        config.set('DLLInjector', 'UseFullPathsFromIni', '1')
        config.set('DLLInjector', 'Exe', str(steam_exe_path))
        config.set('DLLInjector', 'Dll', str(greenluma_dll_path))

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
        greenluma_path (str or Path): The path to the GreenLuma installation.
        verbose (bool): Whether to print validation information.

    Returns:
        dict: Validation results with keys: 'valid', 'missing_components', 'found_components'
    """
    greenluma_path = Path(greenluma_path)
    
    if verbose:
        print(f"Validating GreenLuma installation: {greenluma_path}")
    
    result = {
        'valid': False,
        'missing_components': [],
        'found_components': []
    }
    
    if not greenluma_path.is_dir():
        if verbose:
            print("[Error] GreenLuma path does not exist or is not a directory.")
        result['missing_components'].append('base_directory')
        return result
    
    # Check for required components
    required_components = {
        'NormalMode': greenluma_path / 'NormalMode',
        'DLLInjector.exe': greenluma_path / 'NormalMode' / 'DLLInjector.exe',
        'DLLInjector.ini': greenluma_path / 'NormalMode' / 'DLLInjector.ini',
        'GreenLuma_DLL_x86': greenluma_path / 'NormalMode' / 'GreenLuma_2025_x86.dll',
        'GreenLuma_DLL_x64': greenluma_path / 'NormalMode' / 'GreenLuma_2025_x64.dll',
        'AppList': greenluma_path / 'NormalMode' / 'AppList'
    }
    
    for component_name, component_path in required_components.items():
        if component_path.exists():
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
            applist_path.mkdir(parents=True, exist_ok=True)
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
        gl_path (str or Path): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to add
        depots (list): List of depot dictionaries for this AppID
        verbose (bool): Whether to print progress information
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    gl_path = Path(gl_path)
    
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
        
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        if not applist_dir.is_dir():
            try:
                applist_dir.mkdir(parents=True, exist_ok=True)
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
            txt_files = list(applist_dir.glob('*.txt'))
            indices = []
            
            for txt_file in txt_files:
                try:
                    content = txt_file.read_text(encoding='utf-8').strip()
                    if content.isdigit():
                        existing_ids.add(content)
                    
                    # Track indices for next available index calculation
                    file_index = txt_file.stem
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
            appid_file = applist_dir / f"{next_index}.txt"
            try:
                appid_file.write_text(f"{app_id}\n", encoding='utf-8')
                result['stats']['appids_added'] = 1
                result['stats']['files_created'] += 1
                if verbose:
                    print(f"  - Created {appid_file.name} with AppID {app_id}")
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
                
            depot_file = applist_dir / f"{next_index}.txt"
            try:
                depot_file.write_text(f"{depot_id}\n", encoding='utf-8')
                result['stats']['depots_added'] += 1
                result['stats']['files_created'] += 1
                if verbose:
                    print(f"  - Created {depot_file.name} with DepotID {depot_id}")
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


def _renumber_applist_files(applist_dir: Path, verbose: bool) -> Dict[str, any]:
    """
    Renumbers all .txt files in the AppList directory to be sequential (0, 1, 2...).
    This is a critical cleanup step after removing files to prevent gaps in indices.

    Args:
        applist_dir (Path): The path to the AppList directory.
        verbose (bool): Whether to print progress information.

    Returns:
        A dictionary with 'success' status and a list of 'errors'.
    """
    result = {'success': False, 'errors': []}
    
    try:
        # Step 1: Read all existing files and their contents into memory
        files_to_keep = []
        txt_files = list(applist_dir.glob('*.txt'))
        
        # Sort by original index to maintain order as much as possible
        txt_files.sort(key=lambda x: int(x.stem) if x.stem.isdigit() else 999999)
        
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
                if content:  # Only keep files that have content
                    files_to_keep.append(content)
            except Exception as e:
                if verbose:
                    print(f"    [Warning] Could not read file {txt_file.name}, it will be skipped: {e}")

        # Step 2: Remove all original .txt files
        for txt_file in txt_files:
            try:
                txt_file.unlink()
            except Exception as e:
                result['errors'].append(f"Failed to remove {txt_file.name} during renumbering: {e}")
                return result  # Abort if we can't clean up properly
        
        # Step 3: Write back the files with new, sequential names
        for i, content in enumerate(files_to_keep):
            new_file = applist_dir / f"{i}.txt"
            try:
                new_file.write_text(f"{content}\n", encoding='utf-8')
            except Exception as e:
                result['errors'].append(f"Failed to write new file {new_file.name}: {e}")
        
        if verbose and files_to_keep:
            print(f"  Successfully renumbered {len(files_to_keep)} AppList files.")
        
        result['success'] = True
        return result

    except Exception as e:
        result['errors'].append(f"Unexpected error during file renumbering: {e}")
        return result


def remove_appid_from_greenluma(gl_path, app_id, depots, verbose=True):
    """
    Remove a specific AppID and its depots from the GreenLuma AppList.
    
    Args:
        gl_path (str or Path): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to remove
        depots (list): List of depot dictionaries for this AppID
        verbose (bool): Whether to print progress information
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    gl_path = Path(gl_path)
    
    result = {
        'success': False,
        'errors': [],
        'stats': {'appids_removed': 0, 'depots_removed': 0, 'files_removed': 0}
    }
    
    try:
        if verbose:
            print(f"\nRemoving AppID {app_id} from GreenLuma AppList: {gl_path}")
        
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        if not applist_dir.is_dir():
            if verbose:
                print(f"[Warning] GreenLuma AppList directory not found: {applist_dir}")
            result['success'] = True  # Nothing to remove is considered success
            return result
        
        # Collect all IDs to remove (AppID + all depot IDs)
        ids_to_remove = {app_id}
        for depot in depots:
            ids_to_remove.add(depot['depot_id'])
        
        # Identify and remove files containing the specified IDs
        try:
            txt_files = list(applist_dir.glob('*.txt'))
            for txt_file in txt_files:
                try:
                    content = txt_file.read_text(encoding='utf-8').strip()
                    
                    if content in ids_to_remove:
                        txt_file.unlink()
                        result['stats']['files_removed'] += 1
                        if content == app_id:
                            result['stats']['appids_removed'] += 1
                        else:
                            result['stats']['depots_removed'] += 1
                        if verbose:
                            print(f"  - Removed {txt_file.name} (contained {content})")
                except Exception as e:
                    if verbose:
                        print(f"[Warning] Could not process file {txt_file.name}: {e}")
        except Exception as e:
            result['errors'].append(f"Failed to scan and remove from AppList: {e}")
            return result
        
        # After removing files, renumber the entire directory to ensure it's sequential
        if verbose:
            print(f"  Renumbering remaining AppList files...")
        renumber_result = _renumber_applist_files(applist_dir, verbose)
        if not renumber_result['success']:
            result['errors'].extend(renumber_result['errors'])
        
        result['success'] = not result['errors']
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
    Keeps the first occurrence of each ID, removes subsequent duplicates, then renumbers all files.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Result with success status, errors, statistics, and duplicate details
    """
    gl_path = Path(gl_path)
    
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
        
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        if not applist_dir.is_dir():
            if verbose:
                print(f"[Info] GreenLuma AppList directory not found: {applist_dir}")
            result['success'] = True
            return result

        seen_ids = set()
        
        try:
            txt_files = list(applist_dir.glob('*.txt'))
            result['stats']['total_files_scanned'] = len(txt_files)
            
            # Sort files by index to ensure "first" occurrence is kept correctly
            txt_files.sort(key=lambda x: int(x.stem) if x.stem.isdigit() else 999999)
            
            for txt_file in txt_files:
                try:
                    content = txt_file.read_text(encoding='utf-8').strip()
                    
                    if content.isdigit():
                        if content in seen_ids:
                            # This is a duplicate, remove it
                            txt_file.unlink()
                            result['stats']['duplicates_removed'] += 1
                            if verbose:
                                print(f"    REMOVED: {txt_file.name} (duplicate of ID {content})")
                        else:
                            # First time seeing this ID
                            seen_ids.add(content)
                except Exception as e:
                    if verbose:
                        print(f"    ERROR: Could not read file {txt_file.name}, skipping: {e}")
        except Exception as e:
            result['errors'].append(f"Failed to scan and remove duplicates: {e}")
            return result

        # If we removed any duplicates, renumber the entire directory
        if result['stats']['duplicates_removed'] > 0:
            if verbose:
                print("    Renumbering remaining files...")
            renumber_result = _renumber_applist_files(applist_dir, verbose)
            if not renumber_result['success']:
                result['errors'].extend(renumber_result['errors'])
        
        result['stats']['files_after_cleanup'] = len(seen_ids)
        result['success'] = not result['errors']
        
        if verbose:
            stats = result['stats']
            print(f"\n  Duplicate cleanup completed:")
            print(f"    Files scanned: {stats['total_files_scanned']}")
            print(f"    Duplicates removed: {stats['duplicates_removed']}")
            print(f"    Files remaining: {stats['files_after_cleanup']}")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result


def check_for_duplicate_ids_in_applist(gl_path, verbose=True):
    """
    Checks for duplicate IDs in the GreenLuma AppList folder without removing them.
    Useful for diagnostics and reporting.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.
        verbose (bool): Whether to print progress information.

    Returns:
        dict: Result with duplicate information and statistics
    """
    gl_path = Path(gl_path)
    
    result = {
        'has_duplicates': False,
        'total_files': 0,
        'unique_ids': 0,
        'duplicate_count': 0,
        'duplicates': {}  # {id: [list of filenames that contain this id]}
    }
    
    try:
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        if not applist_dir.is_dir():
            if verbose:
                print(f"[Info] GreenLuma AppList directory not found: {applist_dir}")
            return result

        # Read all files and track IDs
        id_to_files = {}  # {id: [list of filenames]}
        
        txt_files = list(applist_dir.glob('*.txt'))
        result['total_files'] = len(txt_files)
        
        if not txt_files:
            if verbose:
                print(f"[Info] No .txt files found in AppList directory")
            return result
        
        if verbose:
            print(f"Checking {len(txt_files)} AppList files for duplicates...")
        
        # Sort files by index for consistent reporting
        txt_files.sort(key=lambda x: int(x.stem) if x.stem.isdigit() else 999999)
        
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
            
                if content.isdigit():
                    if content not in id_to_files:
                        id_to_files[content] = []
                    id_to_files[content].append(txt_file.name)
                    
            except Exception as e:
                if verbose:
                    print(f"  WARNING: Could not read file {txt_file.name}: {e}")
        
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
    
    elif command == 'check_duplicates':
        check_for_duplicate_ids_in_applist(greenluma_path)
    
    else:
        print(f"[Error] Unknown command: {command}")
        print("Available commands: validate, stats, clear, configure, check_duplicates")


if __name__ == "__main__":
    """
    Standard script entry point for standalone execution.
    """
    main()