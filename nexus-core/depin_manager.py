import os
import asyncio
import logging
from database import db_manager
from depin_workers import UprockWorker, HivemapperWorker, GrassWorker, HoneygainWorker

# Set up logging for DePIN
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DePINManager')

class DePINManager:
    def __init__(self):
        self.workers = {
            "UPROCK": UprockWorker(),
            "Hivemapper": HivemapperWorker(),
            "GRASS": GrassWorker(),
            "Honeygain": HoneygainWorker()
        }
        self.active_tasks = {}

    def start_all(self):
        """Initialize and start all DePIN worker tasks."""
        logger.info("Initializing Real-World DePIN workers...")
        for name, worker in self.workers.items():
            if name not in self.active_tasks or self.active_tasks[name].done():
                self.active_tasks[name] = asyncio.create_task(worker.run())
                logger.info(f"Started worker task for: {name}")

    def get_status(self):
        """Return status of all DePIN processes from the database."""
        with db_manager._lock:
            import sqlite3
            conn = sqlite3.connect(db_manager.DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM depin_status")
            rows = cursor.fetchall()
            conn.close()

            status = {}
            for row in rows:
                status[row['network']] = {
                    "points": row['points'],
                    "status": row['status'],
                    "last_check": row['last_check'],
                    "failures": row['failure_count']
                }
            return status

    def sync_points(self):
        """Aggregate DePIN points and convert to wallet balance if threshold met."""
        # This will be called by the TaskQueue or Scheduler
        status = self.get_status()
        for net, data in status.items():
            points = data.get('points', 0)
            if points > 10 and net != "Honeygain": # Example threshold
                # Convert points to real balance
                reward = points * 0.01
                db_manager.add_transaction(reward, f"depin_sync_{net}")
                # Reset points in status table after sync
                db_manager.update_depin_status(net, points=0)
                logger.info(f"Synced {points} points from {net} to wallet.")
            elif net == "Honeygain" and points > 0:
                # Honeygain points are USD in my mock
                db_manager.add_transaction(0.01, "honeygain_heartbeat") # Small incremental reward
                logger.info("Honeygain heartbeat sync completed.")

depin_manager = DePINManager()
