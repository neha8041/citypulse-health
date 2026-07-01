from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class ActionAgent(BaseAgent):
    """Drafts recommended actions for the health briefing."""

    name = "action-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_area = context.get("risk_area", "the affected zone")
        risk_level = context.get("risk_level", "medium")

        return {
            "actions": [
                f"Escalate monitoring for {risk_area}.",
                f"Increase field response capacity for {risk_level} risk conditions.",
                "Prepare a public notice and internal alert if the trend continues.",
            ]
        }
