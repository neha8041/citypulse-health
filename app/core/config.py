"""Central configuration for CityPulse Health."""
import logging
import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("citypulse")

# Environment
APP_ENV: Final[str] = os.getenv("APP_ENV", "development")

# Google Cloud Project Config
PROJECT_ID: Final[str] = os.getenv("GCP_PROJECT_ID", "citypulse-health-2026")
DATASET_ID: Final[str] = os.getenv("BQ_DATASET_ID", "citypulse_health")

# Models
MODEL_NAME: Final[str] = os.getenv("MODEL_NAME", "gemini-2.0-flash")
