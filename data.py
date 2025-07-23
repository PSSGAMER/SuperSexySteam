# data.py
#
# This script acts as the "back-end" processor for the SuperSexySteam tool.
# It is executed automatically by SuperSexySteam.py after the user clicks "Apply".
# Its primary responsibilities are to read the data prepared by the GUI,
# parse the relevant files, and perform modifications to the Steam and GreenLuma
# configurations.
#
# Main Workflow:
# 1. Reads 'config.ini' to get the user-configured paths for Steam and GreenLuma.
# 2. Reads 'data.ini' to get the lists of "new" and "updated" AppIDs.
# 3. Parses the .lua files for all processed AppIDs to extract depot and key info.
# 4. Updates the GreenLuma 'AppList' by creating new .txt files for new AppIDs
#    and their associated depots.
# 5. Modifies Steam's 'config/config.vdf' file by injecting the new and updated
#    depot decryption keys. It creates a backup before writing.
# 6. Manages the Steam 'depotcache' folder by clearing its contents and copying
#    all .manifest files from the local 'data' directory into it.
#
# This script uses only standard Python libraries.

import configparser
import os
import re
import shutil
import time
import sys
import subprocess


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


# =============================================================================
# --- FILE MODIFICATION FUNCTIONS ---
# =============================================================================

