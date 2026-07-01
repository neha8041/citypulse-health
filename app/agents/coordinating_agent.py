from typing import Any, Dict

from app.agents.action_agent import ActionAgent
from app.agents.data_query_agent import DataQueryAgent
from app.agents.morning_briefing_agent import MorningBriefingAgent
from app.agents.base_agent import BaseAgent


class CoordinatingAgent(BaseAgent):
    """Main coordinator that routes the morning briefing flow across specialist agents."""

    name = "coordinating-agent"

    def __init__(self) -> None:
        self.morning_agent = MorningBriefingAgent()
        self.query_agent = DataQueryAgent()
        self.action_agent = ActionAgent()

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        briefing = self.morning_agent.run(context)
        explanation = self.query_agent.run({"topic": briefing.get("risk_area", "public health")})
        actions = self.action_agent.run(briefing)

        return {
            "summary": briefing.get("summary", "No briefing available."),
            "explanation": explanation.get("answer", "No explanation available."),
            "actions": actions.get("actions", []),
            "risk_area": briefing.get("risk_area"),
            "risk_level": briefing.get("risk_level"),
        }
