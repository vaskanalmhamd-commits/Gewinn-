import httpx
import os
import json
import logging
import asyncio
from dotenv import load_dotenv

# Standard logging
logging.basicConfig(filename='honeygain_api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('HoneygainManager')

class HoneygainManager:
    def __init__(self):
        load_dotenv('config/keys.env')
        self.email = os.getenv('HONEYGAIN_EMAIL')
        self.password = os.getenv('HONEYGAIN_PASSWORD')
        self.token = None
        self.base_url = "https://api.honeygain.com/api/v1"

    async def login(self):
        """Request authentication token using email and password asynchronously."""
        if not (self.email and self.password):
            logger.error("Honeygain credentials not found in keys.env")
            return False

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/users/tokens"
                payload = {"email": self.email, "password": self.password}
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    self.token = response.json().get('data', {}).get('access_token')
                    logger.info("Successfully logged in to Honeygain")
                    return True
                else:
                    logger.error(f"Honeygain login failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error during Honeygain login: {str(e)}")
            return False

    async def get_balance(self):
        """Fetch current balance from Honeygain API asynchronously."""
        if not self.token and not await self.login():
            return {"error": "Authentication failed"}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/users/balances"
                headers = {"Authorization": f"Bearer {self.token}"}
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json().get('data', {})
                    credits = data.get('payout', {}).get('credits', 0)
                    usd_balance = credits / 1000.0
                    logger.info(f"Retrieved Honeygain balance: ${usd_balance}")
                    return {
                        "credits": credits,
                        "usd": usd_balance,
                        "raw": data
                    }
                elif response.status_code == 401:
                    # Retry login once if token expired
                    self.token = None
                    return await self.get_balance()
                else:
                    logger.error(f"Failed to fetch Honeygain balance: {response.status_code}")
                    return {"error": "API request failed"}
        except Exception as e:
            logger.error(f"Error fetching Honeygain balance: {str(e)}")
            return {"error": str(e)}

honeygain_manager = HoneygainManager()
