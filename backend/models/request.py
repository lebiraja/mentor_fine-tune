"""Request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class TextChatRequest(BaseModel):
    """Request for text-only chat."""

    text: str = Field(..., description="User's text input")
    session_id: Optional[str] = Field(
        default=None, description="Existing session ID (optional)"
    )


class SessionRequest(BaseModel):
    """Request to create a new session."""

    pass
