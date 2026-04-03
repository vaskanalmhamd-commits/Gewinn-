import logging
import asyncio
import httpx
import json
from database import db_manager
from honeygain_manager import honeygain_manager

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AIAgent')

class AIAgent:
    """The Intelligent Agent: Powered by Real-World Data."""

    async def execute_task(self, prompt: str):
        prompt_lower = prompt.lower()

        # 1. Real-Data Logic (High Precision)
        if "honeygain" in prompt_lower or "balance" in prompt_lower:
            data = await honeygain_manager.fetch_balance()
            if not data:
                # Fallback to cache
                data = db_manager.get_cache("honeygain")

            if data:
                usd = data.get("usd") or data.get("balance_usd")
                credits = data.get("credits")
                return {"answer": f"Your current Honeygain balance is ${usd:.2f} ({credits:,.0f} credits)."}
            else:
                return {"answer": "I couldn't fetch your balance. Please ensure your Honeygain account is connected."}

        if "threshold" in prompt_lower or "withdraw" in prompt_lower:
            data = db_manager.get_cache("honeygain")
            if data:
                usd = data.get("balance_usd", 0)
                remaining = max(0, 20.0 - usd)
                if remaining == 0:
                    return {"answer": "You have reached the $20 threshold! You can now initiate a withdrawal via PayPal."}
                else:
                    return {"answer": f"You are currently at ${usd:.2f}. You need ${remaining:.2f} more to reach the $20 withdrawal threshold."}

        # 2. General Knowledge / Scouting Fallback
        return {"answer": "I am monitoring your real-world earnings. Ask me about your Honeygain balance or withdrawal threshold."}

# Global instance
ai_agent = AIAgent()
