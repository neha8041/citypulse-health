import unittest
from unittest.mock import patch

from app.workflows.morning_briefing import MorningBriefingWorkflow


class MorningBriefingWorkflowTests(unittest.TestCase):
    @patch('app.workflows.morning_briefing.get_city_summary')
    @patch('app.workflows.morning_briefing.get_anomalies')
    @patch('app.workflows.morning_briefing.DataLoader.load_sample_data')
    @patch('app.workflows.morning_briefing.CoordinatingAgent.run')
    def test_generate_briefing(self, mock_run, mock_load, mock_anomalies, mock_summary) -> None:
        mock_load.return_value = {"date": "2026-07-04"}
        mock_run.return_value = {
            "summary": "Morning briefing summary",
            "explanation": "Explanation here",
            "actions": "Action items"
        }
        mock_summary.return_value = {"date": "Live Data"}
        mock_anomalies.return_value = {"anomalies": []}

        workflow = MorningBriefingWorkflow()
        result = workflow.generate_briefing()

        self.assertIn("morning_briefing", result)
        self.assertIn("explanation", result)
        self.assertIn("actions", result)


if __name__ == "__main__":
    unittest.main()
