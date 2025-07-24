# depot_cache_manager.py
#
# A module for managing Steam depot cache files (.manifest files).
# Handles copying manifest files from data folders to Steam's depot cache
# and removing them during uninstallation.

import os
import shutil
import glob
from typing import Dict, List, Optional


def copy_manifests_for_appid(steam_path: str, app_id: str, data_folder: str) -> Dict[str, int]:
    """
    Copy all manifest files for a specific AppID from data folder to Steam depot cache.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID
        data_folder (str): Path to folder containing manifest files
        
    Returns:
        Dict[str, int]: Statistics with 'copied_count' and 'skipped_count'
    """
    stats = {'copied_count': 0, 'skipped_count': 0}
    
    try:
        # Construct depot cache path
        depot_cache_path = os.path.join(steam_path, 'depotcache')
        if not os.path.exists(depot_cache_path):
            try:
                os.makedirs(depot_cache_path, exist_ok=True)
                print(f"[INFO] Created depot cache directory: {depot_cache_path}")
            except Exception as e:
                print(f"[ERROR] Failed to create depot cache directory: {e}")
                return stats
        
        # Find all manifest files in the data folder
        manifest_pattern = os.path.join(data_folder, "*.manifest")
        manifest_files = glob.glob(manifest_pattern)
        
        if not manifest_files:
            print(f"[INFO] No manifest files found for AppID {app_id} in {data_folder}")
            return stats
        
        # Copy each manifest file
        for manifest_file in manifest_files:
            try:
                filename = os.path.basename(manifest_file)
                destination = os.path.join(depot_cache_path, filename)
                
                # Check if file already exists and is identical
                if os.path.exists(destination):
                    if os.path.getsize(manifest_file) == os.path.getsize(destination):
                        # Files are same size, assume they're identical
                        stats['skipped_count'] += 1
                        continue
                
                # Copy the file
                shutil.copy2(manifest_file, destination)
                stats['copied_count'] += 1
                print(f"[INFO] Copied manifest: {filename}")
                
            except Exception as e:
                print(f"[ERROR] Failed to copy manifest {os.path.basename(manifest_file)}: {e}")
        
        print(f"[INFO] Depot cache update complete for AppID {app_id}: {stats['copied_count']} copied, {stats['skipped_count']} skipped")
        
    except Exception as e:
        print(f"[ERROR] Failed to update depot cache for AppID {app_id}: {e}")
    
    return stats


def remove_manifests_for_appid(steam_path: str, app_id: str) -> Dict[str, int]:
    """
    Remove manifest files for a specific AppID from Steam depot cache.
    Note: This is a basic implementation that removes all .manifest files.
    In a more advanced implementation, you might want to track which specific
    manifest files belong to which AppID.
    
    Args:
        steam_path (str): Path to Steam installation directory
        app_id (str): The Steam AppID
        
    Returns:
        Dict[str, int]: Statistics with 'removed_count'
    """
    stats = {'removed_count': 0}
    
    try:
        # Construct depot cache path
        depot_cache_path = os.path.join(steam_path, 'depotcache')
        if not os.path.exists(depot_cache_path):
            print(f"[INFO] Depot cache directory does not exist: {depot_cache_path}")
            return stats
        
        # For now, we'll implement a simple approach:
        # Remove all manifest files that were likely added for this AppID
        # In a production system, you'd want to track this more precisely
        
        # Find all manifest files in depot cache
        manifest_pattern = os.path.join(depot_cache_path, "*.manifest")
        manifest_files = glob.glob(manifest_pattern)
        
        if not manifest_files:
            print(f"[INFO] No manifest files found in depot cache")
            return stats
        
        # Check if there's a corresponding data folder to match files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_folder = os.path.join(script_dir, "data", app_id)
        
        if os.path.exists(data_folder):
            # Match manifest files from data folder
            data_manifest_pattern = os.path.join(data_folder, "*.manifest")
            data_manifest_files = glob.glob(data_manifest_pattern)
            data_manifest_names = [os.path.basename(f) for f in data_manifest_files]
            
            # Remove matching files from depot cache
            for manifest_file in manifest_files:
                filename = os.path.basename(manifest_file)
                if filename in data_manifest_names:
                    try:
                        os.remove(manifest_file)
                        stats['removed_count'] += 1
                        print(f"[INFO] Removed manifest: {filename}")
                    except Exception as e:
                        print(f"[ERROR] Failed to remove manifest {filename}: {e}")
        else:
            print(f"[WARNING] Data folder not found for AppID {app_id}, cannot match specific manifest files")
        
        print(f"[INFO] Depot cache cleanup complete for AppID {app_id}: {stats['removed_count']} removed")
        
    except Exception as e:
        print(f"[ERROR] Failed to cleanup depot cache for AppID {app_id}: {e}")
    
    return stats


def get_depot_cache_info(steam_path: str) -> Dict[str, any]:
    """
    Get information about the depot cache directory.
    
    Args:
        steam_path (str): Path to Steam installation directory
        
    Returns:
        Dict[str, any]: Information about depot cache
    """
    info = {
        'path': '',
        'exists': False,
        'manifest_count': 0,
        'total_size_mb': 0.0
    }
    
    try:
        depot_cache_path = os.path.join(steam_path, 'depotcache')
        info['path'] = depot_cache_path
        info['exists'] = os.path.exists(depot_cache_path)
        
        if info['exists']:
            manifest_pattern = os.path.join(depot_cache_path, "*.manifest")
            manifest_files = glob.glob(manifest_pattern)
            info['manifest_count'] = len(manifest_files)
            
            total_size = 0
            for manifest_file in manifest_files:
                try:
                    total_size += os.path.getsize(manifest_file)
                except Exception:
                    pass  # Skip files we can't read
            
            info['total_size_mb'] = total_size / (1024 * 1024)
    
    except Exception as e:
        print(f"[ERROR] Failed to get depot cache info: {e}")
    
    return info


if __name__ == "__main__":
    # Test the depot cache manager
    print("Depot cache manager module loaded successfully!")
    
    # Example test (commented out to avoid accidental execution)
    # steam_path = "C:\\Program Files (x86)\\Steam"
    # info = get_depot_cache_info(steam_path)
    # print(f"Depot cache info: {info}")
