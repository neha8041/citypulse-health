import unittest

from app.agents.chat_agent import ChatAgent


class ChatAgentTests(unittest.TestCase):
    def test_run_returns_reply(self) -> None:
        agent = ChatAgent()
        result = agent.run({"message": "How is Zone 7 doing?"})

        self.assertIn("reply", result)
        self.assertIn("How is Zone 7 doing?", result["reply"])


if __name__ == "__main__":
    unittest.main()
