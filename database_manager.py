# database_manager.py
#
# A SQLite database manager for SuperSexySteam.
# This module handles all database operations including AppID and depot management,
# tracking installation status, and providing data for the workflow modules.

import sqlite3
import os
import threading
from typing import List, Dict, Optional, Tuple


class GameDatabaseManager:
    """
    Manages the SQLite database for SuperSexySteam application.
    Handles AppIDs, depots, and their relationships with thread safety.
    """
    
    def __init__(self, db_path: str = "supersexyssteam.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
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
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_installed BOOLEAN DEFAULT 1
                    )
                ''')
                
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
                
                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_depots_app_id ON depots (app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_appids_installed ON appids (is_installed)')
                
                conn.commit()
                conn.close()
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to initialize database: {e}")
                raise
    
    def _get_connection(self):
        """Get a database connection with proper configuration and corruption checking."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            
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
        import shutil
        from datetime import datetime
        import time
        
        # Create backup of corrupted database
        backup_path = f"{self.db_path}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if os.path.exists(self.db_path):
                # Try to close any existing connections first
                time.sleep(0.1)  # Brief pause to allow connections to close
                
                # Attempt backup with retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        shutil.copy2(self.db_path, backup_path)
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
                    os.remove(self.db_path)
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
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=1000')
            conn.execute('PRAGMA temp_store=memory')
            return conn
        except Exception as e:
            print(f"[Error] Failed to create new connection: {e}")
            raise

    def add_appid_with_depots(self, app_id: str, depots: List[Dict[str, str]]) -> bool:
        """
        Add an AppID with its associated depots to the database.
        
        Args:
            app_id (str): The Steam AppID
            depots (List[Dict]): List of depot dictionaries with 'depot_id' and optional 'depot_key'
            
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
                    INSERT OR REPLACE INTO appids (app_id, last_updated, is_installed)
                    VALUES (?, CURRENT_TIMESTAMP, 1)
                ''', (app_id,))
                
                # Remove existing depots for this AppID
                cursor.execute('DELETE FROM depots WHERE app_id = ?', (app_id,))
                
                # Insert new depots
                for depot in depots:
                    depot_id = depot.get('depot_id')
                    decryption_key = depot.get('depot_key')  # Can be None
                    
                    if depot_id:
                        cursor.execute('''
                            INSERT INTO depots (depot_id, app_id, decryption_key)
                            VALUES (?, ?, ?)
                        ''', (depot_id, app_id, decryption_key))
                
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
                
                # Remove the AppID (CASCADE will remove associated depots)
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
            Dict[str, int]: Statistics including total_appids, installed_appids, total_depots, depots_with_keys
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
                
                conn.close()
                
                return {
                    'total_appids': total_appids,
                    'installed_appids': installed_appids,
                    'total_depots': total_depots,
                    'depots_with_keys': depots_with_keys
                }
                
            except sqlite3.Error as e:
                print(f"[Error] Failed to get database stats: {e}")
                return {'total_appids': 0, 'installed_appids': 0, 'total_depots': 0, 'depots_with_keys': 0}
    
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
    
    # Test adding an AppID with depots
    test_depots = [
        {'depot_id': '12345', 'depot_key': 'abcdef123456'},
        {'depot_id': '12346'},  # No key
        {'depot_id': '12347', 'depot_key': '789abc456def'}
    ]
    
    success = db.add_appid_with_depots('999999', test_depots)
    print(f"Add AppID test: {'SUCCESS' if success else 'FAILED'}")
    
    # Test checking if AppID exists
    exists = db.is_appid_exists('999999')
    print(f"AppID exists test: {'SUCCESS' if exists else 'FAILED'}")
    
    # Test getting depots
    retrieved_depots = db.get_appid_depots('999999')
    print(f"Retrieved {len(retrieved_depots)} depots for test AppID")
    
    # Test getting stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Cleanup
    db.remove_appid('999999')
    print("Database test completed.")


if __name__ == "__main__":
    test_database()
