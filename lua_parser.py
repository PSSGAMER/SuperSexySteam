# lua_parser.py
#
# A standalone script for parsing .lua files to extract depot information.
# This script scans the 'data' directory for .lua files and extracts depot IDs
# and their corresponding decryption keys.

from pathlib import Path
import re
import sys


# =============================================================================
# --- LUA PARSING FUNCTIONS ---
# =============================================================================

def parse_lua_for_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotID that have a corresponding
    DepotKey, properly distinguishing between the AppID (from filename) and actual DepotID.

    Args:
        lua_path (str or Path): The full path to the .lua file to be parsed.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if the file is not found or an error occurs.
    """
    # Convert to Path object if needed
    lua_path = Path(lua_path)
    
    # Extract AppID from filename to exclude it from depot results
    app_id = lua_path.stem
    
    # Multiple regex patterns to handle different Lua formats
    patterns = [
        # Pattern 1: adddepot with key: adddepot(12345, "HEXKEY")
        re.compile(r'^\s*adddepot\((\d+),\s*"([a-zA-Z0-9]+)"\)'),
        
        # Pattern 2: addappid function calls: addappid(12345, 1, "HEXKEY")
        re.compile(r'^\s*addappid\((\d+),\s*1,\s*"([a-zA-Z0-9]+)"\)'),
    ]

    extracted_depots = []
    try:
        with lua_path.open('r', encoding='utf-8') as f:
            for line in f:
                # Try each pattern
                for pattern in patterns:
                    match = pattern.match(line)
                    if match:
                        depot_id = match.group(1)
                        depot_key = match.group(2)
                        
                        # Skip if this ID matches the AppID (from filename)
                        # Only actual depot IDs with keys should be included
                        if depot_id != app_id:
                            extracted_depots.append({
                                'depot_id': depot_id,
                                'depot_key': depot_key
                            })
                        break  # Stop at first match for this line
                        
    except FileNotFoundError:
        print(f"  [Warning] Could not find file during parsing: {lua_path}")
    except Exception as e:
        print(f"  [Error] Failed to read or parse {lua_path.name}: {e}")

    return extracted_depots


def parse_lua_for_all_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotID from addappid and adddepot calls,
    properly distinguishing between the AppID (from filename) and actual DepotIDs.
    
    This function uses the filename to determine the AppID and only treats other
    numeric IDs as DepotIDs, providing accurate categorization.

    Args:
        lua_path (str or Path): The full path to the .lua file to be parsed.

    Returns:
        dict: A dictionary with 'app_id' (from filename) and 'depots' (list of depot dicts).
              Returns empty data if the file is not found or an error occurs.
    """
    lua_path = Path(lua_path)
    
    # Extract AppID from filename
    app_id = lua_path.stem
    
    result = {
        'app_id': app_id,
        'depots': []
    }
    
    # Validate that filename is a numeric AppID
    if not app_id.isdigit():
        print(f"  [Warning] Filename '{lua_path.name}' does not contain a valid numeric AppID")
        return result

    # Multiple regex patterns to handle different Lua formats
    patterns = [
        # Pattern 1: adddepot with key: adddepot(12345, "KEY123")
        (re.compile(r'^\s*adddepot\((\d+),\s*"([a-zA-Z0-9]+)"\)'), True),
        
        # Pattern 2: adddepot without key: adddepot(12345)
        (re.compile(r'^\s*adddepot\((\d+)\)'), False),
        
        # Pattern 3: addappid with key: addappid(12345, 1, "KEY123")
        (re.compile(r'^\s*addappid\((\d+),\s*1,\s*"([a-zA-Z0-9]+)"\)'), True),
        
        # Pattern 4: addappid without key: addappid(12345, ...)
        (re.compile(r'^\s*addappid\((\d+),?\s*[^,\)]*\)'), False),
    ]

    extracted_depots = []
    try:
        with lua_path.open('r', encoding='utf-8') as f:
            for line in f:
                # Ignore comment lines to avoid parsing them.
                if line.strip().startswith('--'):
                    continue

                # Try each pattern
                for pattern, has_key in patterns:
                    match = pattern.match(line)
                    if match:
                        depot_id = match.group(1)
                        
                        # Skip if this ID matches the AppID (from filename)
                        # Only actual depot IDs should be included
                        if depot_id == app_id:
                            continue
                        
                        # Check if we already have this depot
                        existing_depot = next((d for d in extracted_depots if d['depot_id'] == depot_id), None)
                        
                        if existing_depot:
                            # If we already have this depot and this match has a key, update it
                            if has_key and len(match.groups()) >= 2:
                                existing_depot['depot_key'] = match.group(2)
                        else:
                            # Add new depot
                            depot_data = {'depot_id': depot_id}
                            if has_key and len(match.groups()) >= 2:
                                depot_data['depot_key'] = match.group(2)
                            extracted_depots.append(depot_data)
                        
                        break  # Stop at first match for this line
    
    except FileNotFoundError:
        print(f"  [Warning] Could not find file during parsing: {lua_path}")
    except Exception as e:
        print(f"  [Error] Failed to read or parse {lua_path.name}: {e}")

    result['depots'] = extracted_depots
    return result


