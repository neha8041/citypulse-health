"""
Data Loader Service — wraps the CityPulse data pipeline.
Real data loading is handled by data/data_loader.py which:
- Fetches real WHO indicators and stores in BigQuery
- Generates synthetic clinic metrics per zone
- Populates disease_signals and city_summary tables
"""
import sys
import os

from app.agents.health_agent import get_anomalies, get_city_summary, get_all_zones_summary

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../data'))
# pylint: disable=wrong-import-position,wrong-import-order
from data_loader import run as run_data_load

class DataLoader:
    """Real data loader connecting to BigQuery and WHO API"""

    def load_sample_data(self):
        """Returns latest city summary from BigQuery"""
        return get_city_summary()

    def load_all_zones(self):
        """Returns all zone health data from BigQuery"""
        return get_all_zones_summary()

    def load_anomalies(self):
        """Returns current anomalies from BigQuery"""
        return get_anomalies()

    def run_full_pipeline(self):
        """Runs the complete data ingestion pipeline"""
        run_data_load()
