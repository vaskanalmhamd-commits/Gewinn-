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
        """Initialize the database schema."""
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()

            # 1. Wallet & Transactions ($SOV and other assets)
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                asset TEXT DEFAULT '$SOV',
                status TEXT DEFAULT 'completed'
            )''')

            # 2. Encrypted Keys (Universal Key Manager)
            cursor.execute('''CREATE TABLE IF NOT EXISTS encrypted_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                encrypted_key TEXT NOT NULL,
                base_url TEXT,
                fail_count INTEGER DEFAULT 0,
                suspended_until TEXT,
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

            # 4. Withdrawals Tracking
            cursor.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
                id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                asset TEXT NOT NULL,
                address TEXT NOT NULL,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

            # 5. Sovereign Task Scheduler (Persistence)
            cursor.execute('''CREATE TABLE IF NOT EXISTS task_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT UNIQUE NOT NULL,
                interval_minutes INTEGER NOT NULL,
                last_run TEXT,
                enabled INTEGER DEFAULT 1
            )''')

            conn.commit()
            conn.close()
            logger.info("Sovereign Database schema initialized successfully.")

    # --- Wallet Operations ---
    def add_transaction(self, amount: float, source: str, asset: str = '$SOV', status: str = 'completed'):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (amount, source, asset, status) VALUES (?, ?, ?, ?)",
                           (amount, source, asset, status))
            conn.commit()
            conn.close()

    def get_balance(self, asset: str = '$SOV') -> float:
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE asset = ?", (asset,))
            balance = cursor.fetchone()[0]
            conn.close()
            return balance if balance else 0.0

    # --- Encrypted Key Operations ---
    def add_key(self, provider: str, raw_key: str, base_url: str = None):
        encrypted_key = security_manager.encrypt(raw_key)
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO encrypted_keys (provider, encrypted_key, base_url) VALUES (?, ?, ?)",
                           (provider.lower(), encrypted_key, base_url))
            conn.commit()
            conn.close()

    def get_keys(self, provider: str = None):
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if provider:
                cursor.execute("SELECT * FROM encrypted_keys WHERE provider = ?", (provider.lower(),))
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

    def update_key_health(self, key_id: int, failure: bool = False, rate_limit: bool = False):
        """Implement Exponential Backoff suspension for keys."""
        now = datetime.now()
        suspended_until = None

        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()

            if failure:
                cursor.execute("SELECT fail_count FROM encrypted_keys WHERE id = ?", (key_id,))
                row = cursor.fetchone()
                fail_count = (row[0] or 0) + 1

                # Logic: 1h -> 4h -> 24h
                if rate_limit:
                    delta_sec = 300 # 5 minutes
                elif fail_count == 1:
                    delta_sec = 3600 # 1 hour
                elif fail_count == 2:
                    delta_sec = 14400 # 4 hours
                else:
                    delta_sec = 86400 # 24 hours

                suspended_until = (now + timedelta(seconds=delta_sec)).isoformat()

                cursor.execute("UPDATE encrypted_keys SET fail_count = ?, suspended_until = ? WHERE id = ?",
                               (fail_count, suspended_until, key_id))
            else:
                # Success - reset health
                cursor.execute("UPDATE encrypted_keys SET fail_count = 0, suspended_until = NULL, last_used = ? WHERE id = ?",
                               (now.isoformat(), key_id))

            conn.commit()
            conn.close()

    # --- DePIN Status Operations ---
    def update_depin_status(self, network: str, points: float = None, status: str = None, failure: bool = False):
        now = datetime.now().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
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
