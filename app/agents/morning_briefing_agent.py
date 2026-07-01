from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class MorningBriefingAgent(BaseAgent):
    """Creates a plain-English morning health briefing."""

    name = "morning-briefing-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        zone = context.get("zone", "Unknown Zone")
        risk_level = context.get("risk_level", "medium")
        clinic_load = context.get("clinic_load", 0.0)

        return {
            "summary": (
                f"Overnight, {zone} showed a {risk_level} health risk. "
                f"Clinic utilization is at {clinic_load:.0%}, which warrants attention."
            ),
            "risk_area": zone,
            "risk_level": risk_level,
        }
