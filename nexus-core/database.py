import sqlite3
import logging
import threading
import os
from datetime import datetime
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
        """Initialize the database schema."""
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()

            # 1. Wallet & Transactions
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                status TEXT DEFAULT 'completed'
            )''')

            # 2. Encrypted Keys (Master Password Protected)
            cursor.execute('''CREATE TABLE IF NOT EXISTS encrypted_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                encrypted_key TEXT NOT NULL,
                last_used TEXT,
                remaining_quota INTEGER DEFAULT 1000
            )''')

            # 3. DePIN Status Monitoring
            cursor.execute('''CREATE TABLE IF NOT EXISTS depin_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                network TEXT UNIQUE NOT NULL,
                points REAL DEFAULT 0,
                status TEXT DEFAULT 'Offline',
                last_check TEXT,
                failure_count INTEGER DEFAULT 0
            )''')

            # 4. Withdrawals (Helio/On-chain Tracking)
            cursor.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
                id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                asset TEXT NOT NULL,
                address TEXT NOT NULL,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

            conn.commit()
            conn.close()
            logger.info("Database schema initialized successfully.")

    # --- Wallet Operations ---
    def add_transaction(self, amount: float, source: str, status: str = 'completed'):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (amount, source, status) VALUES (?, ?, ?)", (amount, source, status))
            conn.commit()
            conn.close()

    def get_balance(self) -> float:
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM transactions")
            balance = cursor.fetchone()[0]
            conn.close()
            return balance if balance else 0.0

    # --- Encrypted Key Operations ---
    def add_key(self, provider: str, raw_key: str):
        encrypted_key = security_manager.encrypt(raw_key)
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO encrypted_keys (provider, encrypted_key) VALUES (?, ?)", (provider.lower(), encrypted_key))
            conn.commit()
            conn.close()

    def get_keys(self, provider: str = None):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if provider:
                cursor.execute("SELECT * FROM encrypted_keys WHERE provider = ? ORDER BY last_used ASC", (provider.lower(),))
            else:
                cursor.execute("SELECT * FROM encrypted_keys")

            rows = cursor.fetchall()
            keys = []
            for row in rows:
                k = dict(row)
                try:
                   k['decrypted_key'] = security_manager.decrypt(k['encrypted_key'])
                except:
                   k['decrypted_key'] = "ENCRYPTION_ERROR"
                keys.append(k)
            conn.close()
            return keys

    # --- DePIN Status Operations ---
    def update_depin_status(self, network: str, points: float = None, status: str = None, failure: bool = False):
        now = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()

            # Update existing or insert new
            cursor.execute("SELECT id, failure_count FROM depin_status WHERE network = ?", (network,))
            row = cursor.fetchone()

            if row:
                f_count = row[1] + 1 if failure else 0
                update_fields = ["last_check = ?", "failure_count = ?"]
                params = [now, f_count]

                if points is not None:
                    update_fields.append("points = ?")
                    params.append(points)
                if status:
                    update_fields.append("status = ?")
                    params.append(status)

                params.append(network)
                query = f"UPDATE depin_status SET {', '.join(update_fields)} WHERE network = ?"
                cursor.execute(query, tuple(params))
            else:
                f_count = 1 if failure else 0
                cursor.execute("INSERT INTO depin_status (network, points, status, last_check, failure_count) VALUES (?, ?, ?, ?, ?)",
                               (network, points or 0, status or 'Connected', now, f_count))

            conn.commit()
            conn.close()

    # --- Withdrawal Operations ---
    def record_withdrawal(self, w_id: str, amount: float, asset: str, address: str, tx_hash: str = None, status: str = 'pending'):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO withdrawals (id, amount, asset, address, tx_hash, status) VALUES (?, ?, ?, ?, ?, ?)",
                           (w_id, amount, asset, address, tx_hash, status))
            conn.commit()
            conn.close()

    def get_withdrawals(self, limit: int = 50):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM withdrawals ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

# Global instance
db_manager = DatabaseManager()
