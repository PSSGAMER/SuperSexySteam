# acfgen.py
#
# This script is responsible for generating Steam's 'appmanifest_*.acf' files.
# Updated for the new database-driven SuperSexySteam system.
# These files are critical for the Steam client to recognize games as "installed."

import configparser
import logging
import re
import time
import traceback
from pathlib import Path
from steam.client import SteamClient
from typing import List, Dict, Union

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('acfgen.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ManifestGenerator:
    """
    A class to handle the generation of Steam appmanifest.acf files.

    This class encapsulates all the logic required to connect to Steam,
    fetch application data, parse it, and format it into the precise
    .acf file structure that the Steam client requires.
    """
    def __init__(self):
        """Initializes the SteamClient instance."""
        logger.info("Initializing ManifestGenerator")
        self.client = SteamClient()
        self._logged_on = False
        logger.debug("SteamClient instance created")

    def _ensure_logged_in(self) -> bool:
        """
        Ensures the Steam client is logged in before making API calls.

        It attempts to log in anonymously. If already logged in, it returns
        True immediately. It uses a polling mechanism with timeout to
        ensure the connection is fully established before proceeding.

        Returns:
            bool: True if the client is successfully logged in, False otherwise.
        """
        if self._logged_on:
            logger.debug("Already logged in to Steam")
            return True
        
        logger.info("Attempting anonymous login to Steam...")
        try:
            # Attempt the anonymous login.
            result = self.client.anonymous_login()
            logger.debug(f"Login result: {result}")
            
            # Poll the logged_on status with a timeout instead of fixed sleep
            timeout = 10.0  # 10 seconds timeout
            poll_interval = 0.2  # Check every 200ms
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.client.logged_on:
                    self._logged_on = True
                    logger.info("Successfully logged in anonymously")
                    logger.info(f"Steam ID: {self.client.steam_id}")
                    return True
                time.sleep(poll_interval)
            
            # If we reach here, we timed out waiting for login
            logger.error(f"Login timed out after {timeout} seconds - client is not logged on")
            return False
                
        except Exception as e:
            logger.error(f"Failed to log into Steam: {e}")
            logger.debug("Login exception details:", exc_info=True)
            return False

    def _sanitize_filename(self, name: str) -> str:
        """
        Removes characters from a string that are invalid for directory names.
        This is used to create a safe 'installdir' from the app's name if the
        API doesn't provide one.

        Args:
            name (str): The raw application name.

        Returns:
            str: A sanitized string suitable for use as a directory name.
        """
        logger.debug(f"Sanitizing filename: '{name}'")
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name).strip()
        logger.debug(f"Sanitized filename result: '{sanitized}'")
        return sanitized

    def _format_acf_dict(self, data: dict, level: int = 0) -> str:
        """
        Recursively formats a Python dictionary into the VDF/ACF string format.

        Steam's .acf files use a specific key-value format with nested braces
        and tabs for indentation. This function converts a dictionary into that
        exact string representation.

        Args:
            data (dict): The dictionary to format.
            level (int): The current indentation level for recursion.

        Returns:
            str: A string formatted in the ACF key-value style.
        """
        logger.debug(f"Formatting ACF dictionary at level {level} with {len(data)} keys")
        indent = '\t' * level
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                logger.debug(f"Processing nested dictionary for key '{key}' with {len(value)} sub-keys")
                lines.append(f'{indent}"{key}"')
                lines.append(f'{indent}{{')
                lines.append(self._format_acf_dict(value, level + 1))
                lines.append(f'{indent}}}')
            else:
                lines.append(f'{indent}"{key}"\t\t"{value}"')
        
        result = '\n'.join(lines)
        logger.debug(f"ACF formatting complete for level {level}, generated {len(lines)} lines")
        return result

    def run_manifest_generator(self, app_id: int, output_dir: Path) -> None:
        """
        Orchestrates the entire process of generating a single .acf file.

        This method handles logging in, fetching product info from Steam,
        parsing the complex response, building the final ACF data structure,
        and writing it to the specified output directory.

        Args:
            app_id (int): The Steam AppID to generate a manifest for.
            output_dir (Path): The directory where the .acf file will be saved.
        """
        logger.info(f"Starting manifest generation for AppID: {app_id}")
        logger.debug(f"Output directory: {output_dir}")
        
        if not self._ensure_logged_in():
            logger.error("Cannot generate manifest without being logged in")
            return

        try:
            # --- Step 1: Fetch Product Info from Steam ---
            # This can sometimes fail due to network issues, so we retry a few times.
            logger.info(f"Fetching product info for app_id: {app_id}")
            max_retries = 3
            res = None
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempt {attempt + 1} of {max_retries} to fetch product info")
                    res = self.client.get_product_info(apps=[app_id])
                    # If we get a valid response with app data, we can stop retrying.
                    if res and 'apps' in res:
                        logger.debug(f"Successfully fetched product info on attempt {attempt + 1}")
                        break
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed")
                        raise
                    time.sleep(2)
            
            if not res:
                logger.error(f"Failed to get any response for app_id {app_id} after {max_retries} attempts")
                return
            
            # The Steam API can be inconsistent, sometimes using a string key for the
            # AppID and sometimes an integer. We check for both possibilities.
            logger.debug("Parsing response data for app information")
            app_data = None
            if 'apps' in res and res['apps']:
                if str(app_id) in res['apps']:
                    app_data = res['apps'][str(app_id)]
                    logger.debug(f"Found app data using string key '{app_id}'")
                elif app_id in res['apps']:
                    app_data = res['apps'][app_id]
                    logger.debug(f"Found app data using integer key {app_id}")
            
            if not app_data:
                logger.error(f"No product info returned for app_id {app_id}")
                logger.debug(f"Full response: {res}")
                return

            # The 'common' section contains essential data like the app name.
            if 'common' not in app_data:
                logger.error(f"App {app_id} has no 'common' section")
                logger.debug(f"App data structure: {list(app_data.keys())}")
                return

            # --- Step 2: Parse the product info into a structured dictionary ---
            logger.debug("Extracting data from app sections")
            common = app_data.get('common', {})
            config = app_data.get('config', {})
            depots_data = app_data.get('depots', {})
            
            app_name = common.get('name', f'Unknown App {app_id}')
            install_dir = config.get('installdir', self._sanitize_filename(app_name))
            build_id = int(depots_data.get('branches', {}).get('public', {}).get('buildid', '0'))
            
            logger.info(f"Processing app: {app_name} (AppID: {app_id})")
            logger.debug(f"Install directory: {install_dir}")
            logger.debug(f"Build ID: {build_id}")
            
            parsed_info = {
                'AppId': app_id,
                'Name': app_name,
                'InstallDir': install_dir,
                'BuildId': build_id,
                'Depots': {},
                'DepotsShared': {}
            }

            # Iterate through all depots to categorize them and extract relevant info.
            logger.debug(f"Processing {len(depots_data)} depot entries")
            depot_count = 0
            shared_depot_count = 0
            
            for depot_id_str, depot_info in depots_data.items():
                if not depot_id_str.isdigit(): 
                    logger.debug(f"Skipping non-depot key: {depot_id_str}")
                    continue # Skip non-depot keys like 'branches'
                    
                depot_id = int(depot_id_str)
                logger.debug(f"Processing depot {depot_id}")

                # A 'sharedinstall' flag indicates a depot shared from another app (e.g., DirectX).
                if depot_info.get('sharedinstall') == '1':
                    shared_app_id = int(depot_info.get('depotfromapp', depot_id))
                    parsed_info['DepotsShared'][depot_id] = shared_app_id
                    shared_depot_count += 1
                    logger.debug(f"Added shared depot {depot_id} from app {shared_app_id}")
                    continue

                # For standard depots, get the manifest ID and size.
                manifests = depot_info.get('manifests', {}).get('public')
                if manifests and 'gid' in manifests:
                    manifest_gid = manifests['gid']
                    manifest_size = int(manifests.get('size', '0'))
                    
                    parsed_info['Depots'][depot_id] = {
                        'manifest': manifest_gid,
                        'size': manifest_size,
                    }
                    depot_count += 1
                    logger.debug(f"Added depot {depot_id}: manifest={manifest_gid}, size={manifest_size}")
                    
                    # If it's a DLC depot, store its parent AppID.
                    if 'dlcappid' in depot_info:
                        dlc_app_id = depot_info['dlcappid']
                        parsed_info['Depots'][depot_id]['dlcappid'] = dlc_app_id
                        logger.debug(f"Depot {depot_id} is DLC for app {dlc_app_id}")
                else:
                    logger.debug(f"Depot {depot_id} has no public manifest, skipping")

            logger.info(f"Processed {depot_count} standard depots and {shared_depot_count} shared depots")

            # --- Step 3: Build the final ACF dictionary ---
            # This dictionary directly maps to the structure required by Steam.
            logger.debug("Building ACF dictionary structure")
            total_size = sum(d['size'] for d in parsed_info['Depots'].values())
            last_owner = self.client.steam_id.as_64 if self.client.steam_id else 0
            
            logger.debug(f"Total size: {total_size} bytes")
            logger.debug(f"Last owner Steam ID: {last_owner}")

            acf_dict = {
                "AppState": {
                    "appid": parsed_info['AppId'],
                    "Universe": 1, # 1 = Public Steam
                    "LauncherPath": "",
                    "name": parsed_info['Name'],
                    "StateFlags": 1026, # 4 = Update required, download in progress
                    "installdir": parsed_info['InstallDir'],
                    "LastUpdated": 0,
                    "SizeOnDisk": total_size,
                    "StagingSize": 0,
                    "buildid": parsed_info['BuildId'],
                    "LastOwner": last_owner,
                    "UpdateResult": 0,
                    "BytesToDownload": 0, "BytesDownloaded": 0,
                    "BytesToStage": 0, "BytesStaged": 0,
                    "TargetBuildID": 0,
                    "AutoUpdateBehavior": 0,
                    "AllowOtherDownloadsWhileRunning": 0,
                    "ScheduledAutoUpdate": 0
                }
            }

            # Only add the 'InstalledDepots' and 'SharedDepots' sections if they contain data.
            if parsed_info['Depots']:
                acf_dict['AppState']['InstalledDepots'] = parsed_info['Depots']
                logger.debug(f"Added {len(parsed_info['Depots'])} installed depots to ACF")
            if parsed_info['DepotsShared']:
                acf_dict['AppState']['SharedDepots'] = parsed_info['DepotsShared']
                logger.debug(f"Added {len(parsed_info['DepotsShared'])} shared depots to ACF")

            # --- Step 4: Format the dictionary to a string and write to file ---
            logger.debug("Converting ACF dictionary to string format")
            acf_string = self._format_acf_dict(acf_dict)
            file_path = output_dir / f"appmanifest_{app_id}.acf"
            
            logger.info(f"Writing ACF file to: {file_path}")
            file_path.write_text(acf_string, encoding="utf-8")

            logger.info("Successfully generated manifest file!")
            logger.info(f"File: {file_path}")
            logger.info(f"AppID: {parsed_info['AppId']}")
            logger.info(f"Name: {parsed_info['Name']}")
            logger.info(f"Install Directory: {parsed_info['InstallDir']}")
            logger.info(f"Size: {total_size} bytes")
            logger.info(f"BuildID: {parsed_info['BuildId']}")
            logger.info(f"Depots: {len(parsed_info['Depots'])}")
            logger.info(f"Shared Depots: {len(parsed_info['DepotsShared'])}")

        except Exception as e:
            logger.error(f"Error generating manifest for AppID {app_id}: {e}")
            logger.debug("Manifest generation exception details:", exc_info=True)


