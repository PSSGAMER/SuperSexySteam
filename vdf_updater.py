# vdf_updater.py
#
# A standalone script for updating Steam's config.vdf file with depot decryption keys.
# This script reads an existing config.vdf file, merges in new depot keys, and writes
# the updated configuration back to disk using the VDF library.

import os
import shutil
import sys
import vdf


# =============================================================================
# --- VDF UPDATE FUNCTIONS ---
# =============================================================================

def update_config_vdf(config_path, depot_keys, create_backup=True, verbose=True):
    """
    Updates Steam's config.vdf file by merging depot decryption keys using the VDF library.
    
    This function reads the existing config.vdf, navigates to the Steam depots section,
    and updates it with new depot keys, then writes the file back.

    Args:
        config_path (str): The full path to Steam's config.vdf file.
        depot_keys (dict): Dictionary mapping depot_id to depot_key.
        create_backup (bool): Whether to create a backup of the original file.
        verbose (bool): Whether to print progress information.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    if verbose:
        print(f"Processing Steam config: {config_path}")
    
    if not os.path.exists(config_path):
        if verbose:
            print("[Error] config.vdf not found at the specified path.")
        return False

    if not depot_keys:
        if verbose:
            print("[Warning] No depot data provided. Skipping config.vdf update.")
        return False

    try:
        # Load existing Steam config.vdf
        if verbose:
            print("  Reading existing config.vdf...")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Navigate through the VDF structure: InstallConfigStore → Software → Valve → Steam
        if 'InstallConfigStore' not in config:
            if verbose:
                print("[Error] InstallConfigStore section not found in config.vdf")
            return False
            
        software = config['InstallConfigStore']['Software']
        
        # Handle case-insensitive keys for Valve
        valve = software.get('Valve') or software.get('valve')
        if not valve:
            if verbose:
                print("[Error] Valve section not found in config.vdf")
            return False
            
        # Handle case-insensitive keys for Steam
        steam = valve.get('Steam') or valve.get('steam')
        if not steam:
            if verbose:
                print("[Error] Steam section not found in config.vdf")
            return False

        if verbose:
            print(f"  Processing {len(depot_keys)} unique depot keys...")

        # Ensure depots section exists, then merge in new keys
        steam.setdefault('depots', {})
        
        # Update depot keys
        for depot_id, depot_key in depot_keys.items():
            steam['depots'][depot_id] = {'DecryptionKey': depot_key}

        # Backup original file if requested
        if create_backup:
            backup_path = config_path + '.bak'
            if verbose:
                print(f"  Backing up original config to {os.path.basename(backup_path)}")
            shutil.copy2(config_path, backup_path)

        # Write the updated VDF back to disk
        if verbose:
            print("  Writing updated config.vdf...")
        with open(config_path, 'w', encoding='utf-8') as f:
            vdf.dump(config, f, pretty=True)

        if verbose:
            print(f"  Successfully updated config.vdf with {len(depot_keys)} depot keys.")
        return True

    except Exception as e:
        if verbose:
            print(f"[Error] Failed to update config.vdf: {e}")
        return False


def validate_config_vdf(config_path, verbose=True):
    """
    Validates that a config.vdf file exists and has the expected structure.

    Args:
        config_path (str): The full path to Steam's config.vdf file.
        verbose (bool): Whether to print validation information.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    if verbose:
        print(f"Validating config.vdf: {config_path}")
    
    if not os.path.exists(config_path):
        if verbose:
            print("[Error] config.vdf not found at the specified path.")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Check for required structure
        if 'InstallConfigStore' not in config:
            if verbose:
                print("[Error] InstallConfigStore section not found")
            return False
            
        software = config['InstallConfigStore']['Software']
        valve = software.get('Valve') or software.get('valve')
        if not valve:
            if verbose:
                print("[Error] Valve section not found")
            return False
            
        steam = valve.get('Steam') or valve.get('steam')
        if not steam:
            if verbose:
                print("[Error] Steam section not found")
            return False

        if verbose:
            depots_count = len(steam.get('depots', {}))
            print(f"  Valid config.vdf with {depots_count} existing depot entries")
        
        return True

    except Exception as e:
        if verbose:
            print(f"[Error] Failed to validate config.vdf: {e}")
        return False


