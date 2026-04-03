import sqlite3
import threading

DB_FILE = 'nexus.db'
lock = threading.Lock()

def init_db():
    with lock:
        conn = sqlite3.connect(DB_FILE)
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount REAL,
            source TEXT,
            status TEXT
        )''')
        conn.commit()
        conn.close()

init_db()

def add_earnings(amount, source, status='completed'):
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO transactions (amount, source, status) VALUES (?, ?, ?)', (amount, source, status))
        conn.commit()
        balance = get_balance(conn)
        conn.close()
        return balance

def get_balance(conn=None):
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_FILE)
        close_conn = True
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM transactions')
    result = cursor.fetchone()[0] or 0.0
    if close_conn:
        conn.close()
    return result

def get_transactions(limit=50):
    with lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, amount, source, status FROM transactions ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'timestamp': r[1], 'amount': r[2], 'source': r[3], 'status': r[4]} for r in rows]