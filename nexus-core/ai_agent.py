import logging
import asyncio
import httpx
from database import db_manager
from honeygain_manager import honeygain_manager
import task_scheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AIAgent')

class AIAgent:
    """The Intelligent Sovereign Agent: Responsive and Proactive."""

    async def execute_task(self, prompt: str):
        prompt_lower = prompt.lower()

        # 1. Real-Data Morning Briefing Request
        if "morning" in prompt_lower or "briefing" in prompt_lower or "report" in prompt_lower:
            return {"answer": task_scheduler.morning_briefing_cache}

        # 2. Real-Data Balance Query
        if "honeygain" in prompt_lower or "balance" in prompt_lower:
            data = db_manager.get_cache("honeygain")
            if data:
                usd = data.get("balance_usd", 0)
                credits = data.get("credits", 0)
                return {"answer": f"Your verified Honeygain balance is ${usd:.2f} ({credits:,.0f} credits)."}
            else:
                return {"answer": "I have no data yet. Please ensure the vault is unlocked and the account is connected."}

        # 3. Threshold / Goal Query
        if "goal" in prompt_lower or "withdraw" in prompt_lower:
            data = db_manager.get_cache("honeygain")
            if data:
                usd = data.get("balance_usd", 0)
                if usd >= 20.0:
                    return {"answer": "🏁 You have reached the $20 goal! Should I initiate the withdrawal process?"}
                else:
                    return {"answer": f"You are currently at ${usd:.2f}. You need ${(20-usd):.2f} more to reach the payout threshold."}

        # 4. Default
        return {"answer": "I am monitoring your Sovereign Machine. Ask me for your 'Morning Briefing' or your 'Balance'."}

# Global instance
ai_agent = AIAgent()
