import unittest

from app.workflows.morning_briefing import MorningBriefingWorkflow


class MorningBriefingWorkflowTests(unittest.TestCase):
    def test_generate_briefing(self) -> None:
        workflow = MorningBriefingWorkflow()
        result = workflow.generate_briefing()

        self.assertIn("morning_briefing", result)
        self.assertIn("explanation", result)
        self.assertIn("actions", result)


if __name__ == "__main__":
    unittest.main()
