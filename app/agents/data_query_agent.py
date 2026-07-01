from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class DataQueryAgent(BaseAgent):
    """Answers follow-up questions using the available context."""

    name = "data-query-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        topic = context.get("topic", "public health")
        return {
            "answer": f"The latest data for {topic} indicates elevated attention is needed.",
            "topic": topic,
        }
