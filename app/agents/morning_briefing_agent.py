import re
from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class MorningBriefingAgent(BaseAgent):
    """Creates a plain-English morning health briefing."""

    name = "morning-briefing-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Handle fallback mock format
        if "zone" in context:
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

        # Parse real city_summary BigQuery format
        highest_risk = context.get("highest_outbreak_probability", "Unknown")
        complaints = context.get("complaint_volume_change", "Unknown")
        maternal = context.get("maternal_appointment_change", "Unknown")

        try:
            match = re.search(r"(\d+(?:\.\d+)?)", highest_risk)
            risk_val = float(match.group(1)) if match else 0
        except Exception:
            risk_val = 0

        return {
            "summary": (
                f"Overnight, city-wide health signals were processed. "
                f"The highest outbreak probability detected is {highest_risk}, "
                f"with complaint volumes changing by {complaints}. "
                f"Maternal appointments showed a change of {maternal}. "
                f"Remediation protocols are advised."
            ),
            "risk_area": "City-Wide",
            "risk_level": "High" if risk_val >= 70 else "Medium",
        }
