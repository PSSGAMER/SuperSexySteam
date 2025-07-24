# acfgen.py
#
# This script is responsible for generating Steam's 'appmanifest_*.acf' files.
# Updated for the new database-driven SuperSexySteam system.
# These files are critical for the Steam client to recognize games as "installed."

import configparser
import os
import re
import time
import traceback
from pathlib import Path
from steam.client import SteamClient

class ManifestGenerator:
    """
    A class to handle the generation of Steam appmanifest.acf files.

    This class encapsulates all the logic required to connect to Steam,
    fetch application data, parse it, and format it into the precise
    .acf file structure that the Steam client requires.
    """
    def __init__(self):
        """Initializes the SteamClient instance."""
        self.client = SteamClient()
        self._logged_on = False

    def _ensure_logged_in(self) -> bool:
        """
        Ensures the Steam client is logged in before making API calls.

        It attempts to log in anonymously. If already logged in, it returns
        True immediately. It includes a short delay and a status check to
        ensure the connection is fully established before proceeding.

        Returns:
            bool: True if the client is successfully logged in, False otherwise.
        """
        if self._logged_on:
            return True
        
        print("Attempting anonymous login to Steam...")
        try:
            # Attempt the anonymous login.
            result = self.client.anonymous_login()
            print(f"Login result: {result}")
            
            # Wait a moment for the connection to stabilize. This is crucial,
            # as the login call can return before the session is fully ready.
            time.sleep(2)
            
            # Explicitly check the logged_on status of the client.
            if self.client.logged_on:
                self._logged_on = True
                print("Successfully logged in anonymously.")
                print(f"Steam ID: {self.client.steam_id}")
                return True
            else:
                print("Login appeared to succeed but client is not logged on.")
                return False
                
        except Exception as e:
            print(f"Error: Failed to log into Steam: {e}")
            traceback.print_exc()
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
        return re.sub(r'[<>:"/\\|?*]', '', name).strip()

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
        indent = '\t' * level
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f'{indent}"{key}"')
                lines.append(f'{indent}{{')
                lines.append(self._format_acf_dict(value, level + 1))
                lines.append(f'{indent}}}')
            else:
                lines.append(f'{indent}"{key}"\t\t"{value}"')
        return '\n'.join(lines)

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
        print(f"\n--- Running Manifest Generator for AppID: {app_id} ---")
        if not self._ensure_logged_in():
            print("Cannot generate manifest without being logged in.")
            return

        try:
            # --- Step 1: Fetch Product Info from Steam ---
            # This can sometimes fail due to network issues, so we retry a few times.
            print(f"Fetching product info for app_id: {app_id}...")
            max_retries = 3
            res = None
            for attempt in range(max_retries):
                try:
                    res = self.client.get_product_info(apps=[app_id])
                    # If we get a valid response with app data, we can stop retrying.
                    if res and 'apps' in res:
                        break
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
            
            if not res:
                print(f"Error: Failed to get any response for app_id {app_id} after {max_retries} attempts.")
                return
            
            # The Steam API can be inconsistent, sometimes using a string key for the
            # AppID and sometimes an integer. We check for both possibilities.
            app_data = None
            if 'apps' in res and res['apps']:
                if str(app_id) in res['apps']:
                    app_data = res['apps'][str(app_id)]
                elif app_id in res['apps']:
                    app_data = res['apps'][app_id]
            
            if not app_data:
                print(f"Error: No product info returned for app_id {app_id}.")
                print(f"Full response: {res}")
                return

            # The 'common' section contains essential data like the app name.
            if 'common' not in app_data:
                print(f"Error: App {app_id} has no 'common' section.")
                return

            # --- Step 2: Parse the product info into a structured dictionary ---
            common = app_data.get('common', {})
            config = app_data.get('config', {})
            depots_data = app_data.get('depots', {})
            
            parsed_info = {
                'AppId': app_id,
                'Name': common.get('name', f'Unknown App {app_id}'),
                'InstallDir': config.get('installdir', self._sanitize_filename(common.get('name', ''))),
                'BuildId': int(depots_data.get('branches', {}).get('public', {}).get('buildid', '0')),
                'Depots': {},
                'DepotsShared': {}
            }

            # Iterate through all depots to categorize them and extract relevant info.
            for depot_id_str, depot_info in depots_data.items():
                if not depot_id_str.isdigit(): continue # Skip non-depot keys like 'branches'
                depot_id = int(depot_id_str)

                # A 'sharedinstall' flag indicates a depot shared from another app (e.g., DirectX).
                if depot_info.get('sharedinstall') == '1':
                    parsed_info['DepotsShared'][depot_id] = int(depot_info.get('depotfromapp', depot_id))
                    continue

                # For standard depots, get the manifest ID and size.
                manifests = depot_info.get('manifests', {}).get('public')
                if manifests and 'gid' in manifests:
                    parsed_info['Depots'][depot_id] = {
                        'manifest': manifests['gid'],
                        'size': int(manifests.get('size', '0')),
                    }
                    # If it's a DLC depot, store its parent AppID.
                    if 'dlcappid' in depot_info:
                        parsed_info['Depots'][depot_id]['dlcappid'] = depot_info['dlcappid']

            # --- Step 3: Build the final ACF dictionary ---
            # This dictionary directly maps to the structure required by Steam.
            total_size = sum(d['size'] for d in parsed_info['Depots'].values())
            last_owner = self.client.steam_id.as_64 if self.client.steam_id else 0

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
            if parsed_info['DepotsShared']:
                acf_dict['AppState']['SharedDepots'] = parsed_info['DepotsShared']

            # --- Step 4: Format the dictionary to a string and write to file ---
            acf_string = self._format_acf_dict(acf_dict)
            file_path = output_dir / f"appmanifest_{app_id}.acf"
            file_path.write_text(acf_string, encoding="utf-8")

            print("-" * 50)
            print("Successfully generated manifest file!")
            print(f"File: {file_path}")
            print(f"AppID: {parsed_info['AppId']}")
            print(f"Name: {parsed_info['Name']}")
            print(f"Install Directory: {parsed_info['InstallDir']}")
            print(f"Size: {total_size} bytes")
            print(f"BuildID: {parsed_info['BuildId']}")
            print(f"Depots: {len(parsed_info['Depots'])}")
            print(f"Shared Depots: {len(parsed_info['DepotsShared'])}")
            print("-" * 50)

        except Exception as e:
            print(f"Error generating manifest for AppID {app_id}: {e}")
            traceback.print_exc()


