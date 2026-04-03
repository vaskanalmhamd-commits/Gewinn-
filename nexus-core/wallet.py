import sqlite3
import threading
from database import db_manager

# This module is now a wrapper around db_manager for backward compatibility
# while I transition all calls to db_manager.

def init_db():
    pass

def add_earnings(amount, source, status='completed'):
    db_manager.add_transaction(amount, source, status)
    return db_manager.get_balance()

def get_balance(conn=None):
    return db_manager.get_balance()

def get_transactions(limit=50):
    with db_manager._lock:
        conn = sqlite3.connect(db_manager.DB_FILE if hasattr(db_manager, 'DB_FILE') else 'nexus-core/nexus.db')
        # Handle path differences if needed
        if not os.path.exists('nexus.db') and os.path.exists('nexus-core/nexus.db'):
             conn = sqlite3.connect('nexus-core/nexus.db')
        elif os.path.exists('nexus.db'):
             conn = sqlite3.connect('nexus.db')

        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, amount, source, status FROM transactions ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'timestamp': r[1], 'amount': r[2], 'source': r[3], 'status': r[4]} for r in rows]

def convert_grass_points(points):
    """Convert GRASS points to wallet balance."""
    # 1000 points = $0.10 (demo conversion)
    reward_amount = round(points * 0.0001, 5)
    if reward_amount > 0:
        add_earnings(reward_amount, "grass")
    return reward_amount

import os # Ensure os is available for the path check
