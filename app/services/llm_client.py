"""
LLM Client — wraps the CityPulse ADK agent.
All AI calls go through health_agent.run_agent()
which uses Vertex AI + Gemini 2.5 Flash via ADK.
"""
import asyncio
from app.agents.health_agent import run_agent


class LLMClient:
    """Real LLM client using Google ADK + Vertex AI + Gemini"""

    def __init__(self, api_key: str = "") -> None:
        # api_key kept for backward compatibility
        # actual auth is handled via GCP Application Default Credentials
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        """Synchronous wrapper around the async ADK agent"""
        return asyncio.run(run_agent(prompt))

    async def generate_async(self, prompt: str) -> str:
        """Async call to the ADK agent"""
        return await run_agent(prompt)
