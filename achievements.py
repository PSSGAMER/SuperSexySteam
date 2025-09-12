
# achievements.py
#
# A standalone script to fetch achievement schemas for Steam games from the database.
# This script reads the SuperSexySteam database, finds all games that need achievement
# schema generation (achievements_generated = false), logs into Steam, and downloads 
# 'UserGameStatsSchema' for those App IDs. After successful processing, it marks
# the games as processed in the database (achievements_generated = true).
#
# Works around ownership requirements by trying multiple public Steam profiles.
#
# The script saves files to two locations:
# 1. UserGameStatsSchema files: Saved to both schema_output/ (backup) and Steam's appcache/stats/
# 2. UserGameStats templates: Copied to Steam's appcache/stats/ directory
#
# Both file types are needed by Steam emulators for achievement functionality.
#
# Usage:
#   python achievements.py                         # Process all unprocessed games from database
#   python achievements.py -appid 123 456 789     # Process specific App IDs manually
#   python achievements.py --delete-credentials    # Delete stored login credentials
#   python achievements.py --show-stored-user      # Show currently stored username

import sys
import logging
import keyring
import shutil
import configparser
from pathlib import Path
from typing import List, Optional, Tuple
from steam.client import SteamClient
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto
from database_manager import GameDatabaseManager
from app_logic import SuperSexySteamLogic

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# --- CONFIGURATION ---
# =============================================================================

# A hardcoded list of Steam IDs with public profiles that own a lot of games.
# This increases the chance of finding a schema for a game you don't own.
TOP_OWNER_IDS = [
    76561198028121353, 76561197979911851, 76561198017975643,
    76561197993544755, 76561198355953202, 76561198001237877,
    76561198237402290, 76561198152618007, 76561198355625888,
    76561198213148949, 76561197969050296, 76561198217186687,
    76561198037867621, 76561198094227663, 76561198019712127,
    76561197963550511, 76561198134044398, 76561198001678750,
    76561197973009892, 76561198044596404, 76561197976597747,
    76561197969810632, 76561198095049646, 76561198085065107,
    76561198864213876, 76561197962473290, 76561198388522904,
    76561198033715344, 76561197995070100, 76561198313790296,
    76561198063574735, 76561197996432822, 76561197976968076,
    76561198281128349, 76561198154462478, 76561198027233260,
    76561198842864763, 76561198010615256, 76561198035900006,
    76561198122859224, 76561198235911884, 76561198027214426,
    76561197970825215, 76561197968410781, 76561198104323854,
    76561198001221571, 76561198256917957, 76561198008181611,
    76561198407953371, 76561198062901118,
]


# =============================================================================
# --- CREDENTIAL MANAGEMENT ---
# =============================================================================

