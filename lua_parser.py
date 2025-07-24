# lua_parser.py
#
# A standalone script for parsing .lua files to extract depot information.
# This script scans the 'data' directory for .lua files and extracts depot IDs
# and their corresponding decryption keys.

import os
import re
import sys


# =============================================================================
# --- LUA PARSING FUNCTIONS ---
# =============================================================================

def parse_lua_for_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotIDs that have a corresponding
    DepotKey. It specifically looks for the 'addappid(id, 1, "key")' format.

    This function is designed to be resilient, ignoring comment lines and lines
    that define AppIDs or DLCs without an associated decryption key.

    Args:
        lua_path (str): The full path to the .lua file to be parsed.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if the file is not found or an error occurs.
    """
    # This regex is crafted to match lines containing a depot with a key.
    # - `^\s*addappid\(`: Matches the start of the line and the function name.
    # - `(\d+)`: Captures the numeric DepotID (Group 1).
    # - `,\s*1,\s*`: Ensures it's a line with the '1' parameter, which typically
    #                indicates a depot with a key, not just a DLC definition.
    # - `"([a-fA-F0-9]+)"`: Captures the hexadecimal DepotKey (Group 2).
    depot_pattern = re.compile(r'^\s*addappid\((\d+),\s*1,\s*"([a-fA-F0-9]+)"\)')

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
                    depot_key = match.group(2)
                    extracted_depots.append({
                        'depot_id': depot_id,
                        'depot_key': depot_key
                    })
    except FileNotFoundError:
        print(f"  [Warning] Could not find file during parsing: {lua_path}")
    except Exception as e:
        print(f"  [Error] Failed to read or parse {os.path.basename(lua_path)}: {e}")

    return extracted_depots


def parse_all_lua_files(data_dir='data', verbose=True):
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information from them.

    Args:
        data_dir (str): The directory to scan for .lua files. Defaults to 'data'.
        verbose (bool): Whether to print progress information. Defaults to True.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if no data directory is found or no .lua files exist.
    """
    all_depots = []
    
    if not os.path.isdir(data_dir):
        if verbose:
            print(f"[Warning] Data directory '{data_dir}' not found.")
        return all_depots
    
    lua_files_found = 0
    if verbose:
        print(f"Scanning '{data_dir}' directory for .lua files...")
    
    # Walk through all subdirectories in the data folder
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if filename.lower().endswith('.lua'):
                lua_path = os.path.join(root, filename)
                app_id = os.path.splitext(filename)[0]
                if verbose:
                    print(f"  Processing {filename} (AppID: {app_id})")
                
                depots = parse_lua_for_depots(lua_path)
                all_depots.extend(depots)
                lua_files_found += 1
    
    if verbose:
        print(f"Found {lua_files_found} .lua file(s) containing {len(all_depots)} depot keys total.")
    
    return all_depots


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
    data_dir = 'data'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
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
