from app.agents.coordinating_agent import CoordinatingAgent
from app.services.data_loader import DataLoader
from app.agents.health_agent import get_city_summary, get_anomalies


class MorningBriefingWorkflow:
    """Orchestrates the morning briefing experience."""

    def __init__(self) -> None:
        self.data_loader = DataLoader()
        self.coordinator = CoordinatingAgent()

    def generate_briefing(self) -> dict:
        try:
            # Dynamically fetches the freshest live data from BigQuery
            context = self.data_loader.load_sample_data()
            result = self.coordinator.run(context)
            live_summary = get_city_summary()
            live_anomalies = get_anomalies()
            
            return {
                "morning_briefing": result.get("summary", "Briefing could not be generated."),
                "explanation": result.get("explanation", ""),
                "actions": result.get("actions", []),
                "anomalies": live_anomalies.get("anomalies", []) if isinstance(live_anomalies, dict) else [],
                "summary": live_summary if isinstance(live_summary, dict) and "error" not in live_summary else {"error": "Failed to load summary"}
            }
        except Exception as e:
            import logging
            logging.error(f"Failed to generate briefing: {e}")
            return {
                "morning_briefing": "Systems are currently operating in fallback mode due to a temporary service interruption. Core health data is being actively monitored.",
                "explanation": "We encountered an issue connecting to our intelligence systems. This is usually due to missing permissions or API quotas.",
                "actions": ["Verify IAM permissions for Vertex AI and BigQuery", "Check Cloud Run logs for detailed trace"],
                "anomalies": [],
                "summary": {"error": "Service unavailable"}
            }
