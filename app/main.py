import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.agents.health_agent import run_agent
from app.core.config import logger
from app.core.exceptions import AgentExecutionError, CityPulseError
from app.schemas.requests import ChatRequest
from app.schemas.responses import BriefingResponse, ChatResponse
from app.services.cache import briefing_cache

app = FastAPI(title="CityPulse Health", version="0.2.0")

STATIC_DIR = Path(__file__).parent / "static"


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    logger.info("Received request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        "Completed %s %s in %.3fs with status %s",
        request.method,
        request.url.path,
        process_time,
        response.status_code,
    )
    return response


@app.exception_handler(CityPulseError)
async def citypulse_exception_handler(_request: Request, exc: CityPulseError):
    logger.error("CityPulseError: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal error occurred during agent execution."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled Exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.get("/api/health")
async def health() -> dict:
    return {"message": "CityPulse Health API is running securely."}


@app.get("/briefing", response_model=BriefingResponse)
async def get_briefing() -> BriefingResponse:
    """Generate the morning briefing using cached ADK agent."""
    logger.info("Generating morning briefing via AI")

    async def generate_briefing_prompt():
        return await run_agent(
            "Provide a comprehensive morning health briefing summarizing anomalies "
            "and overall city health metrics. Format it clearly for a busy health official."
        )

    result = await briefing_cache.get_or_set("daily_briefing", generate_briefing_prompt)
    return BriefingResponse(briefing=result)


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Process a chat message using the ADK agent."""
    logger.info("Processing chat message of length %d", len(payload.message))
    try:
        reply = await run_agent(payload.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise AgentExecutionError(f"Failed to run agent: {e}") from e
