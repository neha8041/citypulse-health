from dataclasses import dataclass


@dataclass
class HealthSignal:
    """Represents a single health signal from the city data feed."""

    zone: str
    risk_level: str
    clinic_load: float
    maternal_care_drop: float
