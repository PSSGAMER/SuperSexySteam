# vdf_updater.py
#
# A standalone script for updating Steam's config.vdf file with depot decryption keys.
# This script reads an existing config.vdf file, merges in new depot keys, and writes
# the updated configuration back to disk using the VDF library.

from pathlib import Path
import shutil
import sys
import vdf
import logging

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


# =============================================================================
# --- VDF HELPER FUNCTION ---
# =============================================================================

def _get_steam_node(config):
    """
    Navigates through a loaded VDF dictionary to safely find the 'Steam' node.

    This helper centralizes the logic for accessing the nested key structure
    and handles case-insensitivity for 'Valve' and 'Steam' keys.

    Args:
        config (dict): The loaded VDF configuration dictionary.

    Returns:
        dict or None: The 'Steam' node dictionary if found, otherwise None.
    """

    # Navigate through the VDF structure: InstallConfigStore → Software → Valve → Steam
    if 'InstallConfigStore' not in config:
        logger.error("'InstallConfigStore' section not found in config.vdf")
        return None

    software = config['InstallConfigStore'].get('Software', {})

    valve = software.get('Valve') or software.get('valve')
    if not valve:
        logger.warning("'Valve' section not found in config.vdf")
        return None

    steam = valve.get('Steam') or valve.get('steam')
    if not steam:
        logger.warning("'Steam' section not found in config.vdf")
        return None

    return steam


# =============================================================================
# --- VDF UPDATE FUNCTIONS ---
# =============================================================================

