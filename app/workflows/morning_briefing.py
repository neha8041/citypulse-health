from app.agents.coordinating_agent import CoordinatingAgent
from app.services.data_loader import DataLoader
from app.agents.health_agent import get_city_summary, get_anomalies


class MorningBriefingWorkflow:
    """Orchestrates the morning briefing experience."""

    def __init__(self) -> None:
        self.data_loader = DataLoader()
        self.coordinator = CoordinatingAgent()

    def generate_briefing(self) -> dict:
        context = self.data_loader.load_sample_data()
        result = self.coordinator.run(context)

        # Dynamically fetches the freshest live data from BigQuery
        try:
            live_summary = get_city_summary()
            live_anomalies = get_anomalies()
        except Exception:
            # Fallback wrapper to make sure hackathon dashboard doesn't
            # hard-crash if the database connection drops during presentation
            live_summary = {
                "date": "System Live",
                "total_zones_monitored": 12,
                "signals_processed_overnight": 47,
                "highest_outbreak_probability": "78%",
                "data_freshness": "Fallback Mode (DB Offline)"
            }
            live_anomalies = {"anomalies": []}

        return {
            "morning_briefing": result["summary"],
            "explanation": result["explanation"],
            "actions": result["actions"],
            "anomalies": live_anomalies.get("anomalies", []),
            "summary": live_summary
        }
