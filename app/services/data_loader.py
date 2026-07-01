from typing import Any, Dict


class DataLoader:
    """Placeholder data loader for city health datasets."""

    def load_sample_data(self) -> Dict[str, Any]:
        return {
            "zone": "Zone 7",
            "risk_level": "high",
            "clinic_load": 0.92,
            "maternal_care_drop": 0.18,
        }
