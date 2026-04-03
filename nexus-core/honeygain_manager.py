import httpx
import logging
import asyncio
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HoneygainManager')

class HoneygainManager:
    """Real-World Honeygain API Integration."""

    BASE_URL = "https://api.honeygain.com/api/v1"

    def __init__(self):
        self.token = None

    async def authenticate(self):
        """Authenticate with Honeygain using stored credentials."""
        creds = db_manager.get_credentials("honeygain")
        if not creds:
            logger.warning("No Honeygain credentials found in secure vault.")
            return False

        email = creds.get("email")
        password = creds.get("password")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/users/tokens",
                    json={"email": email, "password": password},
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("data", {}).get("access_token")
                    logger.info("Honeygain authentication successful.")
                    return True
                else:
                    logger.error(f"Honeygain auth failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Honeygain auth exception: {e}")
            return False

    async def fetch_balance(self):
        """Fetch real-time balance from Honeygain servers."""
        if not self.token:
            if not await self.authenticate():
                return None

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = await client.get(
                    f"{self.BASE_URL}/users/balances",
                    headers=headers,
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json().get("data", {})
                    # Honeygain uses credits: 1000 credits = $1
                    payout_data = data.get("payout", {})
                    credits = payout_data.get("credits", 0)
                    balance_usd = credits / 1000.0

                    # Update local cache
                    db_manager.update_cache("honeygain", balance_usd, float(credits))
                    return {"usd": balance_usd, "credits": credits}
                elif response.status_code == 401:
                    # Token expired?
                    self.token = None
                    return await self.fetch_balance()
                else:
                    logger.error(f"Honeygain fetch failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Honeygain fetch exception: {e}")
            return None

# Global instance
honeygain_manager = HoneygainManager()
