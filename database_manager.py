# database_manager.py
#
# A SQLite database manager for SuperSexySteam.
# This module handles all database operations including AppID and depot management,
# tracking installation status, and providing data for the workflow modules.

import sqlite3
from pathlib import Path
import threading
from typing import List, Dict, Optional, Tuple


class GameDatabaseManager:
    """
    Manages the SQLite database for SuperSexySteam application.
    Handles AppIDs, depots, and their relationships with thread safety.
    """
    
    def __init__(self, db_path: str = "supersexysteam.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema."""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Create AppIDs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS appids (
                        app_id TEXT PRIMARY KEY,
                        game_name TEXT,
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_installed BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Check if game_name column exists, if not add it (for migration)
                cursor.execute("PRAGMA table_info(appids)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'game_name' not in columns:
                    cursor.execute('ALTER TABLE appids ADD COLUMN game_name TEXT')
                    print("[INFO] Added game_name column to existing database")
                
                # Create Depots table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS depots (
                        depot_id TEXT PRIMARY KEY,
                        app_id TEXT NOT NULL,
                        decryption_key TEXT,
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (app_id) REFERENCES appids (app_id) ON DELETE CASCADE
                    )
                ''')

                # Create Manifests table to track manifest files for robust cleanup
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS manifests (
                        app_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (app_id, filename),
                        FOREIGN KEY (app_id) REFERENCES appids (app_id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_depots_app_id ON depots (app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_appids_installed ON appids (is_installed)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_manifests_app_id ON manifests (app_id)')
                
                conn.commit()
                conn.close()
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to initialize database: {e}")
                raise
    
    def _get_connection(self):
        """Get a database connection with proper configuration and corruption checking."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            
            # Test database integrity
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != 'ok':
                print(f"[Warning] Database corruption detected: {integrity_result}")
                conn.close()
                return self._handle_database_corruption()
            
            # Configure connection for optimal performance and foreign key enforcement
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=1000')
            conn.execute('PRAGMA temp_store=memory')
            return conn
            
        except sqlite3.DatabaseError as e:
            print(f"[Error] Database error: {e}")
            return self._handle_database_corruption()
    
    def _handle_database_corruption(self):
        """Handle database corruption by creating a backup and rebuilding."""
        from datetime import datetime
        import time
        
        # Create backup of corrupted database
        backup_path = self.db_path.with_suffix(f".corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        try:
            if self.db_path.exists():
                # Try to close any existing connections first
                time.sleep(0.1)  # Brief pause to allow connections to close
                
                # Attempt backup with retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        backup_path.write_bytes(self.db_path.read_bytes())
                        print(f"[Info] Corrupted database backed up to: {backup_path}")
                        break
                    except (OSError, IOError) as e:
                        if attempt < max_retries - 1:
                            time.sleep(0.5)  # Wait before retry
                            continue
                        else:
                            print(f"[Warning] Could not backup corrupted database after {max_retries} attempts: {e}")
                
                # Try to remove corrupted file
                try:
                    self.db_path.unlink()
                except (OSError, IOError) as e:
                    print(f"[Warning] Could not remove corrupted database: {e}")
                    # Continue anyway, will overwrite
                    
        except Exception as e:
            print(f"[Warning] Error during corruption handling: {e}")
        
        # Reinitialize database
        print("[Info] Rebuilding database from scratch...")
        try:
            self._init_database()
        except Exception as e:
            print(f"[Error] Failed to rebuild database: {e}")
            raise
        
        # Return new connection
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=1000')
            conn.execute('PRAGMA temp_store=memory')
            return conn
        except Exception as e:
            print(f"[Error] Failed to create new connection: {e}")
            raise

    def add_appid_with_depots(self, app_id: str, depots: List[Dict[str, str]], manifest_files: List[str], game_name: str = None) -> bool:
        """
        Add an AppID with its associated depots and manifest files to the database.
        
        Args:
            app_id (str): The Steam AppID
            depots (List[Dict]): List of depot dictionaries with 'depot_id' and optional 'depot_key'
            manifest_files (List[str]): List of manifest filenames
            game_name (str): The name of the game (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input
        if not app_id or not isinstance(app_id, str) or not app_id.strip():
            raise ValueError("app_id must be a non-empty string")
            
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Insert or update the AppID
                cursor.execute('''
                    INSERT OR REPLACE INTO appids (app_id, game_name, last_updated, is_installed)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                ''', (app_id, game_name))
                
                # Remove existing depots and manifests for this AppID
                cursor.execute('DELETE FROM depots WHERE app_id = ?', (app_id,))
                cursor.execute('DELETE FROM manifests WHERE app_id = ?', (app_id,))
                
                # Insert new depots
                for depot in depots:
                    depot_id = depot.get('depot_id')
                    decryption_key = depot.get('depot_key')  # Can be None
                    
                    if depot_id:
                        cursor.execute('''
                            INSERT INTO depots (depot_id, app_id, decryption_key)
                            VALUES (?, ?, ?)
                        ''', (depot_id, app_id, decryption_key))

                # Insert new manifest files
                for filename in manifest_files:
                    cursor.execute('''
                        INSERT INTO manifests (app_id, filename)
                        VALUES (?, ?)
                    ''', (app_id, filename))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to add AppID {app_id} with depots: {e}")
                return False
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def remove_appid(self, app_id: str) -> bool:
        """
        Remove an AppID and all its depots from the database.
        
        Args:
            app_id (str): The Steam AppID to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Remove the AppID (CASCADE will remove associated depots and manifests)
                cursor.execute('DELETE FROM appids WHERE app_id = ?', (app_id,))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to remove AppID {app_id}: {e}")
                return False
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def mark_appid_uninstalled(self, app_id: str) -> bool:
        """
        Mark an AppID as uninstalled without removing it from database.
        
        Args:
            app_id (str): The Steam AppID to mark as uninstalled
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE appids SET is_installed = 0, last_updated = CURRENT_TIMESTAMP
                    WHERE app_id = ?
                ''', (app_id,))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to mark AppID {app_id} as uninstalled: {e}")
                return False
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def is_appid_exists(self, app_id: str) -> bool:
        """
        Check if an AppID exists in the database.
        
        Args:
            app_id (str): The Steam AppID to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT 1 FROM appids WHERE app_id = ? LIMIT 1', (app_id,))
                result = cursor.fetchone()
                
                conn.close()
                return result is not None
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to check AppID {app_id}: {e}")
                return False
    
    def get_appid_depots(self, app_id: str) -> List[Dict[str, str]]:
        """
        Get all depots for a specific AppID.
        
        Args:
            app_id (str): The Steam AppID
            
        Returns:
            List[Dict]: List of depot dictionaries with 'depot_id' and 'decryption_key'
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT depot_id, decryption_key FROM depots 
                    WHERE app_id = ? 
                    ORDER BY depot_id
                ''', (app_id,))
                
                results = cursor.fetchall()
                conn.close()
                
                depots = []
                for depot_id, decryption_key in results:
                    depot = {'depot_id': depot_id}
                    if decryption_key:
                        depot['depot_key'] = decryption_key
                    depots.append(depot)
                
                return depots
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get depots for AppID {app_id}: {e}")
                return []
    
    def get_manifests_for_appid(self, app_id: str) -> List[str]:
        """
        Get all manifest filenames for a specific AppID.

        Args:
            app_id (str): The Steam AppID.

        Returns:
            List[str]: A list of manifest filenames.
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT filename FROM manifests WHERE app_id = ?', (app_id,))
                results = cursor.fetchall()

                conn.close()
                return [row[0] for row in results]

            except sqlite3.Error as e:
                print(f"[Error] Failed to get manifest files for AppID {app_id}: {e}")
                return []

    def get_all_installed_appids(self) -> List[str]:
        """
        Get all installed AppIDs from the database.
        
        Returns:
            List[str]: List of installed AppIDs
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT app_id FROM appids WHERE is_installed = 1 ORDER BY app_id')
                results = cursor.fetchall()
                
                conn.close()
                return [row[0] for row in results]
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get installed AppIDs: {e}")
                return []
    
    def get_all_depots_for_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get all depots for all installed AppIDs.
        
        Returns:
            List[Dict]: List of all depot dictionaries with 'depot_id', 'app_id', and optional 'decryption_key'
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT d.depot_id, d.app_id, d.decryption_key 
                    FROM depots d
                    JOIN appids a ON d.app_id = a.app_id
                    WHERE a.is_installed = 1
                    ORDER BY d.app_id, d.depot_id
                ''')
                
                results = cursor.fetchall()
                conn.close()
                
                depots = []
                for depot_id, app_id, decryption_key in results:
                    depot = {'depot_id': depot_id, 'app_id': app_id}
                    if decryption_key:
                        depot['decryption_key'] = decryption_key
                    depots.append(depot)
                
                return depots
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get all depots: {e}")
                return []
    
    def get_depots_with_keys_for_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get only depots that have decryption keys for installed AppIDs.
        
        Returns:
            List[Dict]: List of depot dictionaries with 'depot_id', 'app_id', and 'decryption_key'
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT d.depot_id, d.app_id, d.decryption_key 
                    FROM depots d
                    JOIN appids a ON d.app_id = a.app_id
                    WHERE a.is_installed = 1 AND d.decryption_key IS NOT NULL
                    ORDER BY d.app_id, d.depot_id
                ''')
                
                results = cursor.fetchall()
                conn.close()
                
                return [{'depot_id': row[0], 'app_id': row[1], 'decryption_key': row[2]} 
                        for row in results]
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get depots with keys: {e}")
                return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get statistics about the database contents.
        
        Returns:
            Dict[str, int]: Statistics including total_appids, installed_appids, total_depots, depots_with_keys, and total_manifests
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get total AppIDs
                cursor.execute('SELECT COUNT(*) FROM appids')
                total_appids = cursor.fetchone()[0]
                
                # Get installed AppIDs
                cursor.execute('SELECT COUNT(*) FROM appids WHERE is_installed = 1')
                installed_appids = cursor.fetchone()[0]
                
                # Get total depots
                cursor.execute('SELECT COUNT(*) FROM depots')
                total_depots = cursor.fetchone()[0]
                
                # Get depots with keys
                cursor.execute('SELECT COUNT(*) FROM depots WHERE decryption_key IS NOT NULL')
                depots_with_keys = cursor.fetchone()[0]
                
                # Get total manifest files tracked
                cursor.execute('SELECT COUNT(*) FROM manifests')
                total_manifests = cursor.fetchone()[0]
                
                conn.close()
                
                return {
                    'total_appids': total_appids,
                    'installed_appids': installed_appids,
                    'total_depots': total_depots,
                    'depots_with_keys': depots_with_keys,
                    'total_manifests': total_manifests
                }
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get database stats: {e}")
                return {'total_appids': 0, 'installed_appids': 0, 'total_depots': 0, 'depots_with_keys': 0, 'total_manifests': 0}
    
    def get_installed_games(self) -> List[Dict[str, str]]:
        """
        Get all installed games with their AppID and name.
        
        Returns:
            List[Dict]: List of games with 'app_id' and 'game_name' keys
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT app_id, game_name 
                    FROM appids 
                    WHERE is_installed = 1 
                    ORDER BY game_name ASC, app_id ASC
                ''')
                
                results = cursor.fetchall()
                conn.close()
                
                games = []
                for app_id, game_name in results:
                    games.append({
                        'app_id': app_id,
                        'game_name': game_name if game_name else f"AppID {app_id}"
                    })
                
                return games
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get installed games: {e}")
                return []
    
    def update_game_name(self, app_id: str, game_name: str) -> bool:
        """
        Update the game name for an existing AppID.
        
        Args:
            app_id (str): The Steam AppID
            game_name (str): The name of the game
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE appids SET game_name = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE app_id = ?
                ''', (game_name, app_id))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to update game name for AppID {app_id}: {e}")
                return False
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def update_missing_game_names(self) -> int:
        """
        Update game names for AppIDs that don't have them yet.
        This is useful for migrating existing databases.
        
        Returns:
            int: Number of games updated
        """
        from steam_game_search import get_game_name_by_appid
        
        updated_count = 0
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get all AppIDs without game names
                cursor.execute('SELECT app_id FROM appids WHERE game_name IS NULL OR game_name = ""')
                app_ids = [row[0] for row in cursor.fetchall()]
                
                for app_id in app_ids:
                    try:
                        game_name = get_game_name_by_appid(app_id)
                        if game_name and game_name != f"AppID {app_id}":
                            cursor.execute('''
                                UPDATE appids SET game_name = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE app_id = ?
                            ''', (game_name, app_id))
                            updated_count += 1
                            print(f"[INFO] Updated game name for AppID {app_id}: {game_name}")
                    except Exception as e:
                        print(f"[WARNING] Failed to update game name for AppID {app_id}: {e}")
                
                conn.commit()
                conn.close()
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to update missing game names: {e}")
        
        return updated_count
    
    def close(self):
        """Close the database connection."""
        # SQLite connections are created per operation, so no persistent connection to close
        pass


# =============================================================================
# --- CONVENIENCE FUNCTIONS ---
# =============================================================================

def get_database_manager() -> GameDatabaseManager:
    """
    Get a singleton instance of the database manager.
    
    Returns:
        GameDatabaseManager: The database manager instance
    """
    if not hasattr(get_database_manager, '_instance'):
        get_database_manager._instance = GameDatabaseManager()
    return get_database_manager._instance


def test_database():
    """Test function to verify database functionality."""
    print("Testing SuperSexySteam Database...")
    
    db = get_database_manager()
    
    # Test adding an AppID with depots and manifests
    test_depots = [
        {'depot_id': '12345', 'depot_key': 'abcdef123456'},
        {'depot_id': '12346'},  # No key
        {'depot_id': '12347', 'depot_key': '789abc456def'}
    ]
    test_manifests = ['manifest_1.bin', 'manifest_2.bin']
    
    success = db.add_appid_with_depots('999999', test_depots, test_manifests, game_name="Test Game")
    print(f"Add AppID test: {'SUCCESS' if success else 'FAILED'}")
    
    # Test checking if AppID exists
    exists = db.is_appid_exists('999999')
    print(f"AppID exists test: {'SUCCESS' if exists else 'FAILED'}")
    
    # Test getting depots
    retrieved_depots = db.get_appid_depots('999999')
    print(f"Retrieved {len(retrieved_depots)} depots for test AppID")

    # Test getting manifests
    retrieved_manifests = db.get_manifests_for_appid('999999')
    print(f"Retrieved {len(retrieved_manifests)} manifests for test AppID: {retrieved_manifests}")
    
    # Test getting stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Cleanup
    db.remove_appid('999999')
    print("Database test completed.")


if __name__ == "__main__":
    test_database()