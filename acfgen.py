# acfgen.py
#
# This script is responsible for generating Steam's 'appmanifest_*.acf' files.
# These files are critical for the Steam client to recognize games as "installed."
# The script performs two primary functions:
#   1. Deletes existing .acf files for any AppIDs marked as "updated" to ensure
#      a clean slate.
#   2. Generates new .acf files for all "new" and "updated" AppIDs by fetching
#      the latest configuration data directly from Steam's servers.
#
# It requires the 'steam' library to interact with the Steam network.
# You can install it by running: pip install -U "steam[client]"

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
            print(f"Location: {file_path.resolve()}")
            print("-" * 50)

        except Exception as e:
            print(f"An unexpected error occurred during manifest generation for AppID {app_id}: {e}")
            traceback.print_exc()

def delete_existing_manifests(steamapps_path, appids_to_delete):
    """
    Scans the steamapps directory and deletes .acf files for specified AppIDs.

    This is done for "updated" apps to ensure that Steam uses the newly
    generated manifest instead of an old, potentially conflicting one.

    Args:
        steamapps_path (Path): The path to the 'steamapps' directory.
        appids_to_delete (list): A list of AppID strings whose manifests should be deleted.
    """
    if not appids_to_delete:
        print("No 'updated' AppIDs found in data.ini. No files to delete.")
        return
        
    print(f"\n--- Deleting old manifests for {len(appids_to_delete)} updated AppIDs ---")
    manifest_pattern = re.compile(r'^appmanifest_(\d+)\.acf$')
    deleted_count = 0
    try:
        for filename in os.listdir(steamapps_path):
            match = manifest_pattern.match(filename)
            if match:
                appid_from_file = match.group(1)
                if appid_from_file in appids_to_delete:
                    file_to_delete = os.path.join(steamapps_path, filename)
                    try:
                        os.remove(file_to_delete)
                        print(f"  - Deleted '{filename}' (AppID: {appid_from_file})")
                        deleted_count += 1
                    except OSError as e:
                        print(f"  [Error] Could not delete file '{filename}': {e}")
    except Exception as e:
        print(f"[Error] An unexpected error occurred while scanning for manifests to delete: {e}")
    print(f"Deleted {deleted_count} old manifest file(s).")

def main():
    """
    The main orchestrator function for the script.

    It reads configuration, determines which apps to process, and then calls
    the necessary functions to delete old manifests and generate new ones.
    """
    print("--- acfgen.py: Starting cleanup and generation of appmanifest files ---")

    # --- Step 1: Read Configuration from .ini files ---
    config = configparser.ConfigParser()
    data_config = configparser.ConfigParser()

    try:
        config.read('config.ini')
        steam_path = config.get('Paths', 'steam_path', fallback=None)

        data_config.read('data.ini')
        new_appids_str = data_config.get('AppIDs', 'new', fallback='')
        updated_appids_str = data_config.get('AppIDs', 'updated', fallback='')
        
        # Create clean lists of AppIDs, filtering out any empty strings.
        new_appids = [app_id for app_id in new_appids_str.split(',') if app_id]
        updated_appids = [app_id for app_id in updated_appids_str.split(',') if app_id]

    except configparser.Error as e:
        print(f"[Error] Failed to read or parse configuration files: {e}")
        return
    except Exception as e:
        print(f"[Error] An unexpected error occurred during configuration loading: {e}")
        return

    # Validate the Steam path.
    if not steam_path or not os.path.isdir(steam_path):
        print(f"[Warning] Steam path '{steam_path}' is invalid or not configured in config.ini. Aborting.")
        return

    steamapps_path = Path(steam_path) / 'steamapps'
    if not steamapps_path.is_dir():
        print(f"[Error] The 'steamapps' directory could not be found at: {steamapps_path}")
        return

    # --- Step 2: Delete old ACF files for 'updated' apps ---
    # This is done first to prevent any conflicts with the new files we're about to generate.
    delete_existing_manifests(steamapps_path, updated_appids)

    # --- Step 3: Generate new ACF files for all 'new' and 'updated' apps ---
    appids_to_generate = new_appids + updated_appids
    if not appids_to_generate:
        print("\nNo new or updated AppIDs to process. Exiting.")
        return

    print(f"\n--- Preparing to generate manifests for {len(appids_to_generate)} AppIDs ---")
    
    # Instantiate the generator once to be used for all AppIDs.
    generator = ManifestGenerator()
    for app_id_str in appids_to_generate:
        try:
            app_id = int(app_id_str)
            generator.run_manifest_generator(app_id, steamapps_path)
        except ValueError:
            print(f"[Warning] Invalid AppID '{app_id_str}' found in data.ini. Skipping.")
        except Exception as e:
            print(f"[Error] A critical error occurred while processing AppID {app_id_str}: {e}")

    print(f"\n--- acfgen.py: Finished ---")
    
    time.sleep(3)

if __name__ == "__main__":
    """
    Standard script entry point. Ensures that the `main()` function is only
    called when the script is executed directly, not when imported as a module.
    """
    main()

# Docs are generated by AI and may be inaccurate
