from typing import Any, Dict
from app.agents.base_agent import BaseAgent
from app.agents.health_agent import get_anomalies


class ActionAgent(BaseAgent):
    """Drafts recommended actions based on live anomaly data from BigQuery."""

    name = "action-agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            anomaly_data = get_anomalies()
            anomalies = anomaly_data.get("anomalies", [])

            if not anomalies:
                return {
                    "actions": [
                        "Continue routine monitoring across all 12 zones.",
                        "Review weekly vaccination coverage reports.",
                        "Confirm all zone data feeds are reporting correctly."
                    ]
                }

            actions = []
            for anomaly in anomalies:
                if anomaly["type"] == "DENGUE_RISK":
                    actions.append(
                        f"Deploy vector control teams to {anomaly['zone']} immediately "
                        f"— dengue probability at {anomaly['dengue_outbreak_probability']}."
                    )
                elif anomaly["type"] == "CLINIC_OVERLOAD":
                    actions.append(
                        f"Redirect non-critical cases away from {anomaly['zone']} "
                        f"— clinic running at {anomaly['utilization']} capacity."
                    )
                elif anomaly["type"] == "MATERNAL_CARE_DROP":
                    actions.append(
                        f"Launch ASHA worker outreach in {anomaly['zone']} "
                        f"— maternal appointments dropped by {anomaly['drop_percentage']}."
                    )

            return {"actions": actions}

        except Exception as e:  # pylint: disable=broad-except
            return {
                "actions": [
                    f"Unable to fetch live actions: {str(e)}",
                    "Please check BigQuery connectivity."
                ]
            }
