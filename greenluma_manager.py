# greenluma_manager.py
#
# A standalone module for managing GreenLuma integration.
# This module handles AppList management, DLL injector configuration,
# and all GreenLuma-related operations for SuperSexySteam.

import re
import logging
from pathlib import Path
from typing import Dict

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


# =============================================================================
# --- GREENLUMA APPLIST MANAGEMENT ---
# =============================================================================

def clear_greenluma_applist(gl_path):
    """
    Clears all entries from the GreenLuma AppList folder.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.

    Returns:
        int: Number of files deleted, or -1 on error.
    """
    logger.info("Clearing GreenLuma AppList")
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    
    applist_dir = gl_path / 'NormalMode' / 'AppList'
    logger.debug(f"AppList directory: {applist_dir}")
    
    if not applist_dir.is_dir():
        logger.warning(f"GreenLuma AppList directory not found: {applist_dir}")
        return 0

    deleted_count = 0
    try:
        txt_files = list(applist_dir.glob('*.txt'))
        logger.debug(f"Found {len(txt_files)} .txt files to delete")
        
        for txt_file in txt_files:
            try:
                txt_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted {txt_file.name}")
            except Exception as e:
                logger.error(f"Could not delete {txt_file.name}: {e}")
                logger.debug(f"File deletion exception for {txt_file.name}:", exc_info=True)
        
        logger.info(f"Cleared {deleted_count} AppList entries")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to clear AppList: {e}")
        logger.debug("Clear AppList exception:", exc_info=True)
        return -1


def get_greenluma_applist_stats(gl_path):
    """
    Gets statistics about the current GreenLuma AppList using database information
    to accurately categorize AppIDs vs DepotIDs.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.

    Returns:
        dict: Statistics with keys: 'total_files', 'appids', 'depots', 'other'
    """
    logger.info("Getting GreenLuma AppList statistics")
    from database_manager import get_database_manager
    
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    stats = {'total_files': 0, 'appids': 0, 'depots': 0, 'other': 0}
    
    applist_dir = gl_path / 'NormalMode' / 'AppList'
    logger.debug(f"AppList directory: {applist_dir}")
    
    if not applist_dir.is_dir():
        logger.info(f"GreenLuma AppList directory not found or empty: {applist_dir}")
        logger.info("This is normal for a fresh installation or test environment")
        return stats

    try:
        # Get database information for accurate categorization
        logger.debug("Getting database information for ID categorization")
        db = get_database_manager()
        installed_appids = set(db.get_all_installed_appids())
        all_depots = db.get_all_depots_for_installed_apps()
        depot_ids = set(depot['depot_id'] for depot in all_depots)
        
        logger.debug(f"Found {len(installed_appids)} installed AppIDs and {len(depot_ids)} depot IDs in database")
        
        txt_files = list(applist_dir.glob('*.txt'))
        stats['total_files'] = len(txt_files)
        logger.debug(f"Found {len(txt_files)} .txt files in AppList")
        
        if not txt_files:
            logger.info(f"No AppList files found in {applist_dir}")
            logger.info("This is expected for a new installation or test environment")
            return stats
        
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
                logger.debug(f"Processing file {txt_file.name} with content: {content}")
                
                if content.isdigit():
                    # Use database to accurately categorize IDs
                    if content in installed_appids:
                        stats['appids'] += 1
                        logger.debug(f"ID {content} categorized as AppID")
                    elif content in depot_ids:
                        stats['depots'] += 1
                        logger.debug(f"ID {content} categorized as DepotID")
                    else:
                        # ID not found in database - could be legacy or external
                        stats['other'] += 1
                        logger.debug(f"ID {content} not found in database - categorized as other")
                else:
                    stats['other'] += 1
                    logger.debug(f"Non-numeric content in {txt_file.name} - categorized as other")
            except Exception as e:
                stats['other'] += 1
                logger.warning(f"Error reading file {txt_file.name}: {e}")
        
        logger.info(f"GreenLuma AppList stats: {stats['total_files']} files total")
        logger.info(f"AppIDs: {stats['appids']}, DepotIDs: {stats['depots']}, Other/Unknown: {stats['other']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get AppList stats: {e}")
        logger.debug("AppList stats exception:", exc_info=True)
        return stats


