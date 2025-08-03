# stats_schema_gen.py
#
# A dedicated script for fetching and saving Steam's UserGameStatsSchema_<AppID>.bin files.
# This is a critical component for generating achievement data for emulators.

import os
import sys
import time
import logging
import shutil
from pathlib import Path
from steam.client import SteamClient
from steam.enums.common import EResult
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto

# Configure logging for clear output
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

# A list of Steam IDs with public profiles that own a large number of games.
# This increases the chances of finding a valid schema for any given AppID.
TOP_OWNER_IDS = [
    76561198017975643, 76561198028121353, 76561197979911851, 76561198355953202,
    76561198217186687, 76561197993544755, 76561198001237877, 76561198237402290,
    76561198152618007, 76561198213148949, 76561198037867621, 76561197969050296,
    76561198134044398, 76561198001678750, 76561198094227663, 76561197973009892,
    76561198019712127, 76561197976597747, 76561197963550511, 76561198044596404,
    76561198119667710, 76561197962473290, 76561197969810632, 76561198095049646,
    76561197995070100, 76561198085065107, 76561197996432822, 76561199492215670,
    76561198313790296, 76561198033715344, 76561198256917957,
]

def _get_stats_schema_from_steam(client: SteamClient, game_id: int, owner_id: int) -> MsgProto | None:
    """
    Sends a request to Steam to fetch the user game stats schema.

    Args:
        client (SteamClient): An active SteamClient instance.
        game_id (int): The AppID of the game.
        owner_id (int): The SteamID64 of a user known to own the game.

    Returns:
        MsgProto | None: The response message if successful, otherwise None.
    """
    logging.debug(f"Requesting schema for AppID {game_id} using owner {owner_id}")
    message = MsgProto(EMsg.ClientGetUserStats)
    message.body.game_id = game_id
    message.body.schema_local_version = -1  # Force Steam to send the latest schema
    message.body.crc_stats = 0
    message.body.steam_id_for_user = owner_id

    client.send(message)
    return client.wait_msg(EMsg.ClientGetUserStatsResponse, timeout=10)

def copy_user_game_stats_template(steam_id: int, app_id: int, steam_path: str) -> bool:
    """
    Copies and renames the UserGameStats template file for the specific user and app.
    
    Args:
        steam_id (int): The user's Steam ID
        app_id (int): The Steam AppID
        steam_path (str): Path to Steam installation directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Source template file
        template_file = Path("UserGameStats_steamid_appid.bin")
        
        if not template_file.exists():
            logging.error(f"Template file {template_file} not found in current directory")
            return False
        
        # Destination directory and file
        stats_dir = Path(steam_path) / "appcache" / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)
        
        dest_file = stats_dir / f"UserGameStats_{steam_id}_{app_id}.bin"
        
        logging.info(f"Copying UserGameStats template to: {dest_file}")
        shutil.copy2(template_file, dest_file)
        
        logging.info("Successfully created UserGameStats file")
        return True
        
    except Exception as e:
        logging.error(f"Error copying UserGameStats template: {e}")
        return False

def generate_stats_schema_bin(app_id: int, output_dir: str | Path, steam_id: int = None, steam_path: str = None) -> bool:
    """
    Fetches and saves the UserGameStatsSchema .bin file for a given AppID.

    This function logs into Steam anonymously, attempts to fetch the stats schema
    by iterating through a list of known game owners, and saves the first valid
    schema it finds to a binary file.

    Args:
        app_id (int): The Steam AppID for which to generate the schema.
        output_dir (str | Path): The directory where the .bin file will be saved.
        steam_id (int, optional): The user's Steam ID for creating UserGameStats file.
        steam_path (str, optional): Path to Steam installation for copying to appcache.

    Returns:
        bool: True if the file was successfully generated, False otherwise.
    """
    logging.info(f"Starting schema generation for AppID: {app_id}")
    client = SteamClient()

    # --- Step 1: Login to Steam ---
    logging.info("Attempting anonymous login to Steam...")
    result = client.anonymous_login()
    
    # Retry login if the initial attempt fails
    trials = 3
    while result != EResult.OK and trials > 0:
        logging.warning(f"Login failed with result: {result}. Retrying in 2 seconds...")
        time.sleep(2)
        result = client.anonymous_login()
        trials -= 1

    if result != EResult.OK:
        logging.error(f"Failed to login to Steam after multiple attempts. Final result: {result}")
        return False
    
    logging.info("Successfully logged in to Steam anonymously.")

    # --- Step 2: Find and Fetch the Schema ---
    stats_schema_response = None
    logging.info(f"Searching for a valid stats schema for AppID {app_id}...")
    for owner_id in TOP_OWNER_IDS:
        response = _get_stats_schema_from_steam(client, app_id, owner_id)
        
        # Check if the response is valid and contains schema data
        if response and response.body and hasattr(response.body, 'schema') and len(response.body.schema) > 0:
            logging.info(f"Successfully found schema using owner ID: {owner_id}")
            stats_schema_response = response
            break
        else:
            logging.debug(f"No schema found using owner ID: {owner_id}. Trying next.")

    client.logout()

    if not stats_schema_response:
        logging.error(f"Could not find a valid stats schema for AppID {app_id} after trying {len(TOP_OWNER_IDS)} owners.")
        logging.error("The game may not have any achievements or stats, or all checked profiles were private/invalid.")
        return False

    # --- Step 3: Write the Schema to the output directory ---
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        schema_file_name = f"UserGameStatsSchema_{app_id}.bin"
        schema_file_path = output_path / schema_file_name
        
        logging.info(f"Writing schema data to: {schema_file_path}")
        with open(schema_file_path, 'wb') as f:
            f.write(stats_schema_response.body.schema)
        
        logging.info(f"Successfully generated {schema_file_name}")
        
        # --- Step 4: If steam_path is provided, copy to Steam appcache/stats ---
        if steam_path:
            stats_dir = Path(steam_path) / "appcache" / "stats"
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            steam_schema_path = stats_dir / schema_file_name
            logging.info(f"Copying schema to Steam directory: {steam_schema_path}")
            shutil.copy2(schema_file_path, steam_schema_path)
            
            # --- Step 5: Copy UserGameStats template if steam_id is provided ---
            if steam_id:
                copy_user_game_stats_template(steam_id, app_id, steam_path)
        
        return True

    except Exception as e:
        logging.error(f"An error occurred while writing the schema file: {e}")
        return False

def generate_achievement_files(app_id: int, steam_id: int, steam_path: str) -> bool:
    """
    Generates both UserGameStatsSchema and UserGameStats files for achievement functionality.
    
    Args:
        app_id (int): The Steam AppID
        steam_id (int): The user's Steam ID
        steam_path (str): Path to Steam installation directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    logging.info(f"Generating achievement files for AppID {app_id}, SteamID {steam_id}")
    
    # Use a temporary directory for initial schema generation
    temp_output = "temp_schemas"
    
    success = generate_stats_schema_bin(app_id, temp_output, steam_id, steam_path)
    
    # Clean up temporary directory
    temp_path = Path(temp_output)
    if temp_path.exists():
        shutil.rmtree(temp_path)
    
    return success


