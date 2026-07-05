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
