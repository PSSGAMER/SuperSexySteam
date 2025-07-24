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
import sys
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

    This function uses a proper VDF parser that correctly handles the hierarchical
    structure and indentation of Steam's VDF format.

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

    # --- Step 2: Parse VDF structure and find depots section ---
    depots_start_index, depots_end_index = -1, -1
    current_indent_level = 0
    depots_indent_level = -1
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Count current indentation level by counting leading tabs
        line_indent = len(line) - len(line.lstrip('\t'))
        
        # Handle opening braces (increase nesting level)
        if stripped == '{':
            current_indent_level += 1
        # Handle closing braces (decrease nesting level)
        elif stripped == '}':
            # If we're ending the depots section
            if depots_indent_level != -1 and current_indent_level == depots_indent_level:
                depots_end_index = i
                break
            current_indent_level -= 1
        # Look for depots section start
        elif stripped.startswith('"depots"') and depots_start_index == -1:
            depots_start_index = i
            depots_indent_level = current_indent_level
            
            # Find the opening brace for depots section
            j = i + 1
            while j < len(lines) and lines[j].strip() != '{':
                j += 1
            if j < len(lines):
                current_indent_level += 1
                i = j  # Skip to the opening brace
        
        i += 1

    # --- Step 3: Determine insertion point and indentation ---
    # Find the Steam section to determine proper indentation
    steam_indent_level = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"Steam"'):
            steam_indent_level = len(line) - len(line.lstrip('\t'))
            break
    
    # Depots should be at the same level as other Steam config entries
    depots_base_indent = '\t' * (steam_indent_level + 1)
    
    # --- Step 4: Build the new depots section ---
    print(f"  Building new depots section with {len(all_depots)} depot keys...")
    
    # Convert list to dictionary to eliminate duplicates (last key wins)
    depots_dict = {}
    for depot in all_depots:
        depots_dict[depot['depot_id']] = depot['depot_key']
    
    new_depots_lines = []
    new_depots_lines.append(f'{depots_base_indent}"depots"\n')
    new_depots_lines.append(f'{depots_base_indent}{{\n')
    
    # Sort by Depot ID for consistent output
    for depot_id, key in sorted(depots_dict.items(), key=lambda x: int(x[0])):
        new_depots_lines.append(f'{depots_base_indent}\t"{depot_id}"\n')
        new_depots_lines.append(f'{depots_base_indent}\t{{\n')
        new_depots_lines.append(f'{depots_base_indent}\t\t"DecryptionKey"\t\t"{key}"\n')
        new_depots_lines.append(f'{depots_base_indent}\t}}\n')
    new_depots_lines.append(f'{depots_base_indent}}}\n')

    # --- Step 5: Replace or insert the depots section ---
    if depots_start_index != -1 and depots_end_index != -1:
        # Replace existing section
        print("  Replacing existing depots section...")
        final_lines = lines[:depots_start_index] + new_depots_lines + lines[depots_end_index + 1:]
    else:
        # Insert new section within the Steam section
        print("  No existing depots section found. Adding new section...")
        
        # Find the end of the Steam section to insert before it
        steam_section_end = -1
        brace_count = 0
        in_steam_section = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"Steam"'):
                in_steam_section = True
                continue
            
            if in_steam_section:
                if stripped == '{':
                    brace_count += 1
                elif stripped == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        steam_section_end = i
                        break
        
        if steam_section_end != -1:
            # Insert before the closing brace of the Steam section
            final_lines = lines[:steam_section_end] + new_depots_lines + lines[steam_section_end:]
        else:
            # Fallback: insert near the end of the file
            print("  [Warning] Could not find Steam section end. Using fallback insertion.")
            insert_index = len(lines) - 2  # Before the last closing brace
            final_lines = lines[:insert_index] + new_depots_lines + lines[insert_index:]

    # --- Step 6: Backup and write the new file ---
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

    # Handle console window visibility based on debug setting
    debug_mode = app_config.getboolean('Debug', 'show_console', fallback=False)
    if not debug_mode and sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass  # Silently ignore if hiding console fails

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