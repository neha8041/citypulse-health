import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.agents.chat_agent import ChatAgent
from app.workflows.morning_briefing import MorningBriefingWorkflow

app = FastAPI(title="CityPulse Health", version="0.1.0")
workflow = MorningBriefingWorkflow()
chat_agent = ChatAgent()

STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc)
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    )

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str

class AlertRequest(BaseModel):
    """Request model for draft alert."""
    zone_id: str
    issue_type: str


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.get("/api/health")
async def health() -> dict:
    return {"message": "CityPulse Health API is running"}


@app.get("/api/briefing")
def get_briefing() -> dict:
    """Generate the morning briefing."""
    return workflow.generate_briefing()


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    """Process a chat message."""
    return chat_agent.run({"message": payload.message})

@app.post("/api/alert")
def draft_alert(payload: AlertRequest) -> dict:
    """Draft a field alert directly without going through the agent."""
    from app.agents.health_agent import draft_field_alert
    return draft_field_alert(payload.zone_id, payload.issue_type)

@app.get("/api/alert/{zone_id}/{issue_type}")
def draft_alert_get(zone_id: str, issue_type: str) -> dict:
    """Draft a field alert via GET for easy frontend integration."""
    from app.agents.health_agent import draft_field_alert
    return draft_field_alert(zone_id, issue_type)

@app.get("/api/zones")
def get_all_zones() -> dict:
    """Return all zones with current health status for the heatmap."""
    from app.agents.health_agent import get_all_zones_summary
    return get_all_zones_summary()

@app.get("/api/zones/{zone_id}")
def get_zone(zone_id: str) -> dict:
    """Return detailed health status for a specific zone."""
    from app.agents.health_agent import get_zone_health_status
    return get_zone_health_status(zone_id)

@app.get("/api/trends/{zone_id}/{metric}")
def get_trends(zone_id: str, metric: str) -> dict:
    """Return last 7 days of a metric for a zone for trend chart."""
    from app.agents.health_agent import _get_bq_client
    valid_metrics = {
        "dengue_risk": "d.dengue_risk_score",
        "utilization": "c.utilization_rate",
        "complaints": "d.complaint_count",
        "maternal": "d.maternal_appointments",
        "aqi": "d.aqi",
        "vaccination": "d.vaccination_coverage"
    }
    if metric not in valid_metrics:
        return {"error": f"Invalid metric. Choose from: {list(valid_metrics.keys())}"}

    col = valid_metrics[metric]
    query = f"""
        SELECT
            DATE(d.recorded_at) as date,
            AVG({col}) as value
        FROM `citypulse-health-2026.citypulse_health.disease_signals` d
        JOIN `citypulse-health-2026.citypulse_health.clinic_metrics` c
            ON d.zone_id = c.zone_id
            AND DATE(d.recorded_at) = DATE(c.recorded_at)
        WHERE d.zone_id = '{zone_id}'
        AND d.recorded_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY date
        ORDER BY date ASC
    """
    try:
        results = _get_bq_client().query(query).result()
        data = [{"date": str(r["date"]), "value": round(float(r["value"]), 4)}
                for r in results]
        return {
            "zone_id": zone_id,
            "metric": metric,
            "data": data,
            "data_points": len(data)
        }
    except Exception as e:  # pylint: disable=broad-except
        return {"error": str(e)}
