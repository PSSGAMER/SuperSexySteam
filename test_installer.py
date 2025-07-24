# test_installer.py
#
# A simple test script to verify the game installer functionality

import os
import configparser
from game_installer import GameInstaller
from database_manager import get_database_manager

def create_test_config():
    """Create a test configuration."""
    config = configparser.ConfigParser()
    config['Paths'] = {
        'steam_path': 'C:\\Program Files (x86)\\Steam',
        'greenluma_path': 'GreenLuma'
    }
    config['Debug'] = {
        'show_console': 'True'
    }
    return config

def create_test_lua_file(app_id, folder_path):
    """Create a test lua file."""
    os.makedirs(folder_path, exist_ok=True)
    lua_content = f"""-- Test lua file for AppID {app_id}
addappid({app_id}123, 1, "abcdef1234567890")
addappid({app_id}124, 1, "fedcba0987654321")
addappid({app_id}125)
"""
    lua_file = os.path.join(folder_path, f"{app_id}.lua")
    with open(lua_file, 'w', encoding='utf-8') as f:
        f.write(lua_content)
    
    return lua_file

def test_installer():
    """Test the game installer functionality."""
    print("Testing Game Installer...")
    
    # Create test configuration
    config = create_test_config()
    
    # Create installer
    installer = GameInstaller(config)
    
    # Test AppID
    test_app_id = "999999"
    test_folder = f"test_data_{test_app_id}"
    
    try:
        # Create test lua file
        lua_file = create_test_lua_file(test_app_id, test_folder)
        print(f"Created test lua file: {lua_file}")
        
        # Test installation
        print(f"Installing AppID {test_app_id}...")
        install_result = installer.install_game(test_app_id, test_folder)
        
        if install_result['success']:
            print("✓ Installation test PASSED")
            print(f"  Stats: {install_result['stats']}")
            if install_result['warnings']:
                print(f"  Warnings: {install_result['warnings']}")
        else:
            print("✗ Installation test FAILED")
            print(f"  Errors: {install_result['errors']}")
        
        # Test database check
        db = get_database_manager()
        exists = db.is_appid_exists(test_app_id)
        print(f"✓ Database check: AppID exists = {exists}")
        
        if exists:
            depots = db.get_appid_depots(test_app_id)
            print(f"  Found {len(depots)} depots in database")
            for depot in depots:
                has_key = 'depot_key' in depot
                print(f"    Depot {depot['depot_id']}: {'with key' if has_key else 'no key'}")
        
        # Test uninstallation
        if exists:
            print(f"Uninstalling AppID {test_app_id}...")
            uninstall_result = installer.uninstall_game(test_app_id)
            
            if uninstall_result['success']:
                print("✓ Uninstallation test PASSED")
                print(f"  Stats: {uninstall_result['stats']}")
                if uninstall_result['warnings']:
                    print(f"  Warnings: {uninstall_result['warnings']}")
            else:
                print("✗ Uninstallation test FAILED")
                print(f"  Errors: {uninstall_result['errors']}")
    
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_folder):
            import shutil
            shutil.rmtree(test_folder, ignore_errors=True)
            print(f"Cleaned up test folder: {test_folder}")
    
    # Show final database stats
    try:
        db = get_database_manager()
        stats = db.get_database_stats()
        print(f"Final database stats: {stats}")
    except Exception as e:
        print(f"Error getting final stats: {e}")

if __name__ == "__main__":
    test_installer()