def generate_acf_for_appid(steam_path: Union[str, Path], app_id: str) -> bool:
    """
    Generate an ACF file for a single AppID.
    
    Args:
        steam_path (Union[str, Path]): Path to Steam installation directory
        app_id (str): The Steam AppID to generate ACF for
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Starting ACF generation for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    
    try:
        steam_path_obj = Path(steam_path)
        steamapps_path = steam_path_obj / 'steamapps'
        
        if not steamapps_path.is_dir():
            logger.error(f"The 'steamapps' directory could not be found at: {steamapps_path}")
            return False
        
        logger.debug(f"Steamapps directory found: {steamapps_path}")
        
        # Remove any existing ACF file first
        logger.debug("Removing any existing ACF file before generation")
        remove_acf_for_appid(steam_path_obj, app_id)
        
        # Generate new ACF file
        generator = ManifestGenerator()
        try:
            app_id_int = int(app_id)
            logger.debug(f"Converted AppID to integer: {app_id_int}")
            generator.run_manifest_generator(app_id_int, steamapps_path)
            logger.info(f"ACF file generated successfully for AppID {app_id}")
            return True
        except ValueError:
            logger.error(f"Invalid AppID '{app_id}' - must be numeric")
            return False
        except Exception as e:
            logger.error(f"Failed to generate ACF for AppID {app_id}: {e}")
            logger.debug("ACF generation exception:", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error generating ACF for AppID {app_id}: {e}")
        logger.debug("Unexpected exception:", exc_info=True)
        return False


def remove_acf_for_appid(steam_path: Union[str, Path], app_id: str) -> bool:
    """
    Remove the ACF file for a specific AppID.
    
    Args:
        steam_path (Union[str, Path]): Path to Steam installation directory
        app_id (str): The Steam AppID to remove ACF for
        
    Returns:
        bool: True if successful or file doesn't exist, False on error
    """
    logger.info(f"Removing ACF file for AppID {app_id}")
    logger.debug(f"Steam path: {steam_path}")
    
    try:
        steam_path_obj = Path(steam_path)
        steamapps_path = steam_path_obj / 'steamapps'
        
        if not steamapps_path.is_dir():
            logger.error(f"The 'steamapps' directory could not be found at: {steamapps_path}")
            return False
        
        # Find and remove the ACF file
        acf_filename = f"appmanifest_{app_id}.acf"
        acf_path = steamapps_path / acf_filename
        
        logger.debug(f"Looking for ACF file: {acf_path}")
        
        if acf_path.exists():
            try:
                acf_path.unlink()
                logger.info(f"Removed ACF file: {acf_filename}")
                return True
            except Exception as e:
                logger.error(f"Failed to remove ACF file {acf_filename}: {e}")
                logger.debug("ACF removal exception:", exc_info=True)
                return False
        else:
            logger.info(f"ACF file not found for AppID {app_id}: {acf_filename}")
            return True  # Not existing is considered success for removal
            
    except Exception as e:
        logger.error(f"Unexpected error removing ACF for AppID {app_id}: {e}")
        logger.debug("Unexpected exception:", exc_info=True)
        return False


def remove_all_tracked_acf_files(steam_path: Union[str, Path], tracked_appids: List[str]) -> Dict[str, int]:
    """
    Remove ACF files for all tracked AppIDs.
    
    Args:
        steam_path (Union[str, Path]): Path to Steam installation directory
        tracked_appids (List[str]): List of AppIDs to remove ACF files for
        
    Returns:
        Dict[str, int]: Statistics with 'removed_count'
    """
    logger.info(f"Starting bulk ACF removal for {len(tracked_appids)} AppIDs")
    logger.debug(f"Steam path: {steam_path}")
    logger.debug(f"AppIDs to remove: {tracked_appids}")
    
    stats = {'removed_count': 0}
    
    try:
        steam_path_obj = Path(steam_path)
        steamapps_path = steam_path_obj / 'steamapps'
        
        if not steamapps_path.is_dir():
            logger.error(f"The 'steamapps' directory could not be found at: {steamapps_path}")
            return stats
        
        logger.debug(f"Steamapps directory found: {steamapps_path}")
        
        for app_id in tracked_appids:
            acf_filename = f"appmanifest_{app_id}.acf"
            acf_path = steamapps_path / acf_filename
            
            logger.debug(f"Processing ACF file: {acf_filename}")
            
            if acf_path.exists():
                try:
                    acf_path.unlink()
                    stats['removed_count'] += 1
                    logger.debug(f"Removed ACF file: {acf_filename}")
                except Exception as e:
                    logger.error(f"Failed to remove ACF file {acf_filename}: {e}")
                    logger.debug(f"ACF removal error for {acf_filename}:", exc_info=True)
            else:
                logger.debug(f"ACF file not found: {acf_filename}")
        
        logger.info(f"ACF cleanup complete: {stats['removed_count']} files removed")
            
    except Exception as e:
        logger.error(f"Unexpected error removing ACF files: {e}")
        logger.debug("Bulk ACF removal exception:", exc_info=True)
    
    return stats


if __name__ == "__main__":
    logger.info("Broken")