def parse_all_lua_files(data_dir='data', verbose=True):
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information from them.

    Args:
        data_dir (str or Path): The directory to scan for .lua files. Defaults to 'data'.
        verbose (bool): Whether to print progress information. Defaults to True.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if no data directory is found or no .lua files exist.
    """
    data_dir = Path(data_dir)
    all_depots = []
    
    if not data_dir.is_dir():
        if verbose:
            print(f"[Warning] Data directory '{data_dir}' not found.")
        return all_depots
    
    lua_files_found = 0
    if verbose:
        print(f"Scanning '{data_dir}' directory for .lua files...")
    
    # Walk through all subdirectories in the data folder
    for lua_path in data_dir.rglob('*.lua'):
        app_id = lua_path.stem
        if verbose:
            print(f"  Processing {lua_path.name} (AppID: {app_id})")
        
        depots = parse_lua_for_depots(lua_path)
        all_depots.extend(depots)
        lua_files_found += 1
    
    if verbose:
        print(f"Found {lua_files_found} .lua file(s) containing {len(all_depots)} depot keys total.")
    
    return all_depots


def parse_all_lua_files_structured(data_dir='data', verbose=True):
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information, returning structured data with AppIDs and their associated depots.

    Args:
        data_dir (str or Path): The directory to scan for .lua files. Defaults to 'data'.
        verbose (bool): Whether to print progress information. Defaults to True.

    Returns:
        list: A list of dictionaries. Each dictionary has 'app_id' and 'depots' keys.
              Returns empty list if no data directory is found or no .lua files exist.
    """
    # Convert to Path object
    data_dir = Path(data_dir)
    all_apps = []
    
    if not data_dir.is_dir():
        if verbose:
            print(f"[Warning] Data directory '{data_dir}' not found.")
        return all_apps
    
    lua_files_found = 0
    if verbose:
        print(f"Scanning '{data_dir}' directory for .lua files...")
    
    # Walk through all subdirectories in the data folder
    for lua_path in data_dir.rglob('*.lua'):
        # Use the improved function that properly categorizes AppID vs DepotID
        app_data = parse_lua_for_all_depots(lua_path)
        
        if verbose:
            print(f"  Processing {lua_path.name} (AppID: {app_data['app_id']}) - Found {len(app_data['depots'])} depots")
        
        all_apps.append(app_data)
        lua_files_found += 1
    
    total_depots = sum(len(app['depots']) for app in all_apps)
    if verbose:
        print(f"Found {lua_files_found} .lua file(s) containing {total_depots} depot entries total.")
    
    return all_apps


def get_unique_depots(all_depots):
    """
    Remove duplicate depot entries, keeping the last occurrence of each depot ID.

    Args:
        all_depots (list): List of depot dictionaries with 'depot_id' and 'depot_key'.

    Returns:
        dict: Dictionary mapping depot_id to depot_key with duplicates removed.
    """
    unique_depots = {}
    for depot in all_depots:
        unique_depots[depot['depot_id']] = depot['depot_key']
    return unique_depots


# =============================================================================
# --- MAIN EXECUTION ---
# =============================================================================

def main():
    """
    Main function for standalone execution.
    Parses all .lua files and displays the results.
    """
    print("--- lua_parser.py: Parsing .lua files for depot data ---")
    
    # Parse command line arguments
    data_dir = Path('data')
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    
    # Parse all lua files
    all_depots = parse_all_lua_files(data_dir)
    
    if not all_depots:
        print("[Warning] No depot data found.")
        return
    
    # Get unique depots
    unique_depots = get_unique_depots(all_depots)
    
    print(f"\n--- Results ---")
    print(f"Total depot entries: {len(all_depots)}")
    print(f"Unique depot keys: {len(unique_depots)}")
    
    # Display first few entries as sample
    print(f"\nSample depot entries:")
    for i, (depot_id, depot_key) in enumerate(list(unique_depots.items())[:5]):
        print(f"  {depot_id}: {depot_key}")
    
    if len(unique_depots) > 5:
        print(f"  ... and {len(unique_depots) - 5} more")


if __name__ == "__main__":
    """
    Standard script entry point. Ensures that the `main()` function is only
    called when the script is executed directly, not when imported as a module.
    """
    main()