def generate_acf_for_appid(steam_path: str, app_id: str) -> bool:
    """
    Generate an ACF file for a single AppID.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID to generate ACF for
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        steamapps_path = Path(steam_path) / 'steamapps'
        if not steamapps_path.is_dir():
            print(f"[Error] The 'steamapps' directory could not be found at: {steamapps_path}")
            return False
        
        print(f"[INFO] Generating ACF file for AppID {app_id}")
        
        # Remove any existing ACF file first
        remove_acf_for_appid(steam_path, app_id)
        
        # Generate new ACF file
        generator = ManifestGenerator()
        try:
            app_id_int = int(app_id)
            generator.run_manifest_generator(app_id_int, steamapps_path)
            print(f"[SUCCESS] ACF file generated for AppID {app_id}")
            return True
        except ValueError:
            print(f"[Error] Invalid AppID '{app_id}' - must be numeric")
            return False
        except Exception as e:
            print(f"[Error] Failed to generate ACF for AppID {app_id}: {e}")
            return False
            
    except Exception as e:
        print(f"[Error] Unexpected error generating ACF for AppID {app_id}: {e}")
        return False


def remove_acf_for_appid(steam_path: str, app_id: str) -> bool:
    """
    Remove the ACF file for a specific AppID.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID to remove ACF for
        
    Returns:
        bool: True if successful or file doesn't exist, False on error
    """
    try:
        steamapps_path = Path(steam_path) / 'steamapps'
        if not steamapps_path.is_dir():
            print(f"[Error] The 'steamapps' directory could not be found at: {steamapps_path}")
            return False
        
        # Find and remove the ACF file
        acf_pattern = f"appmanifest_{app_id}.acf"
        acf_path = steamapps_path / acf_pattern
        
        if acf_path.exists():
            try:
                acf_path.unlink()
                print(f"[INFO] Removed ACF file: {acf_pattern}")
                return True
            except Exception as e:
                print(f"[Error] Failed to remove ACF file {acf_pattern}: {e}")
                return False
        else:
            print(f"[INFO] ACF file not found for AppID {app_id}: {acf_pattern}")
            return True  # Not existing is considered success for removal
            
    except Exception as e:
        print(f"[Error] Unexpected error removing ACF for AppID {app_id}: {e}")
        return False


if __name__ == "__main__":
    """
    Standard script entry point. Individual ACF generation functions are now
    available via generate_acf_for_appid() and remove_acf_for_appid().
    The new system generates ACFs automatically during real-time processing.
    """
    print("acfgen.py - Individual ACF generation functions available")
    print("Use generate_acf_for_appid() and remove_acf_for_appid() functions")
    print("Legacy bulk generation has been removed in favor of real-time processing")
