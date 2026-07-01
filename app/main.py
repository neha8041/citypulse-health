from fastapi import FastAPI

from app.workflows.morning_briefing import MorningBriefingWorkflow

app = FastAPI(title="CityPulse Health", version="0.1.0")
workflow = MorningBriefingWorkflow()


@app.get("/")
async def root() -> dict:
    return {"message": "CityPulse Health API is running"}


@app.get("/briefing")
async def get_briefing() -> dict:
    return workflow.generate_briefing()
