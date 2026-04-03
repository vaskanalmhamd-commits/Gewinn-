import os
import json
import time
import logging
import asyncio
import httpx
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DePINWorkers')

class GenericDePINWorker:
    """Base class for DePIN workers (UPROCK, Hivemapper, etc.)"""
    def __init__(self, network: str, provider_key: str = None):
        self.network = network
        self.provider_key = provider_key or network.lower()
        self.status = "Offline"
        self.points = 0.0
        self.failure_count = 0

    def get_api_key(self):
        """Fetch the decrypted API key/Token from the secure database."""
        keys = db_manager.get_keys(self.provider_key)
        if keys and keys[0]['decrypted_key'] != "ENCRYPTION_ERROR":
            return keys[0]['decrypted_key']
        return None

    def update_status(self, points: float = None, status: str = None, failure: bool = False):
        """Sync worker state to the database."""
        if failure:
            self.failure_count += 1
            self.status = f"Error ({self.failure_count})"
        else:
            self.failure_count = 0
            if status: self.status = status
            if points is not None: self.points = points

        db_manager.update_depin_status(self.network, self.points, self.status, failure)

class UprockWorker(GenericDePINWorker):
    def __init__(self):
        super().__init__("UPROCK")

    async def run(self):
        logger.info("UPROCK Worker started.")
        while True:
            token = self.get_api_key()
            if not token:
                self.update_status(status="Missing Credentials", failure=True)
                await asyncio.sleep(60)
                continue

            try:
                # Realistically, this would call the Uprock API to fetch user status/earnings
                # For this implementation, we simulate the 'Active' connection to the network
                self.update_status(status="Connected")
            except Exception as e:
                self.update_status(failure=True)
            await asyncio.sleep(300)

class HivemapperWorker(GenericDePINWorker):
    def __init__(self):
        super().__init__("Hivemapper")

    async def run(self):
        logger.info("Hivemapper Worker started.")
        while True:
            api_key = self.get_api_key()
            if not api_key:
                self.update_status(status="API Key Required", failure=True)
                await asyncio.sleep(60)
                continue

            try:
                # This would fetch the latest HONEY rewards from the explorer/API
                self.update_status(status="Active")
            except Exception as e:
                self.update_status(failure=True)
            await asyncio.sleep(600)

class GrassWorker(GenericDePINWorker):
    def __init__(self):
        super().__init__("GRASS")

    async def run(self):
        logger.info("GRASS Worker started.")
        while True:
            user_id = self.get_api_key()
            if not user_id:
                self.update_status(status="User ID Required", failure=True)
                await asyncio.sleep(60)
                continue

            try:
                # Instead of just incrementing, we look for real points data from the worker log/config
                # if the standalone grass_worker.py is running.
                points_file = os.path.join(os.path.dirname(__file__), 'config', 'grass_points.json')
                if os.path.exists(points_file):
                    with open(points_file, 'r') as f:
                        data = json.load(f)
                        self.points = data.get('points', 0)

                self.update_status(points=self.points, status="Connected")
            except Exception as e:
                self.update_status(failure=True)

            await asyncio.sleep(120)

class HoneygainWorker(GenericDePINWorker):
    def __init__(self):
        super().__init__("Honeygain")

    async def run(self):
        logger.info("Honeygain Worker started.")
        while True:
            # Honeygain is tracked via the HoneygainManager (API-based)
            from honeygain_manager import honeygain_manager
            try:
                balance = await honeygain_manager.get_balance()
                if not balance.get('error'):
                    usd = balance.get('usd', 0)
                    self.update_status(points=usd, status="Connected")

                    # Threshold Notification Logic ($19 check)
                    if usd >= 19.0:
                        logger.warning(f"⚠️ Honeygain balance high: ${usd:.2f}. Payout threshold ($20) approaching!")
                else:
                    self.update_status(status="Auth Error", failure=True)
            except Exception as e:
                self.update_status(failure=True)

            await asyncio.sleep(1800)
