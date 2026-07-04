"""Global exceptions for CityPulse Health."""

class CityPulseError(Exception):
    """Base exception for all CityPulse custom errors."""

class AgentExecutionError(CityPulseError):
    """Raised when the AI agent fails to execute properly."""

class DatabaseError(CityPulseError):
    """Raised when a database query fails."""
