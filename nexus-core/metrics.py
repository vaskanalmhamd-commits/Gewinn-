import psutil
import logging
import sqlite3
import os
from datetime import datetime, timedelta

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Metrics')

DB_FILE = os.path.join(os.path.dirname(__file__), 'nexus.db')

def get_system_stats():
    """Retrieve CPU and RAM usage percentage."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}
    except:
        return {"cpu": 0, "ram": 0}

def get_rolling_24h_earnings():
    """Calculate real profits from the transactions table."""
    yesterday = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    try:
        if not os.path.exists(DB_FILE): return 0.0
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE timestamp >= ? AND amount > 0", (yesterday,))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0.0
    except Exception as e:
        logger.error(f"Error calculating 24h earnings: {e}")
        return 0.0

def get_total_earnings():
    """Calculate total real profits since start."""
    try:
        if not os.path.exists(DB_FILE): return 0.0
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0.0
    except Exception as e:
        logger.error(f"Error calculating total earnings: {e}")
        return 0.0
