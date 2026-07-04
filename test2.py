import asyncio
from app.agents.health_agent import get_city_summary, get_anomalies
try:
    print("City Summary:", get_city_summary())
except Exception as e:
    print("Error in City Summary:", type(e), e)

try:
    print("Anomalies:", get_anomalies())
except Exception as e:
    print("Error in Anomalies:", type(e), e)
