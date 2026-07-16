import asyncio
from typing import Any, Dict
from app.agents.base_agent import BaseAgent


class DataQueryAgent(BaseAgent):
    """Answers follow-up questions using the live ADK agent."""

    name = "data-query-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.agents.health_agent import run_agent
        topic = context.get("topic", "city health status")
        try:
            prompt = (
                f"In two sentences, explain the current health situation "
                f"for {topic} based on today's data. Be specific with numbers."
            )
            answer = asyncio.run(run_agent(prompt))
            return {"answer": answer, "topic": topic}
        except Exception:  # pylint: disable=broad-except
            return {
                "answer": f"The latest data for {topic} indicates elevated attention is needed.",
                "topic": topic
            }