def get_stored_credentials(username: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve stored Steam credentials from Windows keyring.
    
    Args:
        username: Specific username to retrieve, or None to get the last used username
        
    Returns:
        Tuple of (username, password) or (None, None) if not found
    """
    try:
        # If no username provided, try to get the last used username
        if username is None:
            try:
                username = keyring.get_password("SuperSexySteam", "last_username")
            except Exception as e:
                logger.debug(f"Failed to get last username: {e}")
                return None, None
                
            if username is None:
                return None, None
        
        # Get the password for the username
        try:
            password = keyring.get_password("SuperSexySteam", username)
        except Exception as e:
            logger.debug(f"Failed to get password for user {username}: {e}")
            return username, None
            
        if password is None:
            return username, None
            
        logger.debug(f"Retrieved stored credentials for user: {username}")
        return username, password
        
    except Exception as e:
        logger.debug(f"Failed to retrieve stored credentials: {e}")
        return None, None


def store_credentials(username: str, password: str) -> bool:
    """
    Store Steam credentials in Windows keyring.
    
    Args:
        username: Steam username
        password: Steam password
        
    Returns:
        True if stored successfully, False otherwise
    """
    try:
        # Validate input
        if not username or not password:
            logger.error("Username and password cannot be empty")
            return False
            
        # Store the username and password
        keyring.set_password("SuperSexySteam", username, password)
        logger.debug(f"Stored password for user: {username}")
        
        # Store the last used username
        keyring.set_password("SuperSexySteam", "last_username", username)
        logger.debug(f"Set last_username to: {username}")
        
        logger.debug(f"Stored credentials for user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        return False


def delete_stored_credentials(username: str = None) -> bool:
    """
    Delete stored Steam credentials from Windows keyring.
    
    Args:
        username: Username to delete, or None to delete the last used username
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Get the last username before any deletion if no username provided
        if username is None:
            username = keyring.get_password("SuperSexySteam", "last_username")
            if username is None:
                logger.info("No stored credentials found to delete")
                return True
        
        # Get the last username to compare (before deletion)
        last_username = None
        try:
            last_username = keyring.get_password("SuperSexySteam", "last_username")
        except Exception:
            pass  # Ignore if last_username doesn't exist
        
        # Delete the password for the user
        try:
            keyring.delete_password("SuperSexySteam", username)
            logger.debug(f"Deleted password for user: {username}")
        except Exception as e:
            logger.debug(f"Password for user {username} may not exist: {e}")
        
        # Delete the last username reference if it matches
        if last_username == username:
            try:
                keyring.delete_password("SuperSexySteam", "last_username")
                logger.debug("Deleted last_username reference")
            except Exception as e:
                logger.debug(f"Last username reference may not exist: {e}")
            
        logger.info(f"Deleted stored credentials for user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete credentials: {e}")
        return False


# =============================================================================
# --- CORE FUNCTIONS ---
# =============================================================================

def get_stats_schema(client: SteamClient, game_id: int, owner_id: int) -> Optional[any]:
    """
    Sends a request to Steam to get the UserGameStatsSchema for a specific game.
    
    Args:
        client: Active Steam client connection
        game_id: Steam App ID to get schema for
        owner_id: Steam ID of user who owns the game
        
    Returns:
        Steam response message if successful, None otherwise
    """
    logger.debug(f"Requesting stats schema for game {game_id} using owner {owner_id}")
    
    # Create the protobuf message for the request
    message = MsgProto(EMsg.ClientGetUserStats)
    message.body.game_id = game_id
    message.body.steam_id_for_user = owner_id
    # These fields are typically set this way to request the full schema
    message.body.schema_local_version = -1
    message.body.crc_stats = 0

    # Send the message and wait for a response
    client.send(message)
    # Wait for the specific response message, with a 5-second timeout
    return client.wait_msg(EMsg.ClientGetUserStatsResponse, timeout=5)

def parse_arguments() -> List[int]:
    """
    Parse command line arguments for credential management commands and manual App ID specification.
    
    Returns:
        List of App IDs if manually specified, empty list if they should come from database
        
    Raises:
        SystemExit: If credential management command executed or invalid arguments
    """
    if len(sys.argv) >= 2:
        # Handle credential management commands
        if sys.argv[1] == "--delete-credentials":
            print("Deleting stored credentials...")
            if delete_stored_credentials():
                print("Stored credentials deleted successfully")
            else:
                print("Failed to delete stored credentials or no credentials found")
            sys.exit(0)
        
        if sys.argv[1] == "--show-stored-user":
            stored_username, _ = get_stored_credentials()
            if stored_username:
                print(f"Stored username: {stored_username}")
            else:
                print("No stored credentials found")
            sys.exit(0)
        
        # Handle manual App ID specification
        if sys.argv[1] == "-appid":
            if len(sys.argv) < 3:
                print("Error: -appid requires at least one App ID")
                print("Usage: python achievements.py -appid 123 456 789")
                sys.exit(1)
            
            appids = []
            for appid_str in sys.argv[2:]:
                try:
                    appid = int(appid_str)
                    if appid <= 0:
                        print(f"Error: Invalid App ID '{appid_str}' - must be a positive integer")
                        sys.exit(1)
                    appids.append(appid)
                except ValueError:
                    print(f"Error: Invalid App ID '{appid_str}' - must be a valid integer")
                    sys.exit(1)
            
            print(f"Manual mode: Processing specified App IDs: {appids}")
            return appids
        
        # Warn about deprecated usage for other arguments
        if sys.argv[1] not in ["--delete-credentials", "--show-stored-user", "-appid"]:
            print("Note: App IDs are now automatically read from the database.")
            print("For manual App ID specification, use: python achievements.py -appid 123 456 789")
            print("The script will process all games that need achievement schemas from the database.")
            print()

    # Return empty list - App IDs will come from database
    return []


def get_appids_from_database(db_manager: GameDatabaseManager) -> List[int]:
    """
    Get App IDs from database that need achievement schema generation.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        List of App IDs as integers that need achievement processing
    """
    logger.info("Reading App IDs from database that need achievement processing...")
    
    try:
        appid_strings = db_manager.get_appids_without_achievements()
        
        if not appid_strings:
            logger.info("No App IDs found that need achievement processing")
            return []
        
        # Convert string App IDs to integers
        appids = []
        for appid_str in appid_strings:
            try:
                appid = int(appid_str)
                appids.append(appid)
                logger.debug(f"Added App ID from database: {appid}")
            except ValueError:
                logger.warning(f"Invalid App ID in database: {appid_str}. Skipping.")
        
        logger.info(f"Found {len(appids)} App ID(s) needing achievement processing: {appids}")
        return appids
        
    except Exception as e:
        logger.error(f"Failed to read App IDs from database: {e}")
        return []


def authenticate_steam() -> SteamClient:
    """
    Handle Steam authentication with user credentials.
    Uses stored credentials from Windows keyring if available.
    
    Returns:
        Authenticated Steam client
        
    Raises:
        SystemExit: If authentication fails
    """
    client = SteamClient()
    
    # Try to get stored credentials first
    stored_username, stored_password = get_stored_credentials()
    
    if stored_username and stored_password:
        print(f"Found stored credentials for: {stored_username}")
        use_stored = input("Use stored credentials? (Y/n): ").strip().lower()
        
        if use_stored in ('', 'y', 'yes'):
            username = stored_username
            password = stored_password
            logger.info("Using stored credentials")
        else:
            # User chose not to use stored credentials
            username = input("Enter Steam username: ").strip()
            password = input("Enter Steam password: ")
            
            # Ask if they want to store the new credentials
            if username and password:
                store_creds = input("Store these credentials for future use? (Y/n): ").strip().lower()
                if store_creds in ('', 'y', 'yes'):
                    if store_credentials(username, password):
                        print("Credentials stored successfully")
                    else:
                        print("Failed to store credentials")
    else:
        # No stored credentials, ask for them
        print("No stored credentials found")
        username = input("Enter Steam username: ").strip()
        password = input("Enter Steam password: ")
        
        # Ask if they want to store the credentials
        if username and password:
            store_creds = input("Store credentials for future use? (Y/n): ").strip().lower()
            if store_creds in ('', 'y', 'yes'):
                if store_credentials(username, password):
                    print("Credentials stored successfully")
                else:
                    print("Failed to store credentials")

    if not username or not password:
        logger.error("Username and password are required")
        sys.exit(1)

    logger.info("Attempting Steam authentication...")
    try:
        client.cli_login(username, password)
        
        if not client.logged_on:
            logger.error("Steam authentication failed - please check credentials and Steam Guard")
            # If authentication failed and we used stored credentials, offer to delete them
            if stored_username and stored_password and username == stored_username:
                delete_creds = input("Delete stored credentials? (y/N): ").strip().lower()
                if delete_creds in ('y', 'yes'):
                    delete_stored_credentials(username)
            sys.exit(1)
            
        logger.info(f"Successfully authenticated as: {client.user.name}")
        return client
        
    except Exception as e:
        logger.error(f"Steam authentication error: {e}")
        # If authentication failed and we used stored credentials, offer to delete them
        if stored_username and stored_password and username == stored_username:
            delete_creds = input("Delete stored credentials? (y/N): ").strip().lower()
            if delete_creds in ('y', 'yes'):
                delete_stored_credentials(username)
        sys.exit(1)


def setup_output_directory() -> Path:
    """
    Create and return the output directory for schema files.
    
    Returns:
        Path to the output directory
    """
    output_dir = Path("schema_output")
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Schema files will be saved to: {output_dir.absolute()}")
    return output_dir


def fetch_schema_for_appid(client: SteamClient, appid: int, all_owner_ids: List[int]) -> Optional[any]:
    """
    Try to fetch achievement schema for a specific App ID using multiple owner IDs.
    
    Args:
        client: Authenticated Steam client
        appid: Steam App ID to fetch schema for
        all_owner_ids: List of Steam IDs to try as owners
        
    Returns:
        Schema response if found, None otherwise
    """
    logger.info(f"Processing App ID: {appid}")
    
    for owner_id in all_owner_ids:
        logger.debug(f"Trying owner ID: {owner_id}")
        try:
            response = get_stats_schema(client, appid, owner_id)
            # A successful response has a schema with a non-zero length
            if response and len(response.body.schema) > 0:
                logger.info(f"Found schema for App ID {appid} using owner: {owner_id}")
                return response
        except Exception as e:
            logger.debug(f"Failed to get schema from owner {owner_id}: {e}")
            continue
    
    logger.warning(f"Could not find achievement schema for App ID {appid}")
    return None


def save_schema(schema_response: any, appid: int, output_dir: Path, db_manager: GameDatabaseManager) -> bool:
    """
    Save the achievement schema to a binary file in both the output directory and Steam's appcache/stats directory.
    
    Args:
        schema_response: Steam response containing schema data
        appid: App ID for filename
        output_dir: Directory to save backup file in
        db_manager: Database manager instance to get Steam ID and paths
        
    Returns:
        True if saved successfully to both locations, False otherwise
    """
    schema_data = schema_response.body.schema
    success = True
    
    # Save to output directory (backup/local copy)
    backup_filename = output_dir / f'UserGameStatsSchema_{appid}.bin'
    try:
        with open(backup_filename, 'wb') as f:
            f.write(schema_data)
        logger.info(f"Successfully saved schema backup to: {backup_filename}")
    except IOError as e:
        logger.error(f"Failed to save schema backup file {backup_filename}: {e}")
        success = False
    
    # Save to Steam's appcache/stats directory
    try:
        # Load configuration to get Steam path
        config = SuperSexySteamLogic.load_configuration()
        if not config:
            logger.error("Could not load configuration. Cannot save schema to Steam directory.")
            return False
        
        steam_path = config.get("Paths", "steam_path")
        steam_stats_dir = Path(steam_path) / "appcache" / "stats"
        
        # Ensure the stats directory exists
        steam_stats_dir.mkdir(parents=True, exist_ok=True)
        
        # Save schema file to Steam directory
        steam_filename = steam_stats_dir / f'UserGameStatsSchema_{appid}.bin'
        with open(steam_filename, 'wb') as f:
            f.write(schema_data)
        logger.info(f"Successfully saved schema to Steam directory: {steam_filename}")
        
    except Exception as e:
        logger.error(f"Failed to save schema to Steam directory for App ID {appid}: {e}")
        success = False
    
    return success


def copy_usergamestats_template(appids: List[int], db_manager: GameDatabaseManager) -> bool:
    """
    Copy UserGameStats template for each App ID and move to Steam's appcache/stats directory.
    
    Args:
        appids: List of App IDs to create templates for
        db_manager: Database manager instance to get Steam ID
        
    Returns:
        True if all operations successful, False otherwise
    """
    logger.info("Starting UserGameStats template copying process")
    
    # Get Steam ID from database
    steam_id = db_manager.get_steam_id()
    if not steam_id:
        logger.error("No Steam ID found in database. Cannot create UserGameStats templates.")
        return False
    
    logger.info(f"Using Steam ID: {steam_id}")
    
    # Load configuration using existing app logic
    config = SuperSexySteamLogic.load_configuration()
    if not config:
        logger.error("Could not load configuration. Cannot determine Steam path.")
        return False
    
    try:
        steam_path = config.get("Paths", "steam_path")
    except Exception as e:
        logger.error(f"Steam path not found in configuration: {e}")
        return False
    
    # Construct the destination directory path
    steam_stats_dir = Path(steam_path) / "appcache" / "stats"
    logger.info(f"Target Steam stats directory: {steam_stats_dir}")
    
    # Create the stats directory if it doesn't exist
    try:
        steam_stats_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured stats directory exists: {steam_stats_dir}")
    except Exception as e:
        logger.error(f"Failed to create stats directory {steam_stats_dir}: {e}")
        return False
    
    # Find the UserGameStats template file
    template_file = Path("UserGameStats_steamid_appid.bin")
    if not template_file.exists():
        logger.error(f"UserGameStats template file not found: {template_file}")
        return False
    
    logger.info(f"Found template file: {template_file}")
    
    # Copy template for each App ID
    success_count = 0
    for appid in appids:
        target_filename = f"UserGameStats_{steam_id}_{appid}.bin"
        target_path = steam_stats_dir / target_filename
        
        try:
            # Copy the template file to the target location
            shutil.copy2(template_file, target_path)
            logger.info(f"Successfully copied template for App ID {appid} to: {target_path}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to copy template for App ID {appid}: {e}")
            continue
    
    logger.info(f"Successfully copied {success_count}/{len(appids)} UserGameStats templates")
    return success_count == len(appids)


def main():
    """Main function to orchestrate the achievement schema fetching process."""
    try:
        # Parse command line arguments (for credential management and manual App ID specification)
        manual_appids = parse_arguments()
        
        # Initialize database manager
        db_manager = GameDatabaseManager()
        
        # Get App IDs either from command line or database
        if manual_appids:
            # Manual mode: use App IDs from command line
            appids = manual_appids
            print(f"Manual mode: Using provided App IDs: {appids}")
        else:
            # Database mode: get App IDs from database that need achievement processing
            appids = get_appids_from_database(db_manager)
            
            if not appids:
                print("No games found that need achievement schema generation.")
                print("All games in the database already have their achievement schemas processed.")
                return
            
            print(f"Database mode: Found {len(appids)} games that need achievement processing: {appids}")
        
        # Authenticate with Steam
        client = authenticate_steam()
        
        # Setup output directory
        output_dir = setup_output_directory()
        
        # Add the logged-in user's ID to the front of the list
        all_owner_ids = [client.steam_id.as_64] + TOP_OWNER_IDS
        logger.debug(f"Will try {len(all_owner_ids)} different owner IDs")
        
        # Process each App ID
        success_count = 0
        processed_appids = []
        
        for appid in appids:
            logger.info(f"Processing App ID: {appid} ({success_count + 1}/{len(appids)})")
            schema_response = fetch_schema_for_appid(client, appid, all_owner_ids)
            
            if schema_response:
                if save_schema(schema_response, appid, output_dir, db_manager):
                    success_count += 1
                    processed_appids.append(appid)
                    
                    # Only mark as processed in database if not in manual mode
                    if not manual_appids:
                        if db_manager.mark_achievements_generated(str(appid)):
                            logger.info(f"Marked App ID {appid} as processed in database")
                        else:
                            logger.warning(f"Failed to mark App ID {appid} as processed in database")
                    else:
                        logger.info(f"Manual mode: Skipped marking App ID {appid} as processed in database")
        
        # Summary
        logger.info(f"Successfully processed {success_count}/{len(appids)} App IDs")
        print(f"\nSummary:")
        print(f"- Successfully processed: {success_count}/{len(appids)} games")
        print(f"- Processed App IDs: {processed_appids}")
        
        if success_count < len(appids):
            failed_appids = [appid for appid in appids if appid not in processed_appids]
            print(f"- Failed App IDs: {failed_appids}")
        
        # Copy UserGameStats templates for successfully processed App IDs
        if processed_appids:
            logger.info("Starting UserGameStats template copying process...")
            if copy_usergamestats_template(processed_appids, db_manager):
                logger.info("UserGameStats template copying completed successfully")
                print("- UserGameStats templates copied successfully")
            else:
                logger.warning("UserGameStats template copying completed with some errors")
                print("- UserGameStats template copying had some errors")
        
        # Cleanup
        logger.info("Logging out from Steam")
        client.logout()
        
        print(f"\nProcessing complete!")
        print(f"- Schema backups saved to: {output_dir.absolute()}")
        print(f"- Schema files copied to Steam's appcache/stats directory")
        print(f"- UserGameStats templates copied to Steam's appcache/stats directory")
        
        if manual_appids:
            print(f"- Manual mode: App IDs were NOT marked as processed in database")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

# =============================================================================
# --- ENTRY POINT ---
# =============================================================================

if __name__ == "__main__":
    main()