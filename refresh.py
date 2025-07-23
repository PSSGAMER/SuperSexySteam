# refresh.py
#
# A standalone script that acts as a "database refresher" for SuperSexySteam.
# This script refreshes the Steam configuration by parsing all available data
# and updating Steam's depot keys and cache.
#
# Main Workflow:
# 1. Reads 'config.ini' to get the user-configured Steam path.
# 2. Scans the entire 'data' directory for all .lua files.
# 3. Parses all .lua files to extract depot and key information.
# 4. Completely replaces Steam's 'config/config.vdf' depots section with
#    all the collected depot decryption keys.
# 5. Manages the Steam 'depotcache' folder by clearing its contents and copying
#    all .manifest files from the local 'data' directory into it.
#
# This script uses only standard Python libraries.

import configparser
import os
import re
import shutil
import time


# =============================================================================
# --- DATA PARSING FUNCTIONS ---
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


def parse_all_lua_files():
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information from them.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if no data directory is found or no .lua files exist.
    """
    data_dir = 'data'
    all_depots = []
    
    if not os.path.isdir(data_dir):
        print(f"[Warning] Data directory '{data_dir}' not found.")
        return all_depots
    
    lua_files_found = 0
    print(f"Scanning '{data_dir}' directory for .lua files...")
    
    # Walk through all subdirectories in the data folder
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if filename.lower().endswith('.lua'):
                lua_path = os.path.join(root, filename)
                app_id = os.path.splitext(filename)[0]
                print(f"  Processing {filename} (AppID: {app_id})")
                
                depots = parse_lua_for_depots(lua_path)
                all_depots.extend(depots)
                lua_files_found += 1
    
    print(f"Found {lua_files_found} .lua file(s) containing {len(all_depots)} depot keys total.")
    return all_depots


# =============================================================================
# --- FILE MODIFICATION FUNCTIONS ---
# =============================================================================

def update_config_vdf(vdf_path, all_depots):
    """
    Completely replaces the 'depots' section within Steam's config.vdf file.

    This function reads the VDF file as plain text, finds and removes the existing
    'depots' block, then rebuilds it entirely with all the provided depot data.
    This approach ensures a clean, consistent depot section.

    Args:
        vdf_path (str): The full path to Steam's config.vdf file.
        all_depots (list): A list of depot dictionaries to write to the file.
    """
    print(f"\nProcessing Steam config: {vdf_path}")
    if not os.path.exists(vdf_path):
        print("[Error] config.vdf not found at the specified path.")
        return

    if not all_depots:
        print("[Warning] No depot data provided. Skipping config.vdf update.")
        return

    # --- Step 1: Read the entire VDF file into memory ---
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[Error] Could not read config.vdf: {e}")
        return

    # --- Step 2: Find and remove the existing "depots" section ---
    in_depots_section = False
    depots_start_index, depots_end_index = -1, -1
    brace_level = 0

    # Iterate through the file lines to identify the start and end of the section.
    for i, line in enumerate(lines):
        if '"depots"' in line and not in_depots_section:
            in_depots_section = True
            depots_start_index = i
            # Brace counting begins after the "depots" line is found.
            for j in range(i, len(lines)):
                if '{' in lines[j]:
                    brace_level += 1
                    break
            continue

        if in_depots_section:
            if '{' in line: brace_level += 1
            if '}' in line: brace_level -= 1

            # When brace level returns to 0, the section has ended.
            if brace_level == 0:
                depots_end_index = i
                break

    # --- Step 3: Build the new depots section from all depot data ---
    print(f"  Building new depots section with {len(all_depots)} depot keys...")
    
    # Convert list to dictionary to eliminate duplicates (last key wins)
    depots_dict = {}
    for depot in all_depots:
        depots_dict[depot['depot_id']] = depot['depot_key']
    
    new_depots_lines = []
    base_indent = '\t' * 4  # Match Steam's indentation style.
    new_depots_lines.append(f'{base_indent}"depots"\n')
    new_depots_lines.append(f'{base_indent}{{\n')
    
    # Sort by Depot ID for a clean, consistent output.
    for depot_id, key in sorted(depots_dict.items()):
        new_depots_lines.append(f'{base_indent}\t"{depot_id}"\n')
        new_depots_lines.append(f'{base_indent}\t{{\n')
        new_depots_lines.append(f'{base_indent}\t\t"DecryptionKey"\t\t"{key}"\n')
        new_depots_lines.append(f'{base_indent}\t}}\n')
    new_depots_lines.append(f'{base_indent}}}\n')

    # --- Step 4: Replace or insert the depots section ---
    if depots_start_index != -1 and depots_end_index != -1:
        # Replace existing section
        print("  Replacing existing depots section...")
        final_lines = lines[:depots_start_index] + new_depots_lines + lines[depots_end_index + 1:]
    else:
        # Insert new section at the end if no existing section found
        print("  No existing depots section found. Adding new section...")
        # Insert before the final closing brace of the file
        insert_index = len(lines) - 1
        while insert_index > 0 and not lines[insert_index].strip():
            insert_index -= 1  # Skip empty lines at the end
        final_lines = lines[:insert_index] + new_depots_lines + lines[insert_index:]

    # --- Step 5: Backup the old file and write the new one ---
    try:
        backup_path = vdf_path + '.bak'
        print(f"  Backing up original config to {os.path.basename(backup_path)}")
        shutil.copy2(vdf_path, backup_path)
        print("  Writing updated config.vdf...")
        with open(vdf_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        print(f"  Successfully updated config.vdf with {len(depots_dict)} unique depot keys.")
    except Exception as e:
        print(f"[Error] Failed to write updated config.vdf: {e}")

def manage_depot_cache(steam_path):
    """
    Clears the Steam depotcache folder and copies all .manifest files from the
    local 'data' directory into it.

    This ensures that Steam has the correct manifest files for any subsequent
    operations without having to download them.

    Args:
        steam_path (str): The path to the main Steam installation folder.
    """
    depotcache_dir = os.path.join(steam_path, 'depotcache')
    data_dir = 'data'
    print(f"\nProcessing Steam depotcache: {depotcache_dir}")

    if not os.path.isdir(data_dir):
        print("[Warning] 'data' directory not found. Nothing to copy.")
        return

    try:
        # Create the depotcache directory if it doesn't exist.
        os.makedirs(depotcache_dir, exist_ok=True)
        # Clear all contents of the directory for a clean slate.
        print("  Clearing existing depotcache contents...")
        for item_name in os.listdir(depotcache_dir):
            item_path = os.path.join(depotcache_dir, item_name)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    except Exception as e:
        print(f"[Error] Failed to clear depotcache: {e}")
        return

    # Walk through the entire 'data' directory tree to find all .manifest files.
    print("  Copying new manifest files...")
    manifest_count = 0
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if filename.lower().endswith('.manifest'):
                source_path = os.path.join(root, filename)
                dest_path = os.path.join(depotcache_dir, filename)
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"    - Copied {filename}")
                    manifest_count += 1
                except Exception as e:
                    print(f"[Error] Failed to copy {filename}: {e}")

    print(f"  Finished. Copied {manifest_count} manifest files.")


# =============================================================================
# --- MAIN EXECUTION ---
# =============================================================================

def main():
    """
    The main orchestrator function for the script.
    It reads configuration, parses all available lua data, and refreshes
    the Steam configuration database.
    """
    print("--- refresh.py: Refreshing Steam database ---")

    # --- Configuration Loading ---
    app_config = configparser.ConfigParser()
    app_config.read('config.ini')
    steam_path = app_config.get('Paths', 'steam_path', fallback='')

    if not steam_path or not os.path.isdir(steam_path):
        print(f"[Error] Steam path '{steam_path}' is invalid or not configured in config.ini.")
        print("Please run SuperSexySteam.py first to configure paths.")
        return

    # --- Data Parsing ---
    print("\n--- Parsing all depot data ---")
    all_depots = parse_all_lua_files()

    if not all_depots:
        print("[Warning] No depot data found. Nothing to refresh.")
        return

    # --- Update Steam VDF ---
    print("\n--- Updating Steam configuration ---")
    config_vdf_path = os.path.join(steam_path, 'config', 'config.vdf')
    update_config_vdf(config_vdf_path, all_depots)

    # --- Manage Depot Cache ---
    print("\n--- Refreshing depot cache ---")
    manage_depot_cache(steam_path)

    print("\n-------------------------------------------")
    print("Database refresh complete!")
    print(f"Processed {len(all_depots)} depot keys total.")
    print("Steam configuration has been updated.")
    
    # Brief pause to allow reading of the final output
    time.sleep(3)

if __name__ == "__main__":
    """
    Standard script entry point. Ensures that the `main()` function is only
    called when the script is executed directly, not when imported as a module.
    """
    main()

# Docs are generated by AI and may be inaccurate