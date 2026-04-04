import logging
import asyncio
from pyHoneygain import HoneyGain
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HoneygainManager')

class HoneygainManager:
    """Hardened Honeygain Integration using pyHoneygain."""

    def __init__(self):
        self.client = None

    async def authenticate(self):
        """Authenticate with Honeygain using credentials from the secure vault."""
        creds = db_manager.get_credentials("honeygain")
        if not creds:
            logger.warning("Vault LOCKED or Honeygain credentials missing.")
            return False

        email = creds.get("email")
        password = creds.get("password")

        try:
            self.client = await asyncio.to_thread(HoneyGain, email, password)
            logger.info("Honeygain (pyHoneygain) authentication successful.")
            return True
        except Exception as e:
            logger.error(f"Honeygain authentication failed: {e}")
            return False

    async def fetch_balance(self):
        """Fetch real-time balance."""
        if not self.client:
            if not await self.authenticate():
                return None

        try:
            balances = await asyncio.to_thread(self.client.balances)
            credits = balances.get('payout', {}).get('credits', 0)
            balance_usd = credits / 1000.0
            db_manager.update_cache("honeygain", balance_usd, float(credits))
            return {"usd": balance_usd, "credits": credits}
        except Exception as e:
            logger.error(f"Failed to fetch Honeygain data: {e}")
            self.client = None
            return None

# Global instance
honeygain_manager = HoneygainManager()
