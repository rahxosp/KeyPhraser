import sqlite3
from typing import Dict, List, Tuple, Optional
from config import Config
class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.initialize_db()
        self.initialize_services()


    def initialize_db(self):
        """Initialize database with all required tables"""
        try:
            cursor = self.conn.cursor()
            
            # Create services table first
            cursor.execute(Config.DB_SCHEMA_SERVICES)
            
            # Check if service_id column exists in credentials table
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pragma_table_info('credentials') 
                WHERE name='service_id'
            """)
            
            has_service_id = cursor.fetchone()[0] > 0
            
            if not has_service_id:
                # Drop existing credentials table and create new one
                cursor.execute("DROP TABLE IF EXISTS credentials")
                cursor.execute(Config.DB_SCHEMA_CREDENTIALS)
            
            cursor.execute(Config.DB_SCHEMA_REPLACEMENTS)
            cursor.execute(Config.DB_SCHEMA_HOTKEYS)
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    def initialize_services(self):
        """Initialize supported services in the database"""
        try:
            for code, service in Config.SUPPORTED_SERVICES.items():
                query = '''
                INSERT OR IGNORE INTO services (code, name, shortcut)
                VALUES (?, ?, ?)
                '''
                self.execute_query(query, (code, service['name'], service['shortcut']))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize services: {str(e)}")

    def get_services(self):
        """Get all configured services"""
        query = 'SELECT id, code, name, shortcut FROM services ORDER BY name'
        cursor = self.execute_query(query)
        return cursor.fetchall() if cursor else []
    
    def get_service_by_code(self, code):
        """Get service details by code"""
        query = 'SELECT id, code, name, shortcut FROM services WHERE code = ?'
        cursor = self.execute_query(query, (code,))
        return cursor.fetchone() if cursor else None
    
    def get_service_by_shortcut(self, shortcut):
        """Get service details by shortcut"""
        query = 'SELECT id, code, name, shortcut FROM services WHERE shortcut = ?'
        cursor = self.execute_query(query, (shortcut,))
        return cursor.fetchone() if cursor else None
    
    def get_credentials_by_service(self, service_id):
        """Get credentials for a specific service"""
        try:
            query = '''
            SELECT c.id, c.content, c.position, c.last_used
            FROM credentials c
            WHERE c.service_id = ?
            ORDER BY c.position
            '''
            cursor = self.execute_query(query, (service_id,))
            results = cursor.fetchall()
            return results
        except Exception as e:
            return []
    
    def save_credential(self, service_id, content, position=None):
        """Save a credential for a specific service"""
        if position is None:
            query = 'SELECT COALESCE(MAX(position), 0) + 1 FROM credentials WHERE service_id = ?'
            cursor = self.execute_query(query, (service_id,))
            position = cursor.fetchone()[0]
        
        query = '''
        INSERT INTO credentials (service_id, content, position)
        VALUES (?, ?, ?)
        '''
        self.execute_query(query, (service_id, content, position))

    def get_next_credential(self, shortcut):
        """Get next credential based on service shortcut"""
        try:
            cursor = self.conn.cursor()
            
            # Get service ID from shortcut
            service_query = 'SELECT id FROM services WHERE shortcut = ?'
            cursor.execute(service_query, (shortcut,))
            service_result = cursor.fetchone()
            
            if not service_result:
                return None
            
            service_id = service_result[0]
            
            # Get next credential for the specific service
            cursor.execute('''
                SELECT MAX(position) 
                FROM credentials 
                WHERE service_id = ? AND last_used IS NOT NULL
            ''', (service_id,))
            last_pos = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT id, content, position 
                FROM credentials 
                WHERE service_id = ? AND position > ? 
                ORDER BY position ASC 
                LIMIT 1
            ''', (service_id, last_pos))
            
            result = cursor.fetchone()
            if not result:
                cursor.execute('''
                    SELECT id, content, position 
                    FROM credentials 
                    WHERE service_id = ?
                    ORDER BY position ASC 
                    LIMIT 1
                ''', (service_id,))
                result = cursor.fetchone()
            
            if result:
                id_, content, _ = result
                cursor.execute('''
                    UPDATE credentials 
                    SET last_used = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (id_,))
                self.conn.commit()
                return content
                
            return None
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def execute_query(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Basic query execution with error handling"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise DatabaseError(f"Database error: {str(e)}")

    def execute_query_one(self, query: str, parameters: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a query and return a single row"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            self.conn.commit()
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def execute_many(self, query: str, parameters: List[tuple]) -> None:
        """Execute many operations in a single transaction"""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.executemany(query, parameters)
        except sqlite3.Error as e:
            print(f"Database error in batch operation: {e}")
            raise

    def get_all_shortcuts(self) -> List[Tuple[str, str]]:
        query = 'SELECT keyword, replacement FROM replacements ORDER BY keyword'
        cursor = self.execute_query(query)
        return cursor.fetchall() if cursor else []
    def get_shortcut(self, keyword: str) -> Optional[Tuple[str, str]]:
        query = 'SELECT keyword, replacement FROM replacements WHERE keyword = ?'
        cursor = self.execute_query(query, (keyword,))
        return cursor.fetchone() if cursor else None
    def save_shortcut(self, keyword: str, replacement: str):
        query = '''
        INSERT OR REPLACE INTO replacements (keyword, replacement, updated_at) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        self.execute_query(query, (keyword, replacement))
    def delete_credential(self, credential_id: int):
        """Delete a specific credential by ID and reorder positions"""
        query = 'DELETE FROM credentials WHERE id = ?'
        self.execute_query(query, (credential_id,))
        reorder_query = '''
            UPDATE credentials 
            SET position = (
                SELECT (SELECT COUNT(*) 
                       FROM credentials c2 
                       WHERE c2.position <= c1.position) 
                FROM credentials c1 
                WHERE c1.id = credentials.id
            )
        '''
        self.execute_query(reorder_query)
    def get_credential_by_id(self, credential_id: int):
        """Get credential details by ID"""
        query = 'SELECT id, email, password, position FROM credentials WHERE id = ?'
        cursor = self.execute_query(query, (credential_id,))
        return cursor.fetchone() if cursor else None
    def delete_shortcut(self, keyword: str):
        query = 'DELETE FROM replacements WHERE keyword = ?'
        self.execute_query(query, (keyword,))
    def get_shortcuts_dict(self) -> Dict[str, str]:
        shortcuts = self.get_all_shortcuts()
        return {keyword: replacement for keyword, replacement in shortcuts}
    def bulk_save_shortcuts(self, shortcuts: List[Tuple[str, str]]):
        query = '''
        INSERT OR REPLACE INTO replacements (keyword, replacement, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        try:
            with self.conn:
                self.conn.executemany(query, shortcuts)
        except sqlite3.Error as e:
            raise DatabaseError(f"Bulk save failed: {str(e)}")
    def clear_all_shortcuts(self):
        query = 'DELETE FROM replacements'
        self.execute_query(query)
    def backup_database(self, backup_path: str):
        try:
            with sqlite3.connect(backup_path) as backup:
                self.conn.backup(backup)
        except sqlite3.Error as e:
            raise DatabaseError(f"Backup failed: {str(e)}")
    def restore_database(self, backup_path: str):
        try:
            with sqlite3.connect(backup_path) as source:
                source.backup(self.conn)
        except sqlite3.Error as e:
            raise DatabaseError(f"Restore failed: {str(e)}")
    
    def load_credentials_from_file(self, file_path: str, service_id: int) -> int:
        """Load credentials from file and append to existing ones"""
        try:
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
            # Get max position for the specific service
            query = 'SELECT COALESCE(MAX(position), 0) FROM credentials WHERE service_id = ?'
            cursor = self.execute_query(query, (service_id,))
            last_position = cursor.fetchone()[0]
            
            # Prepare credentials with service_id
            credentials = [
                (service_id, content, last_position + pos + 1) 
                for pos, content in enumerate(lines)
            ]
            
            query = '''
            INSERT INTO credentials (service_id, content, position)
            VALUES (?, ?, ?)
            '''
            
            with self.conn:
                self.conn.executemany(query, credentials)
            return len(credentials)
            
        except Exception as e:
            raise DatabaseError(f"Failed to load credentials: {str(e)}")
    
    def get_current_credential_count(self) -> int:
        """Get count of currently loaded credentials"""
        query = 'SELECT COUNT(*) FROM credentials'
        cursor = self.execute_query(query)
        return cursor.fetchone()[0]
    
    def check_duplicate_credentials(self, service_id: int, new_credentials: List[str]) -> List[str]:
        """Check for duplicates between new and existing credentials"""
        query = 'SELECT content FROM credentials WHERE service_id = ?'
        cursor = self.execute_query(query, (service_id,))
        existing = {row[0] for row in cursor.fetchall()}
        duplicates = [cred for cred in new_credentials if cred in existing]
        return duplicates
    
    def reset_credential_usage(self, service_id: int = None):
        """Reset credentials usage tracking for a specific service or all services"""
        if service_id is None:
            query = 'UPDATE credentials SET last_used = NULL'
            self.execute_query(query)
        else:
            query = 'UPDATE credentials SET last_used = NULL WHERE service_id = ?'
            self.execute_query(query, (service_id,))
    
    def get_credentials_count(self, service_id=None) -> int:
        if service_id:
            query = 'SELECT COUNT(*) FROM credentials WHERE service_id = ?'
            cursor = self.execute_query(query, (service_id,))
        else:
            query = 'SELECT COUNT(*) FROM credentials'
            cursor = self.execute_query(query)
        
        return cursor.fetchone()[0] if cursor else 0

    
    def clear_all_credentials(self, service_id: int = None) -> bool:
        if service_id is None:
            query = 'DELETE FROM credentials'
            self.execute_query(query)
        else:
            query = 'DELETE FROM credentials WHERE service_id = ?'
            self.execute_query(query, (service_id,))
        return self.get_credentials_count(service_id) == 0
    
    def save_hotkey(self, key_combo: str, action_value: str, action_type: str):
        query = '''
        INSERT OR REPLACE INTO hotkeys (
            key_combo, 
            action_value, 
            action_type, 
            updated_at
        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        self.execute_query(query, (key_combo, action_value, action_type))
    
    def get_all_hotkeys(self):
        """Get all configured hotkeys"""
        query = '''
        SELECT key_combo, action_value, action_type 
        FROM hotkeys 
        ORDER BY created_at
        '''
        cursor = self.execute_query(query)
        return cursor.fetchall() if cursor else []
    
    def delete_hotkey(self, key_combo: str):
        """Delete a specific hotkey"""
        query = 'DELETE FROM hotkeys WHERE key_combo = ?'
        self.execute_query(query, (key_combo,))
    
    def get_hotkey(self, key_combo: str):
        """Get a specific hotkey configuration"""
        query = '''
        SELECT key_combo, action_type, action_value 
        FROM hotkeys 
        WHERE key_combo = ?
        '''
        cursor = self.execute_query(query, (key_combo,))
        return cursor.fetchone() if cursor else None

    def get_service_id_by_name(self, service_name: str) -> Optional[int]:
        """Get service ID efficiently"""
        try:
            query = "SELECT id FROM services WHERE name = ?"
            result = self.execute_query_one(query, (service_name,))
            return result['id'] if result else None
        except Exception as e:
            print(f"Error getting service ID: {e}")
            return None

    def optimized_load_credentials(self, service_id: int, credentials: List[tuple], batch_size: int = 1000) -> Tuple[int, int]:
        """
        Load credentials in batches with optimized performance
        Returns (added_count, duplicate_count)
        """
        try:
            # Get existing credentials in a single query
            query = "SELECT content FROM credentials WHERE service_id = ?"
            existing_contents = {
                row['content'] for row in self.execute_query(query, (service_id,)).fetchall()
            }
            
            # Get current max position
            query = "SELECT COALESCE(MAX(position), 0) FROM credentials WHERE service_id = ?"
            current_max = self.execute_query_one(query, (service_id,))
            position = (current_max[0] if current_max else 0) + 1
            
            # Prepare batches avoiding duplicates
            duplicates = 0
            to_insert = []
            
            for content in credentials:
                if content in existing_contents:
                    duplicates += 1
                    continue
                    
                to_insert.append((service_id, content, position))
                position += 1
                
                # Process in batches to avoid memory issues
                if len(to_insert) >= batch_size:
                    self._insert_credential_batch(to_insert)
                    to_insert = []
            
            # Insert remaining credentials
            if to_insert:
                self._insert_credential_batch(to_insert)
            
            return len(credentials) - duplicates, duplicates
            
        except Exception as e:
            print(f"Error in optimized load: {e}")
            raise

    def _insert_credential_batch(self, credentials: List[tuple]) -> None:
        """Insert a batch of credentials efficiently"""
        query = """
            INSERT INTO credentials (service_id, content, position)
            VALUES (?, ?, ?)
        """
        self.execute_many(query, credentials)

    def bulk_update_credentials(self, service_id: int, credential_updates: List[Dict]) -> None:
        """Bulk update credentials in a single transaction"""
        try:
            update_query = """
                UPDATE credentials 
                SET content = ?, 
                    position = ?,
                    last_used = ?
                WHERE id = ? AND service_id = ?
            """
            
            with self.conn:
                cursor = self.conn.cursor()
                cursor.executemany(update_query, [
                    (update['content'], update['position'], update.get('last_used'),
                     update['id'], service_id)
                    for update in credential_updates
                ])
        except sqlite3.Error as e:
            print(f"Error in bulk update: {e}")
            raise

    def get_credential_contents_by_service(self, service_id: int) -> List[str]:
        """Get all credential contents for a service efficiently"""
        try:
            query = "SELECT content FROM credentials WHERE service_id = ?"
            results = self.execute_query(query, (service_id,))
            return [row[0] for row in results]
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return []

    def batch_save_credentials(self, credentials: List[Dict]) -> None:
        """Save multiple credentials in a single transaction"""
        try:
            query = """
                INSERT INTO credentials (service_id, content, position)
                VALUES (?, ?, ?)
            """
            
            with self.conn:  # Start transaction
                cursor = self.conn.cursor()
                cursor.executemany(query, [
                    (cred['service_id'], cred['content'], cred['position'])
                    for cred in credentials
                ])
                
        except Exception as e:
            print(f"Error in batch save: {e}")
            raise

class DatabaseError(Exception):
    pass
