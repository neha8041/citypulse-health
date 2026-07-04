import unittest
from unittest.mock import patch

from app.agents.chat_agent import ChatAgent


class ChatAgentTests(unittest.TestCase):
    @patch('app.agents.chat_agent.LLMClient.generate')
    def test_run_returns_reply(self, mock_generate) -> None:
        mock_generate.return_value = "Mock response: How is Zone 7 doing?"
        agent = ChatAgent()
        result = agent.run({"message": "How is Zone 7 doing?"})

        self.assertIn("reply", result)
        self.assertIn("How is Zone 7 doing?", result["reply"])


if __name__ == "__main__":
    unittest.main()