def update_config_vdf(config_path, depot_keys, create_backup=True):
    """
    Updates Steam's config.vdf file by merging depot decryption keys using the VDF library.
    
    This function reads the existing config.vdf, navigates to the Steam depots section,
    and updates it with new depot keys, then writes the file back.

    Args:
        config_path (str or Path): The full path to Steam's config.vdf file.
        depot_keys (dict): Dictionary mapping depot_id to depot_key.
        create_backup (bool): Whether to create a backup of the original file.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    config_path = Path(config_path)
    logger.info(f"Processing Steam config: {config_path}")
    
    if not config_path.exists():
        logger.error("config.vdf not found at the specified path")
        return False

    if not depot_keys:
        logger.warning("No depot data provided. Skipping config.vdf update")
        return False

    try:
        # Load existing Steam config.vdf
        logger.debug("Reading existing config.vdf")
        with config_path.open('r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Get the Steam node using the helper function
        steam = _get_steam_node(config)
        if not steam:
            return False

        logger.info(f"Processing {len(depot_keys)} unique depot keys")

        # Ensure depots section exists, then merge in new keys
        steam.setdefault('depots', {})
        
        # Update depot keys
        for depot_id, depot_key in depot_keys.items():
            steam['depots'][depot_id] = {'DecryptionKey': depot_key}
            logger.debug(f"Added depot key for depot {depot_id}")

        # Backup original file if requested
        if create_backup:
            backup_path = config_path.with_suffix(config_path.suffix + '.bak')
            logger.debug(f"Backing up original config to {backup_path.name}")
            shutil.copy2(config_path, backup_path)

        # Write the updated VDF back to disk
        logger.debug("Writing updated config.vdf")
        with config_path.open('w', encoding='utf-8') as f:
            vdf.dump(config, f, pretty=True)

        logger.info(f"Successfully updated config.vdf with {len(depot_keys)} depot keys")
        return True

    except Exception as e:
        logger.error(f"Failed to update config.vdf: {e}")
        logger.debug("Config.vdf update error details:", exc_info=True)
        return False


def validate_config_vdf(config_path):
    """
    Validates that a config.vdf file exists and has the expected structure.

    Args:
        config_path (str or Path): The full path to Steam's config.vdf file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    config_path = Path(config_path)
    logger.info(f"Validating config.vdf: {config_path}")
    
    if not config_path.exists():
        logger.error("config.vdf not found at the specified path")
        return False

    try:
        with config_path.open('r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Check for required structure using the helper
        steam = _get_steam_node(config)
        if not steam:
            return False

        depots_count = len(steam.get('depots', {}))
        logger.info(f"Valid config.vdf with {depots_count} existing depot entries")
        
        return True

    except Exception as e:
        logger.error(f"Failed to validate config.vdf: {e}")
        logger.debug("Config.vdf validation error details:", exc_info=True)
        return False


def get_existing_depot_keys(config_path):
    """
    Reads existing depot keys from a config.vdf file.

    Args:
        config_path (str or Path): The full path to Steam's config.vdf file.

    Returns:
        dict: Dictionary mapping depot_id to depot_key, or empty dict on error.
    """
    config_path = Path(config_path)
    existing_keys = {}
    logger.debug(f"Reading existing depot keys from {config_path}")
    
    try:
        with config_path.open('r', encoding='utf-8') as f:
            config = vdf.load(f)

        steam = _get_steam_node(config)
        if not steam:
            return existing_keys

        depots = steam.get('depots', {})
        
        for depot_id, depot_data in depots.items():
            if isinstance(depot_data, dict) and 'DecryptionKey' in depot_data:
                existing_keys[depot_id] = depot_data['DecryptionKey']
        
        logger.info(f"Found {len(existing_keys)} existing depot keys")
        
    except Exception as e:
        logger.error(f"Failed to read existing depot keys: {e}")
        logger.debug("Get existing depot keys error details:", exc_info=True)
    
    return existing_keys


def add_depots_to_config_vdf(config_path, depots, create_backup=True):
    """
    Add depot decryption keys to Steam's config.vdf file.
    
    Args:
        config_path (str or Path): The full path to Steam's config.vdf file
        depots (list): List of depot dictionaries with 'depot_id' and 'depot_key'
        create_backup (bool): Whether to create a backup of the original file
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    config_path = Path(config_path)
    logger.info(f"Adding depots to Steam config: {config_path}")
    
    if not config_path.exists():
        logger.error("config.vdf not found at the specified path")
        return False

    if not depots:
        logger.warning("No depot data provided. Skipping config.vdf update")
        return True  # No depots to add is considered success

    try:
        # Convert depots list to dictionary format
        depot_keys = {}
        for depot in depots:
            if 'depot_key' in depot:
                depot_keys[depot['depot_id']] = depot['depot_key']
        
        if not depot_keys:
            logger.info("No depot keys to add to config.vdf")
            return True
        
        # Use existing update function
        return update_config_vdf(config_path, depot_keys, create_backup)
        
    except Exception as e:
        logger.error(f"Failed to add depots to config.vdf: {e}")
        logger.debug("Add depots to config.vdf error details:", exc_info=True)
        return False


def remove_depots_from_config_vdf(config_path, depots, create_backup=True):
    """
    Remove depot decryption keys from Steam's config.vdf file.
    
    Args:
        config_path (str or Path): The full path to Steam's config.vdf file
        depots (list): List of depot dictionaries with 'depot_id'
        create_backup (bool): Whether to create a backup of the original file
        
    Returns:
        bool: True if the removal was successful, False otherwise
    """
    config_path = Path(config_path)
    logger.info(f"Removing depots from Steam config: {config_path}")
    
    if not config_path.exists():
        logger.error("config.vdf not found at the specified path")
        return False

    if not depots:
        logger.warning("No depot data provided. Skipping config.vdf update")
        return True  # No depots to remove is considered success

    try:
        # Load existing Steam config.vdf
        logger.debug("Reading existing config.vdf")
        with config_path.open('r', encoding='utf-8') as f:
            config = vdf.load(f)

        # Navigate through the VDF structure using the helper
        steam = _get_steam_node(config)
        if not steam:
            return True # Nothing to remove is considered success

        # Check if depots section exists
        if 'depots' not in steam:
            logger.info("No depots section found in config.vdf")
            return True  # Nothing to remove

        # Remove depot keys
        removed_count = 0
        depot_ids_to_remove = {depot['depot_id'] for depot in depots}

        for depot_id in list(steam['depots'].keys()): # Iterate over a copy of keys
            if depot_id in depot_ids_to_remove:
                del steam['depots'][depot_id]
                removed_count += 1
                logger.debug(f"Removed depot key for {depot_id}")

        if removed_count == 0:
            logger.info("No matching depot keys found to remove")
            return True

        # Backup original file if requested
        if create_backup:
            backup_path = config_path.with_suffix(config_path.suffix + '.bak')
            logger.debug(f"Backing up original config to {backup_path.name}")
            shutil.copy2(config_path, backup_path)

        # Write the updated VDF back to disk
        logger.debug("Writing updated config.vdf")
        with config_path.open('w', encoding='utf-8') as f:
            vdf.dump(config, f, pretty=True)

        logger.info(f"Successfully removed {removed_count} depot keys from config.vdf")
        return True

    except Exception as e:
        logger.error(f"Failed to remove depots from config.vdf: {e}")
        logger.debug("Remove depots from config.vdf error details:", exc_info=True)
        return False


# =============================================================================
# --- MAIN EXECUTION ---
# =============================================================================

def main():
    """
    Main function for standalone execution.
    Validates a config.vdf file and optionally displays existing depot keys.
    """
    logger.info("vdf_updater.py: Steam config.vdf management")
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python vdf_updater.py <config_vdf_path> [--show-keys]")
        logger.error("Example: python vdf_updater.py \"C:\\Steam\\config\\config.vdf\"")
        return
    
    config_path = Path(sys.argv[1])
    show_keys = '--show-keys' in sys.argv
    
    # Validate the config file
    if not validate_config_vdf(config_path):
        logger.error("config.vdf validation failed")
        return
    
    logger.info("config.vdf is valid")
    
    # Optionally show existing depot keys
    if show_keys:
        existing_keys = get_existing_depot_keys(config_path)
        if existing_keys:
            logger.info(f"Existing depot keys (showing first 10):")
            for i, (depot_id, depot_key) in enumerate(list(existing_keys.items())[:10]):
                logger.info(f"  {depot_id}: {depot_key}")
            if len(existing_keys) > 10:
                logger.info(f"  ... and {len(existing_keys) - 10} more")
        else:
            logger.info("No existing depot keys found")


