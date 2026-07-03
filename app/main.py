import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agents.health_agent import run_agent

app = FastAPI(
    title="CityPulse Health API",
    description="AI-powered city health decision intelligence platform",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
def root():
    return {"status": "CityPulse Health API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/briefing")
async def get_morning_briefing():
    """Generate the AI morning briefing from live BigQuery data"""
    try:
        response = await run_agent(
            "Generate the morning briefing for today. "
            "Check all anomalies and give me a full summary with recommendations."
        )
        return {"briefing": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Ask the health agent any question in plain English"""
    try:
        response = await run_agent(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies")
async def get_anomalies():
    """Get all current health anomalies across the city"""
    try:
        response = await run_agent(
            "List all current health anomalies across the city with details."
        )
        return {"anomalies": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Get detailed health status for a specific zone"""
    try:
        response = await run_agent(
            f"Give me the detailed health status for zone {zone_id}"
        )
        return {"zone_id": zone_id, "status": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alert/{zone_id}/{issue_type}")
async def draft_alert(zone_id: str, issue_type: str):
    """Draft a field team alert for a zone and issue type"""
    try:
        response = await run_agent(
            f"Draft a field team alert for {issue_type} in zone {zone_id}"
        )
        return {"zone_id": zone_id, "issue_type": issue_type, "alert": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
