import os
from pathlib import Path

class Config:

    APP_NAME = "TEXT CHANGER"
    VERSION = "4.4.0"
    AUTHOR = "AJU"
    
    WINDOW_SIZE = "1000x600"
    MIN_WIDTH = 1000
    MIN_HEIGHT = 600
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    ASSETS_DIR = BASE_DIR / 'assets'
    
    DB_PATH = DATA_DIR / 'replacements.db'
    ASSETS_DIR = BASE_DIR / 'assets'
    ICON_PATH = ASSETS_DIR / 'icon.ico'
    
    SUPPORTED_SERVICES = {
        'netflix': {
            'name': 'Netflix',
            'shortcut': '@nf',
            'icon': 'netflix.ico'
        },
        'hotstar': {
            'name': 'Disney+ Hotstar',
            'shortcut': '@dh',
            'icon': 'hotstar.ico'
        },
    }

    DB_SCHEMA_REPLACEMENTS = """
    CREATE TABLE IF NOT EXISTS replacements (
        keyword TEXT PRIMARY KEY,
        replacement TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    DB_SCHEMA_HOTKEYS = '''
    CREATE TABLE IF NOT EXISTS hotkeys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_combo TEXT NOT NULL,
        action_type TEXT NOT NULL,
        action_value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    DB_SCHEMA_CREDENTIALS = """
    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        position INTEGER NOT NULL,
        last_used TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    DB_SCHEMA_SERVICES = """
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        shortcut TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    DB_SCHEMA_CREDENTIALS = """
    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        position INTEGER NOT NULL,
        last_used TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id)
    )
    """

    MAX_BUFFER_SIZE = 50
    REPLACE_DELAY = 0.002
    
    @classmethod
    def initialize(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_resource_path(cls, resource_name):
        return cls.ASSETS_DIR / resource_name
    
    @classmethod
    def get_data_path(cls, filename):
        return cls.DATA_DIR / filename
