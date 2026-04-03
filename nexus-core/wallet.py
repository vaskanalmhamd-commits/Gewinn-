import sqlite3
import threading
import os
from database import db_manager

# Sovereign Wallet Wrapper for $SOV and DePIN Tokens

def add_earnings(amount: float, source: str, asset: str = '$SOV', status: str = 'completed'):
    """Record earnings in the sovereign wallet."""
    db_manager.add_transaction(amount, source, asset, status)
    return db_manager.get_balance(asset)

def get_balance(asset: str = '$SOV'):
    """Retrieve balance for a specific asset."""
    return db_manager.get_balance(asset)

def get_transactions(limit: int = 50):
    """Retrieve recent transactions from the database."""
    with db_manager._lock:
        conn = sqlite3.connect(db_manager.DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, amount, source, asset, status FROM transactions ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def convert_to_sov(amount: float, from_asset: str):
    """
    Placeholder for currency conversion logic.
    In v1.0, we track tokens individually but show their $SOV equivalent.
    """
    rates = {
        "GRASS": 0.0001,
        "UPT": 0.001,
        "HONEY": 0.05,
        "NC": 0.005,
        "USDT": 1.0,
        "USDC": 1.0
    }
    rate = rates.get(from_asset.upper(), 0.0)
    return amount * rate

def get_total_sov_value():
    """Calculate total wallet value in $SOV equivalent."""
    # This would iterate through all unique assets and convert them
    # For now, we return the main $SOV balance plus a mock sum of others
    main_bal = get_balance('$SOV')
    return main_bal # Simplified for Phase 1
