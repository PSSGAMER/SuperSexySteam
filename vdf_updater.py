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
# --- VDF HELPER FUNCTION ---
# =============================================================================

def _get_steam_node(config, verbose=True):
    """
    Navigates through a loaded VDF dictionary to safely find the 'Steam' node.

    This helper centralizes the logic for accessing the nested key structure
    and handles case-insensitivity for 'Valve' and 'Steam' keys.

    Args:
        config (dict): The loaded VDF configuration dictionary.
        verbose (bool): Whether to print error/warning messages.

    Returns:
        dict or None: The 'Steam' node dictionary if found, otherwise None.
    """

    # Navigate through the VDF structure: InstallConfigStore → Software → Valve → Steam
    if 'InstallConfigStore' not in config:
        if verbose:
            print("[Error] 'InstallConfigStore' section not found in config.vdf")
        return None

    software = config['InstallConfigStore'].get('Software', {})

    valve = software.get('Valve') or software.get('valve')
    if not valve:
        if verbose:
            print("[Warning] 'Valve' section not found in config.vdf")
        return None

    steam = valve.get('Steam') or valve.get('steam')
    if not steam:
        if verbose:
            print("[Warning] 'Steam' section not found in config.vdf")
        return None

    return steam


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

        # Get the Steam node using the helper function
        steam = _get_steam_node(config, verbose)
        if not steam:
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

        # Check for required structure using the helper
        steam = _get_steam_node(config, verbose)
        if not steam:
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

        steam = _get_steam_node(config, verbose=False) # No need for verbose output here
        if not steam:
            return existing_keys

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


def add_depots_to_config_vdf(config_path, depots, create_backup=True, verbose=True):
    """
    Add depot decryption keys to Steam's config.vdf file.
    
    Args:
        config_path (str): The full path to Steam's config.vdf file
        depots (list): List of depot dictionaries with 'depot_id' and 'depot_key'
        create_backup (bool): Whether to create a backup of the original file
        verbose (bool): Whether to print progress information
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    if verbose:
        print(f"Adding depots to Steam config: {config_path}")
    
    if not os.path.exists(config_path):
        if verbose:
            print("[Error] config.vdf not found at the specified path.")
        return False

    if not depots:
        if verbose:
            print("[Warning] No depot data provided. Skipping config.vdf update.")
        return True  # No depots to add is considered success

    try:
        # Convert depots list to dictionary format
        depot_keys = {}
        for depot in depots:
            if 'depot_key' in depot:
                depot_keys[depot['depot_id']] = depot['depot_key']
        
        if not depot_keys:
            if verbose:
                print("[Info] No depot keys to add to config.vdf")
            return True
        
        # Use existing update function
        return update_config_vdf(config_path, depot_keys, create_backup, verbose)
        
    except Exception as e:
        if verbose:
            print(f"[Error] Failed to add depots to config.vdf: {e}")
        return False


def remove_depots_from_config_vdf(config_path, depots, create_backup=True, verbose=True):
    """
    Remove depot decryption keys from Steam's config.vdf file.
    
    Args:
        config_path (str): The full path to Steam's config.vdf file
        depots (list): List of depot dictionaries with 'depot_id'
        create_backup (bool): Whether to create a backup of the original file
        verbose (bool): Whether to print progress information
        
    Returns:
        bool: True if the removal was successful, False otherwise
    """
    if verbose:
        print(f"Removing depots from Steam config: {config_path}")
    
    if not os.path.exists(config_path):
        if verbose:
            print("[Error] config.vdf not found at the specified path.")
        return False

    if not depots:
        if verbose:
            print("[Warning] No depot data provided. Skipping config.vdf update.")
        return True  # No depots to remove is considered success

    try:
        # Load existing Steam config.vdf
        if verbose:
            print("  Reading existing config.vdf...")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Navigate through the VDF structure using the helper
        steam = _get_steam_node(config, verbose)
        if not steam:
            return True # Nothing to remove is considered success

        # Check if depots section exists
        if 'depots' not in steam:
            if verbose:
                print("[Info] No depots section found in config.vdf")
            return True  # Nothing to remove

        # Remove depot keys
        removed_count = 0
        depot_ids_to_remove = {depot['depot_id'] for depot in depots}

        for depot_id in list(steam['depots'].keys()): # Iterate over a copy of keys
            if depot_id in depot_ids_to_remove:
                del steam['depots'][depot_id]
                removed_count += 1
                if verbose:
                    print(f"  - Removed depot key for {depot_id}")

        if removed_count == 0:
            if verbose:
                print("[Info] No matching depot keys found to remove")
            return True

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
            print(f"  Successfully removed {removed_count} depot keys from config.vdf")
        return True

    except Exception as e:
        if verbose:
            print(f"[Error] Failed to remove depots from config.vdf: {e}")
        return False


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