# =============================================================================
# --- GREENLUMA DLL INJECTOR CONFIGURATION ---
# =============================================================================

def configure_greenluma_injector(steam_path, greenluma_path):
    """
    Configures the DLLInjector.ini file in the GreenLuma NormalMode directory
    with the correct Steam executable path and GreenLuma DLL path using a robust
    line-by-line replacement method to preserve file structure and comments.
    
    Args:
        steam_path (str or Path): The path to the Steam installation directory.
        greenluma_path (str or Path): The path to the GreenLuma directory.

    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    logger.info("Configuring GreenLuma DLLInjector.ini")
    steam_path = Path(steam_path)
    greenluma_path = Path(greenluma_path)
    
    logger.debug(f"Steam path: {steam_path}")
    logger.debug(f"GreenLuma path: {greenluma_path}")
    
    # Construct the full path to the DLLInjector.ini file
    injector_ini_path = greenluma_path / 'NormalMode' / 'DLLInjector.ini'
    logger.debug(f"DLLInjector.ini path: {injector_ini_path}")
    
    if not injector_ini_path.exists():
        logger.error(f"DLLInjector.ini not found at: {injector_ini_path}")
        return False
    
    try:
        steam_exe_path = steam_path / 'Steam.exe'
        greenluma_dll_path = greenluma_path / 'NormalMode' / 'GreenLuma_2025_x86.dll'
        
        logger.debug(f"Steam executable path: {steam_exe_path}")
        logger.debug(f"GreenLuma DLL path: {greenluma_dll_path}")

        # Define the key-value pairs we want to set.
        # The keys here must match the case in the INI file.
        updates = {
            "UseFullPathsFromIni": "1",
            "Exe": str(steam_exe_path),
            "Dll": str(greenluma_dll_path),
        }
        
        logger.debug(f"Updates to apply: {updates}")

        # Read all lines from the file
        logger.debug("Reading DLLInjector.ini file")
        with open(injector_ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        updated_keys = set()

        # Process each line
        logger.debug(f"Processing {len(lines)} lines from ini file")
        for line in lines:
            stripped_line = line.strip()
            
            # Find which key, if any, this line corresponds to
            key_to_update = None
            for key in updates:
                # Match "Key = Value" or "Key=Value", ignoring case for robustness
                if re.match(rf'^\s*{re.escape(key)}\s*=', stripped_line, re.IGNORECASE):
                    key_to_update = key
                    break

            if key_to_update:
                # This is a line we need to change. Replace it.
                # We use the key's original casing from our `updates` dict.
                new_line = f'{key_to_update} = {updates[key_to_update]}\n'
                new_lines.append(new_line)
                updated_keys.add(key_to_update)
                logger.debug(f"Updated line for key '{key_to_update}': {new_line.strip()}")
            else:
                # This line is not a target for update, so keep it as is.
                new_lines.append(line)
        
        # Write the modified lines back to the file
        logger.debug("Writing updated configuration back to file")
        with open(injector_ini_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        logger.info("Successfully configured DLLInjector.ini")
        logger.info(f"Steam executable: {steam_exe_path}")
        logger.info(f"GreenLuma DLL: {greenluma_dll_path}")
        logger.info("UseFullPathsFromIni: 1")
        logger.debug(f"Updated {len(updated_keys)} configuration keys")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure DLLInjector.ini: {e}")
        logger.debug("DLLInjector configuration exception:", exc_info=True)
        return False


def validate_greenluma_installation(greenluma_path):
    """
    Validates that a GreenLuma installation exists and has the expected structure.

    Args:
        greenluma_path (str or Path): The path to the GreenLuma installation.

    Returns:
        dict: Validation results with keys: 'valid', 'missing_components', 'found_components'
    """
    logger.info("Validating GreenLuma installation")
    greenluma_path = Path(greenluma_path)
    logger.debug(f"GreenLuma path: {greenluma_path}")
    
    result = {
        'valid': False,
        'missing_components': [],
        'found_components': []
    }
    
    if not greenluma_path.is_dir():
        logger.error("GreenLuma path does not exist or is not a directory")
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
    
    logger.debug(f"Checking {len(required_components)} required components")
    
    for component_name, component_path in required_components.items():
        if component_path.exists():
            result['found_components'].append(component_name)
            logger.debug(f"Found component: {component_name}")
        else:
            result['missing_components'].append(component_name)
            logger.debug(f"Missing component: {component_name}")
    
    # Create AppList directory if it's missing but other components exist
    if 'AppList' in result['missing_components'] and len(result['found_components']) > 2:
        try:
            applist_path = required_components['AppList']
            logger.debug(f"Creating missing AppList directory: {applist_path}")
            applist_path.mkdir(parents=True, exist_ok=True)
            result['missing_components'].remove('AppList')
            result['found_components'].append('AppList')
            logger.info("Created missing AppList directory")
        except Exception as e:
            logger.warning(f"Failed to create AppList directory: {e}")
            logger.debug("AppList creation exception:", exc_info=True)
    
    # Consider installation valid if most core components are present
    core_components = ['NormalMode', 'DLLInjector.exe', 'DLLInjector.ini']
    core_found = sum(1 for comp in core_components if comp in result['found_components'])
    result['valid'] = core_found >= len(core_components)
    
    logger.info(f"GreenLuma validation result: valid={result['valid']}")
    logger.info(f"Found components: {len(result['found_components'])}, Missing: {len(result['missing_components'])}")
    
    if result['valid']:
        logger.info("GreenLuma installation appears to be valid")
    else:
        logger.error("GreenLuma installation is incomplete or invalid")
        logger.debug(f"Missing components: {result['missing_components']}")
    
    return result


# =============================================================================
# --- GREENLUMA INTEGRATION ORCHESTRATOR ---
# =============================================================================

def process_single_appid_for_greenluma(gl_path, app_id, depots):
    """
    Add a single AppID and its depots to the GreenLuma AppList.
    Automatically removes duplicates before adding new entries to maintain a clean AppList.
    
    Args:
        gl_path (str or Path): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to add
        depots (list): List of depot dictionaries for this AppID
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    logger.info(f"Adding AppID {app_id} to GreenLuma AppList")
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    logger.debug(f"Processing {len(depots)} depots for AppID {app_id}")
    
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
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        logger.debug(f"AppList directory: {applist_dir}")
        
        if not applist_dir.is_dir():
            try:
                logger.debug("Creating missing AppList directory")
                applist_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created missing AppList directory: {applist_dir}")
            except Exception as e:
                error_msg = f"Could not create AppList directory: {e}"
                logger.error(error_msg)
                logger.debug("AppList directory creation exception:", exc_info=True)
                result['errors'].append(error_msg)
                return result
        
        # Step 1: Automatically clean up any existing duplicates
        logger.debug("Checking for existing duplicates")
        duplicate_check = check_for_duplicate_ids_in_applist(gl_path)
        if duplicate_check['has_duplicates']:
            logger.info(f"Found {duplicate_check['duplicate_count']} duplicate files, cleaning up")
            
            cleanup_result = remove_duplicate_ids_from_applist(gl_path)
            if cleanup_result['success']:
                result['stats']['duplicates_cleaned'] = cleanup_result['stats']['duplicates_removed']
                if cleanup_result['stats']['duplicates_removed'] > 0:
                    logger.info(f"Removed {cleanup_result['stats']['duplicates_removed']} duplicate files")
            else:
                logger.warning(f"Cleanup warnings: {cleanup_result.get('errors', [])}")
                result['warnings'].extend(cleanup_result.get('errors', []))
        
        # Step 2: Scan existing files to check for duplicates of what we're about to add
        logger.debug("Scanning existing files for duplicate detection")
        existing_ids = set()
        try:
            txt_files = list(applist_dir.glob('*.txt'))
            indices = []
            
            logger.debug(f"Found {len(txt_files)} existing .txt files")
            
            for txt_file in txt_files:
                try:
                    content = txt_file.read_text(encoding='utf-8').strip()
                    if content.isdigit():
                        existing_ids.add(content)
                    
                    # Track indices for next available index calculation
                    file_index = txt_file.stem
                    if file_index.isdigit():
                        indices.append(int(file_index))
                except Exception as e:
                    # Skip files we can't read
                    logger.debug(f"Skipping unreadable file {txt_file.name}: {e}")
                    pass
            
            next_index = max(indices) + 1 if indices else 0
            logger.debug(f"Next available index: {next_index}")
            logger.debug(f"Found {len(existing_ids)} existing IDs in AppList")
            
        except Exception as e:
            error_msg = f"Could not scan existing files: {e}"
            logger.error(error_msg)
            logger.debug("File scanning exception:", exc_info=True)
            result['errors'].append(error_msg)
            return result
        
        # Step 3: Add AppID if it doesn't already exist
        if app_id in existing_ids:
            logger.info(f"AppID {app_id} already exists in AppList, skipping")
            result['warnings'].append(f"AppID {app_id} already exists")
            result['stats']['skipped_duplicates'] += 1
        else:
            # Write AppID
            appid_file = applist_dir / f"{next_index}.txt"
            try:
                appid_file.write_text(f"{app_id}\n", encoding='utf-8')
                result['stats']['appids_added'] = 1
                result['stats']['files_created'] += 1
                logger.info(f"Created {appid_file.name} with AppID {app_id}")
                next_index += 1
            except Exception as e:
                error_msg = f"Failed to write AppID file: {e}"
                logger.error(error_msg)
                logger.debug("AppID file write exception:", exc_info=True)
                result['errors'].append(error_msg)
                return result
        
        # Step 4: Add depots (only if they don't already exist)
        logger.debug(f"Processing {len(depots)} depots")
        for depot in depots:
            depot_id = depot['depot_id']
            if depot_id in existing_ids:
                logger.debug(f"DepotID {depot_id} already exists in AppList, skipping")
                result['stats']['skipped_duplicates'] += 1
                continue
                
            depot_file = applist_dir / f"{next_index}.txt"
            try:
                depot_file.write_text(f"{depot_id}\n", encoding='utf-8')
                result['stats']['depots_added'] += 1
                result['stats']['files_created'] += 1
                logger.debug(f"Created {depot_file.name} with DepotID {depot_id}")
                next_index += 1
            except Exception as e:
                error_msg = f"Failed to write depot file for {depot_id}: {e}"
                logger.error(error_msg)
                logger.debug(f"Depot file write exception for {depot_id}:", exc_info=True)
                result['errors'].append(error_msg)
                # Continue with other depots even if one fails
        
        result['success'] = True
        stats = result['stats']
        cleanup_msg = f", cleaned {stats['duplicates_cleaned']} duplicates" if stats['duplicates_cleaned'] > 0 else ""
        logger.info(f"Successfully processed AppID {app_id}: {stats['appids_added']} AppIDs + {stats['depots_added']} depots added, {stats['skipped_duplicates']} duplicates skipped ({stats['files_created']} files created{cleanup_msg})")
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        logger.debug("Process AppID exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def _renumber_applist_files(applist_dir: Path) -> Dict[str, any]:
    """
    Renumbers all .txt files in the AppList directory to be sequential (0, 1, 2...).
    This is a critical cleanup step after removing files to prevent gaps in indices.

    Args:
        applist_dir (Path): The path to the AppList directory.

    Returns:
        A dictionary with 'success' status and a list of 'errors'.
    """
    logger.debug(f"Renumbering AppList files in: {applist_dir}")
    result = {'success': False, 'errors': []}
    
    try:
        # Step 1: Read all existing files and their contents into memory
        files_to_keep = []
        txt_files = list(applist_dir.glob('*.txt'))
        
        # Sort by original index to maintain order as much as possible
        txt_files.sort(key=lambda x: int(x.stem) if x.stem.isdigit() else 999999)
        logger.debug(f"Found {len(txt_files)} files to renumber")
        
        for txt_file in txt_files:
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
                if content:  # Only keep files that have content
                    files_to_keep.append(content)
                    logger.debug(f"Keeping content from {txt_file.name}: {content}")
            except Exception as e:
                logger.warning(f"Could not read file {txt_file.name}, it will be skipped: {e}")

        # Step 2: Remove all original .txt files
        logger.debug(f"Removing {len(txt_files)} original files")
        for txt_file in txt_files:
            try:
                txt_file.unlink()
            except Exception as e:
                error_msg = f"Failed to remove {txt_file.name} during renumbering: {e}"
                logger.error(error_msg)
                logger.debug(f"File removal exception for {txt_file.name}:", exc_info=True)
                result['errors'].append(error_msg)
                return result  # Abort if we can't clean up properly
        
        # Step 3: Write back the files with new, sequential names
        logger.debug(f"Writing {len(files_to_keep)} files with sequential names")
        for i, content in enumerate(files_to_keep):
            new_file = applist_dir / f"{i}.txt"
            try:
                new_file.write_text(f"{content}\n", encoding='utf-8')
                logger.debug(f"Created {new_file.name} with content: {content}")
            except Exception as e:
                error_msg = f"Failed to write new file {new_file.name}: {e}"
                logger.error(error_msg)
                logger.debug(f"File write exception for {new_file.name}:", exc_info=True)
                result['errors'].append(error_msg)
        
        if files_to_keep:
            logger.info(f"Successfully renumbered {len(files_to_keep)} AppList files")
        
        result['success'] = True
        return result

    except Exception as e:
        error_msg = f"Unexpected error during file renumbering: {e}"
        logger.error(error_msg)
        logger.debug("File renumbering exception:", exc_info=True)
        result['errors'].append(error_msg)
        return result


def remove_appid_from_greenluma(gl_path, app_id, depots):
    """
    Remove a specific AppID and its depots from the GreenLuma AppList.
    
    Args:
        gl_path (str or Path): Path to the main GreenLuma folder
        app_id (str): The Steam AppID to remove
        depots (list): List of depot dictionaries for this AppID
        
    Returns:
        dict: Result with success status, errors, and statistics
    """
    logger.info(f"Removing AppID {app_id} from GreenLuma AppList")
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    logger.debug(f"Removing {len(depots)} depots for AppID {app_id}")
    
    result = {
        'success': False,
        'errors': [],
        'stats': {'appids_removed': 0, 'depots_removed': 0, 'files_removed': 0}
    }
    
    try:
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        logger.debug(f"AppList directory: {applist_dir}")
        
        if not applist_dir.is_dir():
            logger.warning(f"GreenLuma AppList directory not found: {applist_dir}")
            result['success'] = True  # Nothing to remove is considered success
            return result
        
        # Collect all IDs to remove (AppID + all depot IDs)
        ids_to_remove = {app_id}
        for depot in depots:
            ids_to_remove.add(depot['depot_id'])
        
        logger.debug(f"IDs to remove: {ids_to_remove}")
        
        # Identify and remove files containing the specified IDs
        try:
            txt_files = list(applist_dir.glob('*.txt'))
            logger.debug(f"Scanning {len(txt_files)} files for removal")
            
            for txt_file in txt_files:
                try:
                    content = txt_file.read_text(encoding='utf-8').strip()
                    
                    if content in ids_to_remove:
                        txt_file.unlink()
                        result['stats']['files_removed'] += 1
                        if content == app_id:
                            result['stats']['appids_removed'] += 1
                            logger.info(f"Removed AppID file {txt_file.name} (contained {content})")
                        else:
                            result['stats']['depots_removed'] += 1
                            logger.debug(f"Removed depot file {txt_file.name} (contained {content})")
                except Exception as e:
                    logger.warning(f"Could not process file {txt_file.name}: {e}")
                    logger.debug(f"File processing exception for {txt_file.name}:", exc_info=True)
        except Exception as e:
            error_msg = f"Failed to scan and remove from AppList: {e}"
            logger.error(error_msg)
            logger.debug("AppList scan/remove exception:", exc_info=True)
            result['errors'].append(error_msg)
            return result
        
        # After removing files, renumber the entire directory to ensure it's sequential
        logger.debug("Renumbering remaining AppList files")
        renumber_result = _renumber_applist_files(applist_dir)
        if not renumber_result['success']:
            logger.error(f"Renumbering failed: {renumber_result['errors']}")
            result['errors'].extend(renumber_result['errors'])
        
        result['success'] = not result['errors']
        stats = result['stats']
        logger.info(f"Successfully removed AppID {app_id}: {stats['appids_removed']} AppIDs, {stats['depots_removed']} depots ({stats['files_removed']} files removed)")
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        logger.debug("Remove AppID exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


# =============================================================================
# --- GREENLUMA DUPLICATE MANAGEMENT ---
# =============================================================================

def remove_duplicate_ids_from_applist(gl_path):
    """
    Detects and removes duplicate IDs from the GreenLuma AppList folder.
    Keeps the first occurrence of each ID, removes subsequent duplicates, then renumbers all files.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.

    Returns:
        dict: Result with success status, errors, statistics, and duplicate details
    """
    logger.info("Scanning GreenLuma AppList for duplicates")
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    
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
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        logger.debug(f"AppList directory: {applist_dir}")
        
        if not applist_dir.is_dir():
            logger.info(f"GreenLuma AppList directory not found: {applist_dir}")
            result['success'] = True
            return result

        seen_ids = set()
        
        try:
            txt_files = list(applist_dir.glob('*.txt'))
            result['stats']['total_files_scanned'] = len(txt_files)
            logger.debug(f"Scanning {len(txt_files)} files for duplicates")
            
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
                            logger.info(f"REMOVED: {txt_file.name} (duplicate of ID {content})")
                        else:
                            # First time seeing this ID
                            seen_ids.add(content)
                            logger.debug(f"Keeping first occurrence of ID {content} in {txt_file.name}")
                except Exception as e:
                    logger.error(f"Could not read file {txt_file.name}, skipping: {e}")
                    logger.debug(f"File read exception for {txt_file.name}:", exc_info=True)
        except Exception as e:
            error_msg = f"Failed to scan and remove duplicates: {e}"
            logger.error(error_msg)
            logger.debug("Duplicate scan/remove exception:", exc_info=True)
            result['errors'].append(error_msg)
            return result

        # If we removed any duplicates, renumber the entire directory
        if result['stats']['duplicates_removed'] > 0:
            logger.debug("Renumbering remaining files after duplicate removal")
            renumber_result = _renumber_applist_files(applist_dir)
            if not renumber_result['success']:
                logger.error(f"Renumbering failed: {renumber_result['errors']}")
                result['errors'].extend(renumber_result['errors'])
        
        result['stats']['files_after_cleanup'] = len(seen_ids)
        result['success'] = not result['errors']
        
        stats = result['stats']
        logger.info("Duplicate cleanup completed:")
        logger.info(f"Files scanned: {stats['total_files_scanned']}")
        logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
        logger.info(f"Files remaining: {stats['files_after_cleanup']}")
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        logger.debug("Remove duplicates exception:", exc_info=True)
        result['errors'].append(error_msg)
    
    return result


def check_for_duplicate_ids_in_applist(gl_path):
    """
    Checks for duplicate IDs in the GreenLuma AppList folder without removing them.
    Useful for diagnostics and reporting.

    Args:
        gl_path (str or Path): The path to the main GreenLuma folder.

    Returns:
        dict: Result with duplicate information and statistics
    """
    logger.debug("Checking for duplicate IDs in GreenLuma AppList")
    gl_path = Path(gl_path)
    logger.debug(f"GreenLuma path: {gl_path}")
    
    result = {
        'has_duplicates': False,
        'total_files': 0,
        'unique_ids': 0,
        'duplicate_count': 0,
        'duplicates': {}  # {id: [list of filenames that contain this id]}
    }
    
    try:
        applist_dir = gl_path / 'NormalMode' / 'AppList'
        logger.debug(f"AppList directory: {applist_dir}")
        
        if not applist_dir.is_dir():
            logger.info(f"GreenLuma AppList directory not found: {applist_dir}")
            return result

        # Read all files and track IDs
        id_to_files = {}  # {id: [list of filenames]}
        
        txt_files = list(applist_dir.glob('*.txt'))
        result['total_files'] = len(txt_files)
        
        if not txt_files:
            logger.info("No .txt files found in AppList directory")
            return result
        
        logger.debug(f"Checking {len(txt_files)} AppList files for duplicates")
        
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
                logger.warning(f"Could not read file {txt_file.name}: {e}")
        
        # Analyze for duplicates
        result['unique_ids'] = len(id_to_files)
        
        for app_id, filenames in id_to_files.items():
            if len(filenames) > 1:
                result['has_duplicates'] = True
                result['duplicate_count'] += len(filenames) - 1  # Number of extra files
                result['duplicates'][app_id] = filenames
                logger.debug(f"DUPLICATE: ID {app_id} found in {len(filenames)} files: {', '.join(filenames)}")
        
        if result['has_duplicates']:
            logger.info(f"Duplicate Summary:")
            logger.info(f"Total files: {result['total_files']}")
            logger.info(f"Unique IDs: {result['unique_ids']}")
            logger.info(f"Duplicate files: {result['duplicate_count']}")
            logger.info(f"IDs with duplicates: {len(result['duplicates'])}")
        else:
            logger.info(f"No duplicates found! All {result['total_files']} files contain unique IDs")
        
    except Exception as e:
        logger.error(f"Failed to check for duplicates: {e}")
        logger.debug("Duplicate check exception:", exc_info=True)
    
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
    
    logger.info("greenluma_manager.py: GreenLuma Integration Management")
    
    if len(sys.argv) < 2:
        logger.info("Usage:")
        logger.info("  python greenluma_manager.py <greenluma_path> [command] [options]")
        logger.info("Commands:")
        logger.info("  validate              - Validate GreenLuma installation")
        logger.info("  stats                 - Show AppList statistics")
        logger.info("  clear                 - Clear all AppList entries")
        logger.info("  configure <steam_path> - Configure DLL injector")
        logger.info("  check_duplicates       - Check for duplicate IDs in AppList (no removal)")
        logger.info("Examples:")
        logger.info("  python greenluma_manager.py \"C:\\GreenLuma\" validate")
        logger.info("  python greenluma_manager.py \"C:\\GreenLuma\" configure \"C:\\Steam\"")
        logger.info("  python greenluma_manager.py \"C:\\GreenLuma\" check_duplicates")
        return
    
    greenluma_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'validate'
    
    logger.info(f"Executing command '{command}' on GreenLuma path: {greenluma_path}")
    
    if command == 'validate':
        validate_greenluma_installation(greenluma_path)
    
    elif command == 'stats':
        get_greenluma_applist_stats(greenluma_path)
    
    elif command == 'clear':
        count = clear_greenluma_applist(greenluma_path)
        if count >= 0:
            logger.info(f"Cleared {count} AppList entries")
    
    elif command == 'configure':
        if len(sys.argv) < 4:
            logger.error("Steam path required for configure command")
            logger.info("Usage: python greenluma_manager.py <greenluma_path> configure <steam_path>")
            return
        
        steam_path = sys.argv[3]
        success = configure_greenluma_injector(steam_path, greenluma_path)
        if success:
            logger.info("DLL injector configured successfully")
        else:
            logger.error("Failed to configure DLL injector")
    
    elif command == 'check_duplicates':
        check_for_duplicate_ids_in_applist(greenluma_path)
    
    else:
        logger.error(f"Unknown command: {command}")
        logger.info("Available commands: validate, stats, clear, configure, check_duplicates")


if __name__ == "__main__":
    main()