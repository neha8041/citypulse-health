from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.services.llm_client import LLMClient


class ChatAgent(BaseAgent):
    """Answers free-form chat questions from the UI.

    Backed by the placeholder LLMClient for now — swap LLMClient.generate()
    for a real model call once the hackathon demo needs real answers.
    """

    name = "chat-agent"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        message = context.get("message", "")
        return {"reply": self.llm_client.generate(message)}
