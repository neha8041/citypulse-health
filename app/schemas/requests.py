"""Pydantic schemas for API requests."""
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Request payload for the chat endpoint."""
    message: str = Field(..., max_length=1000, description="The user's chat message.")
