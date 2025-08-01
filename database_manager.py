# database_manager.py
#
# A SQLite database manager for SuperSexySteam.
# This module handles all database operations including AppID and depot management,
# tracking installation status, and providing data for the workflow modules.

import logging
import sqlite3
from pathlib import Path
import threading
from typing import List, Dict, Optional, Tuple

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


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
        logger.info(f"Initializing GameDatabaseManager with database: {db_path}")
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        logger.debug("Database lock created")
        self._init_database()
        logger.info("GameDatabaseManager initialized successfully")
    
    def _init_database(self):
        """Initialize the database schema."""
        logger.debug("Initializing database schema")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Create AppIDs table
                logger.debug("Creating appids table")
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
                    logger.info("Adding game_name column to existing database (migration)")
                    cursor.execute('ALTER TABLE appids ADD COLUMN game_name TEXT')
                else:
                    logger.debug("game_name column already exists")
                
                # Create Depots table
                logger.debug("Creating depots table")
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
                logger.debug("Creating manifests table")
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
                logger.debug("Creating database indices")
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_depots_app_id ON depots (app_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_appids_installed ON appids (is_installed)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_manifests_app_id ON manifests (app_id)')
                
                conn.commit()
                conn.close()
                logger.info("Database schema initialized successfully")
                
            except sqlite3.Error as e:
                logger.error(f"Failed to initialize database: {e}")
                logger.debug("Database initialization exception:", exc_info=True)
                raise
    
    def _get_connection(self):
        """Get a database connection with proper configuration and corruption checking."""
        logger.debug(f"Creating database connection to {self.db_path}")
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            
            # Test database integrity
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != 'ok':
                logger.warning(f"Database corruption detected: {integrity_result}")
                conn.close()
                return self._handle_database_corruption()
            
            # Configure connection for optimal performance and foreign key enforcement
            logger.debug("Configuring database connection settings")
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=1000')
            conn.execute('PRAGMA temp_store=memory')
            logger.debug("Database connection configured successfully")
            return conn
            
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error: {e}")
            logger.debug("Database connection error:", exc_info=True)
            return self._handle_database_corruption()
    
    def _handle_database_corruption(self):
        """Handle database corruption by creating a backup and rebuilding."""
        logger.warning("Handling database corruption")
        from datetime import datetime
        import time
        
        # Create backup of corrupted database
        backup_path = self.db_path.with_suffix(f".corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        try:
            if self.db_path.exists():
                logger.info(f"Attempting to backup corrupted database to: {backup_path}")
                # Try to close any existing connections first
                time.sleep(0.1)  # Brief pause to allow connections to close
                
                # Attempt backup with retry
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        backup_path.write_bytes(self.db_path.read_bytes())
                        logger.info(f"Corrupted database backed up to: {backup_path}")
                        break
                    except (OSError, IOError) as e:
                        if attempt < max_retries - 1:
                            logger.debug(f"Backup attempt {attempt + 1} failed, retrying: {e}")
                            time.sleep(0.5)  # Wait before retry
                            continue
                        else:
                            logger.warning(f"Could not backup corrupted database after {max_retries} attempts: {e}")
                
                # Try to remove corrupted file
                try:
                    logger.debug("Removing corrupted database file")
                    self.db_path.unlink()
                except (OSError, IOError) as e:
                    logger.warning(f"Could not remove corrupted database: {e}")
                    # Continue anyway, will overwrite
                    
        except Exception as e:
            logger.error(f"Error during corruption handling: {e}")
            logger.debug("Database corruption handling exception:", exc_info=True)
        
        # Reinitialize database
        logger.info("Rebuilding database from scratch...")
        try:
            self._init_database()
        except Exception as e:
            logger.error(f"Failed to rebuild database: {e}")
            logger.debug("Database rebuild exception:", exc_info=True)
            raise
        
        # Return new connection
        try:
            logger.debug("Creating new connection after rebuild")
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=1000')
            conn.execute('PRAGMA temp_store=memory')
            logger.info("Database corruption handled successfully")
            return conn
        except Exception as e:
            logger.error(f"Failed to create new connection: {e}")
            logger.debug("New connection creation exception:", exc_info=True)
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
        logger.info(f"Adding AppID {app_id} with {len(depots)} depots and {len(manifest_files)} manifest files")
        logger.debug(f"Game name: {game_name}")
        
        # Validate input
        if not app_id or not isinstance(app_id, str) or not app_id.strip():
            logger.error("app_id must be a non-empty string")
            raise ValueError("app_id must be a non-empty string")
            
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Insert or update the AppID
                logger.debug(f"Inserting/updating AppID {app_id} in database")
                cursor.execute('''
                    INSERT OR REPLACE INTO appids (app_id, game_name, last_updated, is_installed)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                ''', (app_id, game_name))
                
                # Remove existing depots and manifests for this AppID
                logger.debug(f"Removing existing depots and manifests for AppID {app_id}")
                cursor.execute('DELETE FROM depots WHERE app_id = ?', (app_id,))
                cursor.execute('DELETE FROM manifests WHERE app_id = ?', (app_id,))
                
                # Insert new depots
                depot_count = 0
                for depot in depots:
                    depot_id = depot.get('depot_id')
                    decryption_key = depot.get('depot_key')  # Can be None
                    
                    if depot_id:
                        cursor.execute('''
                            INSERT INTO depots (depot_id, app_id, decryption_key)
                            VALUES (?, ?, ?)
                        ''', (depot_id, app_id, decryption_key))
                        depot_count += 1
                        logger.debug(f"Added depot {depot_id} for AppID {app_id}")

                # Insert new manifest files
                manifest_count = 0
                for filename in manifest_files:
                    cursor.execute('''
                        INSERT INTO manifests (app_id, filename)
                        VALUES (?, ?)
                    ''', (app_id, filename))
                    manifest_count += 1
                    logger.debug(f"Added manifest file {filename} for AppID {app_id}")
                
                conn.commit()
                logger.info(f"Successfully added AppID {app_id} with {depot_count} depots and {manifest_count} manifest files")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"Failed to add AppID {app_id} with depots: {e}")
                logger.debug("Add AppID with depots exception:", exc_info=True)
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
        logger.info(f"Removing AppID {app_id} from database")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Remove the AppID (CASCADE will remove associated depots and manifests)
                logger.debug(f"Executing DELETE for AppID {app_id}")
                cursor.execute('DELETE FROM appids WHERE app_id = ?', (app_id,))
                
                conn.commit()
                logger.info(f"Successfully removed AppID {app_id} from database")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"Failed to remove AppID {app_id}: {e}")
                logger.debug("Remove AppID exception:", exc_info=True)
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
        logger.info(f"Marking AppID {app_id} as uninstalled")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                logger.debug(f"Updating is_installed flag for AppID {app_id}")
                cursor.execute('''
                    UPDATE appids SET is_installed = 0, last_updated = CURRENT_TIMESTAMP
                    WHERE app_id = ?
                ''', (app_id,))
                
                conn.commit()
                logger.info(f"Successfully marked AppID {app_id} as uninstalled")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"Failed to mark AppID {app_id} as uninstalled: {e}")
                logger.debug("Mark AppID uninstalled exception:", exc_info=True)
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
        logger.debug(f"Checking if AppID {app_id} exists in database")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT 1 FROM appids WHERE app_id = ? LIMIT 1', (app_id,))
                result = cursor.fetchone()
                
                conn.close()
                exists = result is not None
                logger.debug(f"AppID {app_id} exists: {exists}")
                return exists
                
            except sqlite3.Error as e:
                logger.error(f"Failed to check AppID {app_id}: {e}")
                logger.debug("Check AppID exists exception:", exc_info=True)
                return False
    
    def get_appid_depots(self, app_id: str) -> List[Dict[str, str]]:
        """
        Get all depots for a specific AppID.
        
        Args:
            app_id (str): The Steam AppID
            
        Returns:
            List[Dict]: List of depot dictionaries with 'depot_id' and 'decryption_key'
        """
        logger.debug(f"Retrieving depots for AppID {app_id}")
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
                
                logger.debug(f"Retrieved {len(depots)} depots for AppID {app_id}")
                return depots
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get depots for AppID {app_id}: {e}")
                logger.debug("Get AppID depots exception:", exc_info=True)
                return []
    
    def get_manifests_for_appid(self, app_id: str) -> List[str]:
        """
        Get all manifest filenames for a specific AppID.

        Args:
            app_id (str): The Steam AppID.

        Returns:
            List[str]: A list of manifest filenames.
        """
        logger.debug(f"Retrieving manifest files for AppID {app_id}")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT filename FROM manifests WHERE app_id = ?', (app_id,))
                results = cursor.fetchall()

                conn.close()
                manifest_files = [row[0] for row in results]
                logger.debug(f"Retrieved {len(manifest_files)} manifest files for AppID {app_id}")
                return manifest_files

            except sqlite3.Error as e:
                logger.error(f"Failed to get manifest files for AppID {app_id}: {e}")
                logger.debug("Get manifests for AppID exception:", exc_info=True)
                return []

    def get_all_installed_appids(self) -> List[str]:
        """
        Get all installed AppIDs from the database.
        
        Returns:
            List[str]: List of installed AppIDs
        """
        logger.debug("Retrieving all installed AppIDs")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT app_id FROM appids WHERE is_installed = 1 ORDER BY app_id')
                results = cursor.fetchall()
                
                conn.close()
                appids = [row[0] for row in results]
                logger.info(f"Retrieved {len(appids)} installed AppIDs")
                return appids
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get installed AppIDs: {e}")
                logger.debug("Get installed AppIDs exception:", exc_info=True)
                return []
    
    def get_all_depots_for_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get all depots for all installed AppIDs.
        
        Returns:
            List[Dict]: List of all depot dictionaries with 'depot_id', 'app_id', and optional 'decryption_key'
        """
        logger.debug("Retrieving all depots for installed apps")
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
                
                logger.debug(f"Retrieved {len(depots)} depots for installed apps")
                return depots
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get all depots: {e}")
                logger.debug("Get all depots exception:", exc_info=True)
                return []
    
    def get_depots_with_keys_for_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get only depots that have decryption keys for installed AppIDs.
        
        Returns:
            List[Dict]: List of depot dictionaries with 'depot_id', 'app_id', and 'decryption_key'
        """
        logger.debug("Retrieving depots with keys for installed apps")
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
                
                depots_with_keys = [{'depot_id': row[0], 'app_id': row[1], 'decryption_key': row[2]} 
                        for row in results]
                logger.debug(f"Retrieved {len(depots_with_keys)} depots with keys")
                return depots_with_keys
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get depots with keys: {e}")
                logger.debug("Get depots with keys exception:", exc_info=True)
                return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get statistics about the database contents.
        
        Returns:
            Dict[str, int]: Statistics including total_appids, installed_appids, total_depots, depots_with_keys, and total_manifests
        """
        logger.debug("Retrieving database statistics")
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
                
                stats = {
                    'total_appids': total_appids,
                    'installed_appids': installed_appids,
                    'total_depots': total_depots,
                    'depots_with_keys': depots_with_keys,
                    'total_manifests': total_manifests
                }
                
                logger.info(f"Database stats: {stats}")
                return stats
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get database stats: {e}")
                logger.debug("Get database stats exception:", exc_info=True)
                return {'total_appids': 0, 'installed_appids': 0, 'total_depots': 0, 'depots_with_keys': 0, 'total_manifests': 0}
    
    def get_installed_games(self) -> List[Dict[str, str]]:
        """
        Get all installed games with their AppID and name.
        
        Returns:
            List[Dict]: List of games with 'app_id' and 'game_name' keys
        """
        logger.debug("Retrieving installed games list")
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
                
                logger.debug(f"Retrieved {len(games)} installed games")
                return games
                
            except sqlite3.Error as e:
                logger.error(f"Failed to get installed games: {e}")
                logger.debug("Get installed games exception:", exc_info=True)
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
        logger.info(f"Updating game name for AppID {app_id}: {game_name}")
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE appids SET game_name = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE app_id = ?
                ''', (game_name, app_id))
                
                conn.commit()
                logger.info(f"Successfully updated game name for AppID {app_id}")
                return True
                
            except sqlite3.Error as e:
                logger.error(f"Failed to update game name for AppID {app_id}: {e}")
                logger.debug("Update game name exception:", exc_info=True)
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
        logger.info("Starting update of missing game names")
        from steam_game_search import get_game_name_by_appid
        
        updated_count = 0
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get all AppIDs without game names
                cursor.execute('SELECT app_id FROM appids WHERE game_name IS NULL OR game_name = ""')
                app_ids = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Found {len(app_ids)} AppIDs without game names")
                
                for app_id in app_ids:
                    try:
                        logger.debug(f"Looking up game name for AppID {app_id}")
                        game_name = get_game_name_by_appid(app_id)
                        if game_name and game_name != f"AppID {app_id}":
                            cursor.execute('''
                                UPDATE appids SET game_name = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE app_id = ?
                            ''', (game_name, app_id))
                            updated_count += 1
                            logger.info(f"Updated game name for AppID {app_id}: {game_name}")
                    except Exception as e:
                        logger.warning(f"Failed to update game name for AppID {app_id}: {e}")
                
                conn.commit()
                conn.close()
                logger.info(f"Completed update of missing game names: {updated_count} updated")
                
            except sqlite3.Error as e:
                logger.error(f"Failed to update missing game names: {e}")
                logger.debug("Update missing game names exception:", exc_info=True)
        
        return updated_count
    
    def close(self):
        """Close the database connection."""
        logger.debug("Database manager close() called")
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
    logger.info("Testing SuperSexySteam Database...")
    
    db = get_database_manager()
    
    # Test adding an AppID with depots and manifests
    test_depots = [
        {'depot_id': '12345', 'depot_key': 'abcdef123456'},
        {'depot_id': '12346'},  # No key
        {'depot_id': '12347', 'depot_key': '789abc456def'}
    ]
    test_manifests = ['manifest_1.bin', 'manifest_2.bin']
    
    success = db.add_appid_with_depots('999999', test_depots, test_manifests, game_name="Test Game")
    logger.info(f"Add AppID test: {'SUCCESS' if success else 'FAILED'}")
    
    # Test checking if AppID exists
    exists = db.is_appid_exists('999999')
    logger.info(f"AppID exists test: {'SUCCESS' if exists else 'FAILED'}")
    
    # Test getting depots
    retrieved_depots = db.get_appid_depots('999999')
    logger.info(f"Retrieved {len(retrieved_depots)} depots for test AppID")

    # Test getting manifests
    retrieved_manifests = db.get_manifests_for_appid('999999')
    logger.info(f"Retrieved {len(retrieved_manifests)} manifests for test AppID: {retrieved_manifests}")
    
    # Test getting stats
    stats = db.get_database_stats()
    logger.info(f"Database stats: {stats}")
    
    # Cleanup
    db.remove_appid('999999')
    print("Database test completed.")


