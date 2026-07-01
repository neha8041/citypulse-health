from app.agents.coordinating_agent import CoordinatingAgent
from app.services.data_loader import DataLoader


class MorningBriefingWorkflow:
    """Orchestrates the morning briefing experience."""

    def __init__(self) -> None:
        self.data_loader = DataLoader()
        self.coordinator = CoordinatingAgent()

    def generate_briefing(self) -> dict:
        context = self.data_loader.load_sample_data()
        result = self.coordinator.run(context)

        return {
            "morning_briefing": result["summary"],
            "explanation": result["explanation"],
            "actions": result["actions"],
        }
