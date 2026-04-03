import sqlite3
import logging
import threading
import os
from datetime import datetime, timedelta
from security import security_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Database')

DB_FILE = os.path.join(os.path.dirname(__file__), 'nexus.db')

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.DB_FILE = DB_FILE
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Initialize the database schema for the Real-World Command Center."""
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()

            # 1. Transactions Table (Real historical data fetched from platforms)
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                asset TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'completed'
            )''')

            # 2. Encrypted Credentials Table (Real user logins)
            cursor.execute('''CREATE TABLE IF NOT EXISTS external_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL UNIQUE,
                encrypted_data TEXT NOT NULL,
                last_sync TEXT,
                status TEXT DEFAULT 'Disconnected'
            )''')

            # 3. Cache Table (For real-time balances to avoid heavy API hits)
            cursor.execute('''CREATE TABLE IF NOT EXISTS account_cache (
                platform TEXT PRIMARY KEY,
                balance_usd REAL DEFAULT 0.0,
                credits REAL DEFAULT 0.0,
                last_updated TEXT
            )''')

            conn.commit()
            conn.close()
            logger.info("Real-World Database schema initialized.")

    # --- Credential Operations ---
    def store_credentials(self, platform: str, raw_data: dict):
        """Encrypt and store credentials for a platform."""
        import json
        encrypted_text = security_manager.encrypt(json.dumps(raw_data))
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO external_credentials (platform, encrypted_data) VALUES (?, ?)",
                           (platform.lower(), encrypted_text))
            conn.commit()
            conn.close()

    def get_credentials(self, platform: str):
        """Fetch and decrypt credentials for a platform."""
        import json
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_data FROM external_credentials WHERE platform = ?", (platform.lower(),))
            row = cursor.fetchone()
            conn.close()

            if row:
                try:
                    decrypted_json = security_manager.decrypt(row[0])
                    return json.loads(decrypted_json)
                except Exception as e:
                    logger.error(f"Failed to decrypt credentials for {platform}: {e}")
                    return None
            return None

    # --- Cache Operations ---
    def update_cache(self, platform: str, balance: float, credits: float = 0.0):
        now = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO account_cache (platform, balance_usd, credits, last_updated) VALUES (?, ?, ?, ?)",
                           (platform.lower(), balance, credits, now))
            conn.commit()
            conn.close()

    def get_cache(self, platform: str = None):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if platform:
                cursor.execute("SELECT * FROM account_cache WHERE platform = ?", (platform.lower(),))
                row = cursor.fetchone()
                conn.close()
                return dict(row) if row else None
            else:
                cursor.execute("SELECT * FROM account_cache")
                rows = cursor.fetchall()
                conn.close()
                return [dict(r) for r in rows]

# Global instance
db_manager = DatabaseManager()
