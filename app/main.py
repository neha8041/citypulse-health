from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.agents.chat_agent import ChatAgent
from app.workflows.morning_briefing import MorningBriefingWorkflow

app = FastAPI(title="CityPulse Health", version="0.1.0")
workflow = MorningBriefingWorkflow()
chat_agent = ChatAgent()

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str


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
