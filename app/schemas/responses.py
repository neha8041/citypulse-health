"""Pydantic schemas for API responses."""
from pydantic import BaseModel

class ChatResponse(BaseModel):
    """Response payload for the chat endpoint."""
    reply: str

class BriefingResponse(BaseModel):
    """Response payload for the morning briefing endpoint."""
    briefing: str