def update_config_vdf(vdf_path, all_depots_to_apply):
    """
    Safely parses and updates the 'depots' section within Steam's config.vdf file.

    This function reads the VDF file as plain text because it's a non-standard
    Key-Value format. It finds the 'depots' block, parses its contents into a
    Python dictionary, updates this dictionary with the new data, and then
    reconstructs the block and writes the entire file back. This approach
    preserves all other data in the file.

    Args:
        vdf_path (str): The full path to Steam's config.vdf file.
        all_depots_to_apply (list): A list of depot dictionaries to add or update.
    """
    print(f"\nProcessing Steam config: {vdf_path}")
    if not os.path.exists(vdf_path):
        print("[Error] config.vdf not found at the specified path.")
        return

    # --- Step 1: Read the entire VDF file into memory ---
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[Error] Could not read config.vdf: {e}")
        return

    # --- Step 2: Find the "depots" section and parse its contents ---
    depots = {}
    in_depots_section = False
    depots_start_index, depots_end_index = -1, -1
    brace_level = 0
    depot_id_pattern = re.compile(r'^\s*"(\d+)"\s*$')
    key_pattern = re.compile(r'^\s*"DecryptionKey"\s*"([a-fA-F0-9]{64})"\s*$')

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

            # If a depot ID is found, check the next couple of lines for its key.
            id_match = depot_id_pattern.match(line)
            if id_match and i + 2 < len(lines):
                key_match = key_pattern.match(lines[i + 2])
                if key_match:
                    depots[id_match.group(1)] = key_match.group(1)

            # When brace level returns to 0, the section has ended.
            if brace_level == 0:
                depots_end_index = i
                break

    if depots_start_index == -1 or depots_end_index == -1:
        print("[Error] Could not find a valid 'depots' section in config.vdf.")
        return

    print(f"  Found {len(depots)} existing depot keys in config.vdf.")

    # --- Step 3: Update the depots dictionary with our new data ---
    update_count = 0
    for depot in all_depots_to_apply:
        depot_id, depot_key = depot['depot_id'], depot['depot_key']
        # Only count as an update if the key is new or different.
        if depots.get(depot_id) != depot_key:
            depots[depot_id] = depot_key
            update_count += 1

    if update_count == 0:
        print("  No new or different depot keys to apply to config.vdf.")
        return
    print(f"  Adding or updating {update_count} depot keys.")

    # --- Step 4: Reconstruct the "depots" section as a list of strings ---
    new_depots_lines = []
    base_indent = '\t' * 4  # Match Steam's indentation style.
    new_depots_lines.append(f'{base_indent}"depots"\n')
    new_depots_lines.append(f'{base_indent}{{\n')
    # Sort by Depot ID for a clean, consistent output.
    for depot_id, key in sorted(depots.items()):
        new_depots_lines.append(f'{base_indent}\t"{depot_id}"\n')
        new_depots_lines.append(f'{base_indent}\t{{\n')
        new_depots_lines.append(f'{base_indent}\t\t"DecryptionKey"\t\t"{key}"\n')
        new_depots_lines.append(f'{base_indent}\t}}\n')
    new_depots_lines.append(f'{base_indent}}}\n')

    # --- Step 5: Replace the old section with the new one ---
    final_lines = lines[:depots_start_index] + new_depots_lines + lines[depots_end_index + 1:]

    # --- Step 6: Backup the old file and write the new one ---
    try:
        backup_path = vdf_path + '.bak'
        print(f"  Backing up original config to {os.path.basename(backup_path)}")
        shutil.copy2(vdf_path, backup_path)
        print("  Writing updated config.vdf...")
        with open(vdf_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        print("  Successfully updated config.vdf.")
    except Exception as e:
        print(f"[Error] Failed to write updated config.vdf: {e}")

def update_greenluma_applist(gl_path, new_appids, new_depots):
    """
    Adds new AppIDs and their associated DepotIDs to the GreenLuma AppList folder.

    It works by finding the highest numbered existing .txt file and creating
    new files sequentially from that point. First, it writes all the new AppIDs,
    then it writes all the depots associated with those new AppIDs.

    Args:
        gl_path (str): The path to the main GreenLuma folder.
        new_appids (list): A list of AppID strings to add.
        new_depots (list): A list of depot dictionaries from the new apps.
    """
    print(f"\nProcessing GreenLuma AppList: {gl_path}")
    applist_dir = os.path.join(gl_path, 'NormalMode', 'AppList')
    if not os.path.isdir(applist_dir):
        print(f"[Error] GreenLuma AppList directory not found: {applist_dir}")
        return

    # Find the next available index for a new file.
    indices = [int(os.path.splitext(f)[0]) for f in os.listdir(applist_dir) if os.path.splitext(f)[0].isdigit() and f.endswith('.txt')]
    current_index = max(indices) + 1 if indices else 0
    print(f"  Found {len(indices)} existing entries. Starting new entries from index {current_index}.")

    # Write all new AppIDs to sequentially numbered files.
    if new_appids:
        print(f"  Writing {len(new_appids)} new AppIDs...")
        for app_id in new_appids:
            filepath = os.path.join(applist_dir, f"{current_index}.txt")
            try:
                with open(filepath, 'w', encoding='utf-8') as f: f.write(app_id)
                print(f"    - Created {os.path.basename(filepath)} with AppID: {app_id}")
                current_index += 1
            except Exception as e: print(f"[Error] Could not write file {filepath}: {e}")

    # Write all depots from those new apps to sequentially numbered files.
    new_depot_ids = [d['depot_id'] for d in new_depots]
    if new_depot_ids:
        print(f"  Writing {len(new_depot_ids)} new DepotIDs...")
        for depot_id in new_depot_ids:
            filepath = os.path.join(applist_dir, f"{current_index}.txt")
            try:
                with open(filepath, 'w', encoding='utf-8') as f: f.write(depot_id)
                print(f"    - Created {os.path.basename(filepath)} with DepotID: {depot_id}")
                current_index += 1
            except Exception as e: print(f"[Error] Could not write file {filepath}: {e}")

    print("  Finished updating GreenLuma AppList.")

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
    It reads configuration, parses data, and calls the appropriate
    file modification functions in sequence.
    """
    print("--- data.py has taken control ---")

    # --- Configuration and Data Loading ---
    app_config = configparser.ConfigParser()
    app_config.read('config.ini')
    steam_path = app_config.get('Paths', 'steam_path', fallback='')
    greenluma_path = app_config.get('Paths', 'greenluma_path', fallback='')

    data_config = configparser.ConfigParser()
    data_config.read('data.ini')
    new_appids_str = data_config.get('AppIDs', 'new', fallback='')
    updated_appids_str = data_config.get('AppIDs', 'updated', fallback='')
    new_appids = new_appids_str.split(',') if new_appids_str else []
    updated_appids = updated_appids_str.split(',') if updated_appids_str else []

    # --- Data Parsing ---
    # Use list comprehensions for a concise way to gather all depots.
    all_new_depots = [depot for app_id in new_appids for depot in parse_lua_for_depots(os.path.join('data', app_id, f"{app_id}.lua"))]
    all_updated_depots = [depot for app_id in updated_appids for depot in parse_lua_for_depots(os.path.join('data', app_id, f"{app_id}.lua"))]

    # --- Execution Step 1: Update GreenLuma ---
    if greenluma_path and os.path.isdir(greenluma_path):
        # Only new AppIDs and their depots are sent to the AppList.
        update_greenluma_applist(greenluma_path, new_appids, all_new_depots)
    else:
        print(f"\n[Warning] GreenLuma path '{greenluma_path}' is invalid. Skipping AppList update.")

    # --- Execution Step 2: Update Steam VDF ---
    all_depots_for_vdf = all_new_depots + all_updated_depots
    if steam_path and os.path.isdir(steam_path) and all_depots_for_vdf:
        config_vdf_path = os.path.join(steam_path, 'config', 'config.vdf')
        update_config_vdf(config_vdf_path, all_depots_for_vdf)

    # --- Execution Step 3: Manage Depot Cache ---
    if steam_path and os.path.isdir(steam_path):
        manage_depot_cache(steam_path)
    else:
        print(f"\n[Warning] Steam path '{steam_path}' is invalid. Skipping depotcache management.")

      # --- Final Step: Execute acfgen.py ---
    print("\nLaunching acfgen.py...")
    try:
        # Use Popen to launch the script in a new, non-blocking process.
        subprocess.Popen([sys.executable, "acfgen.py"])
        print("  Successfully launched acfgen.py.")
    except FileNotFoundError:
        print("  [Error] 'acfgen.py' not found in the script directory! Skipping.")
    except Exception as e:
        print(f"  [Error] Failed to launch acfgen.py: {e}")

    print("\n-------------------------------------------")
    print("Processing complete.")
    # Pause to allow the user to read the console output before the window closes.
    time.sleep(5)

if __name__ == "__main__":
    """
    Standard script entry point. Ensures that the `main()` function is only
    called when the script is executed directly, not when imported as a module.
    """
    main()

# Docs are generated by AI and may be inaccurate