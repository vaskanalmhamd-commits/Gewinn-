import logging
import asyncio
import httpx
import json
from key_manager import get_next_key
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AIAgent')

class AIAgent:
    """The Sovereign AI Agent: Interprets NL and executes structured tasks."""

    def __init__(self):
        self.context = {}

    async def execute_task(self, prompt: str):
        """
        High-level interface: Converts Natural Language to Action.
        In v1.0, we use a hybrid approach: string matching for efficiency,
        with LLM fallback for complex logic.
        """
        prompt_lower = prompt.lower()

        # 1. Quick Action Routing (The Sovereign Command Set)
        if "earn" in prompt_lower or "profit" in prompt_lower:
            from metrics import get_rolling_24h_earnings
            val = get_rolling_24h_earnings()
            return {"answer": f"In the last 24 hours, you have earned ${val:.4f} $SOV."}

        elif "withdraw" in prompt_lower:
            # NL: "withdraw 10 USDT to 0x..."
            # For simplicity, we return the instruction to use the form
            # or extract params if using a specialized micro-agent
            return {"answer": "I have received your withdrawal request. Please confirm the details in the Withdrawal Gateway."}

        elif "status" in prompt_lower and "grass" in prompt_lower:
            from depin_manager import depin_manager
            status = depin_manager.get_status().get('GRASS', {})
            return {"answer": f"GRASS node status: {status.get('status', 'Offline')}. points: {status.get('points', 0)}"}

        # 2. LLM Fallback (Autonomous Decision Making)
        # We use the Internal AI Micro-Agent to 'think' about the prompt
        thinking_result = await self.ai_micro_agent("chat", {
            "provider": "groq",
            "prompt": f"Act as the Sovereign Agent for Gewinn. The user said: '{prompt}'. Provide a concise, professional response based on your role as an autonomous earning manager."
        })

        if thinking_result.get("success"):
            return {"answer": thinking_result['result']['choices'][0]['message']['content']}
        else:
            return {"answer": "I am processing your request through the secure gateway, but the AI provider is currently unreachable. Please check your API keys."}

    async def ai_micro_agent(self, action: str, params: dict):
        """Micro-agent for LLM interactions using Universal Key Manager."""
        provider = params.get("provider", "groq")
        prompt = params.get("prompt")

        # Get pre-configured Client from Key Manager
        client = get_next_key(provider)
        if not client:
            return {"error": f"No available keys for {provider}"}

        try:
            async with httpx.AsyncClient() as http_client:
                # Optimized for OpenAI-compatible APIs
                payload = {
                    "model": params.get("model", "llama-3.1-8b-instant"),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                response = await http_client.post(
                    f"{client.base_url}/chat/completions",
                    headers=client.headers,
                    json=payload,
                    timeout=15.0
                )

                if response.status_code == 200:
                    client.report_success()
                    return {"success": True, "result": response.json()}
                elif response.status_code == 429:
                    client.report_failure(rate_limit=True)
                    return {"error": "Rate limit exceeded. Key rotated."}
                else:
                    client.report_failure()
                    return {"error": f"API Error: {response.status_code}"}

        except Exception as e:
            logger.error(f"AI Micro-Agent exception: {e}")
            client.report_failure()
            return {"error": str(e)}

# Global instance
ai_agent = AIAgent()