def get_existing_depot_keys(config_path, verbose=True):
    """
    Reads existing depot keys from a config.vdf file.

    Args:
        config_path (str): The full path to Steam's config.vdf file.
        verbose (bool): Whether to print information.

    Returns:
        dict: Dictionary mapping depot_id to depot_key, or empty dict on error.
    """
    existing_keys = {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = vdf.load(f)

        software = config['InstallConfigStore']['Software']
        valve = software.get('Valve') or software.get('valve')
        steam = valve.get('Steam') or valve.get('steam')
        depots = steam.get('depots', {})
        
        for depot_id, depot_data in depots.items():
            if isinstance(depot_data, dict) and 'DecryptionKey' in depot_data:
                existing_keys[depot_id] = depot_data['DecryptionKey']
        
        if verbose:
            print(f"Found {len(existing_keys)} existing depot keys")
        
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to read existing depot keys: {e}")
    
    return existing_keys


def update_config_vdf_for_appids(config_path, appids, data_dir='data', create_backup=True, verbose=True):
    """
    Updates Steam's config.vdf file with depot keys from specific AppIDs only.
    
    This function parses lua files for the given AppIDs, extracts depot keys,
    and updates the config.vdf file with only those keys.

    Args:
        config_path (str): The full path to Steam's config.vdf file.
        appids (list): List of AppID strings to process.
        data_dir (str): Directory containing the AppID folders with lua files.
        create_backup (bool): Whether to create a backup of the original file.
        verbose (bool): Whether to print progress information.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    if verbose:
        print(f"Processing Steam config for AppIDs: {', '.join(appids)}")
    
    if not os.path.exists(config_path):
        if verbose:
            print("[Error] config.vdf not found at the specified path.")
        return False

    if not appids:
        if verbose:
            print("[Warning] No AppIDs provided. Skipping config.vdf update.")
        return False

    # Import lua_parser to extract depot keys from lua files
    from lua_parser import parse_lua_for_depots
    
    # Collect depot keys from the specified AppIDs
    depot_keys = {}
    processed_count = 0
    
    for app_id in appids:
        lua_path = os.path.join(data_dir, app_id, f"{app_id}.lua")
        if os.path.exists(lua_path):
            depots = parse_lua_for_depots(lua_path)
            for depot in depots:
                if 'depot_key' in depot and depot['depot_key']:
                    depot_keys[depot['depot_id']] = depot['depot_key']
            processed_count += 1
            if verbose:
                print(f"  Processed AppID {app_id}: found {len(depots)} depots")
        else:
            if verbose:
                print(f"  [Warning] Lua file not found for AppID {app_id}: {lua_path}")
    
    if not depot_keys:
        if verbose:
            print("[Warning] No depot keys found in the specified AppIDs.")
        return False
    
    if verbose:
        print(f"  Collected {len(depot_keys)} depot keys from {processed_count} AppIDs")
    
    # Use the existing update_config_vdf function
    return update_config_vdf(config_path, depot_keys, create_backup, verbose)

# =============================================================================
# --- MAIN EXECUTION ---
# =============================================================================

def main():
    """
    Main function for standalone execution.
    Validates a config.vdf file and optionally displays existing depot keys.
    """
    print("--- vdf_updater.py: Steam config.vdf management ---")
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python vdf_updater.py <config_vdf_path> [--show-keys]")
        print("Example: python vdf_updater.py \"C:\\Steam\\config\\config.vdf\"")
        return
    
    config_path = sys.argv[1]
    show_keys = '--show-keys' in sys.argv
    
    # Validate the config file
    if not validate_config_vdf(config_path):
        print("[Error] config.vdf validation failed.")
        return
    
    print("[Success] config.vdf is valid.")
    
    # Optionally show existing depot keys
    if show_keys:
        existing_keys = get_existing_depot_keys(config_path)
        if existing_keys:
            print(f"\nExisting depot keys (showing first 10):")
            for i, (depot_id, depot_key) in enumerate(list(existing_keys.items())[:10]):
                print(f"  {depot_id}: {depot_key}")
            if len(existing_keys) > 10:
                print(f"  ... and {len(existing_keys) - 10} more")
        else:
            print("\nNo existing depot keys found.")


if __name__ == "__main__":
    """
    Standard script entry point. Ensures that the `main()` function is only
    called when the script is executed directly, not when imported as a module.
    """
    main()
