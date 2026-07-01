from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class for all CityPulse Health agents."""

    name: str = "base-agent"

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent logic for the supplied context."""
        raise NotImplementedError
