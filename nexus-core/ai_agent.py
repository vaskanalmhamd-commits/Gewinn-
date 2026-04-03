import logging
import asyncio
import httpx
from key_manager import get_next_key
from database import db_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AIAgent')

class AIAgent:
    """The Master Brain responsible for task execution via micro-agents."""

    async def execute_task(self, command: dict):
        """
        Structured Command Interface (JSON).
        Example: {"agent": "AI", "action": "chat", "params": {"provider": "groq", "prompt": "Hello"}}
        """
        agent_type = command.get("agent")
        action = command.get("action")
        params = command.get("params", {})

        logger.info(f"Agent {agent_type} executing action: {action}")

        if agent_type == "AI":
            return await self.ai_micro_agent(action, params)
        elif agent_type == "DePIN":
            return await self.depin_micro_agent(action, params)
        else:
            return {"error": f"Unknown agent type: {agent_type}"}

    async def ai_micro_agent(self, action: str, params: dict):
        """Micro-agent for LLM interactions using Universal Key Manager."""
        provider = params.get("provider")
        prompt = params.get("prompt")

        # Get pre-configured Client from Key Manager
        client = get_next_key(provider)
        if not client:
            return {"error": f"No available keys for {provider}"}

        try:
            async with httpx.AsyncClient() as http_client:
                # Optimized for OpenAI-compatible APIs (Groq, OpenAI, etc.)
                payload = {
                    "model": params.get("model", "llama-3.1-8b-instant"),
                    "messages": [{"role": "user", "content": prompt}]
                }
                response = await http_client.post(
                    f"{client.base_url}/chat/completions",
                    headers=client.headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    client.report_success()
                    return {"success": True, "result": response.json()}
                elif response.status_code == 429:
                    client.report_failure(rate_limit=True)
                    return {"error": "Rate limit exceeded. Key rotated."}
                else:
                    client.report_failure()
                    return {"error": f"API Error: {response.status_code} - {response.text}"}

        except Exception as e:
            logger.error(f"AI Micro-Agent error: {e}")
            client.report_failure()
            return {"error": str(e)}

    async def depin_micro_agent(self, action: str, params: dict):
        """Micro-agent for managing DePIN workers."""
        from depin_manager import depin_manager
        platform = params.get("platform")

        if action == "restart":
            # Logic to restart a specific worker
            logger.info(f"Restarting DePIN worker: {platform}")
            return {"success": True, "message": f"Worker {platform} restart initiated"}
        elif action == "sync":
            depin_manager.sync_points()
            return {"success": True}
        return {"error": f"Unknown DePIN action: {action}"}

# Global instance
ai_agent = AIAgent()
