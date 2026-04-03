import logging
import asyncio
import os
from simplepyq import SimplePyQ

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TaskQueue')

QUEUE_DB = os.path.join(os.path.dirname(__file__), 'tasks.db')

class QueueManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
            cls._instance.pyq = SimplePyQ(QUEUE_DB)
            cls._instance._setup_channels()
        return cls._instance

    def _setup_channels(self):
        """Register the processing functions for different channels."""
        self.pyq.add_channel("withdrawals", self._process_withdrawal_task)
        self.pyq.add_channel("depin_sync", self._process_depin_sync_task)
        logger.info("Task queue channels registered.")

    def add_task(self, channel: str, data: dict):
        """Enqueue a task to the persistent SQLite store."""
        self.pyq.enqueue(channel, data)
        logger.info(f"Task enqueued in channel: {channel}")

    def start_worker(self):
        """Start the background task scheduler."""
        self.pyq.start()
        logger.info("Task queue worker started.")

    def stop_worker(self):
        self.pyq.stop()

    def _process_withdrawal_task(self, data):
        """Sync function called by SimplePyQ worker."""
        logger.info(f"Processing withdrawal: {data}")
        import withdraw
        # SimplePyQ worker context: need to bridge to async if using httpx
        try:
            asyncio.run(withdraw.process_helio_withdrawal(data))
        except Exception as e:
            logger.error(f"Error in async bridge for withdrawal task: {e}")

    def _process_depin_sync_task(self, data):
        logger.info("Syncing DePIN points...")
        # depin_manager.sync_points()
        pass

# Global instance
queue_manager = QueueManager()
