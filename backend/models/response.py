"""Response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class TranscriptResponse(BaseModel):
    """Transcript response."""

    type: str = Field(default="transcript")
    text: str = Field(..., description="Transcribed text")


class EmotionResponse(BaseModel):
    """Emotion detection response."""

    type: str = Field(default="emotion")
    primary_emotion: str = Field(..., description="Detected emotion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    scores: Dict[str, float] = Field(..., description="All emotion scores")
    source_agreement: Optional[float] = Field(
        default=None, description="Agreement between speech and text emotion"
    )


class LLMResponse(BaseModel):
    """LLM response."""

    type: str = Field(default="response")
    text: str = Field(..., description="Generated response text")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    models_loaded: bool = Field(..., description="Whether all models are loaded")
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionResponse(BaseModel):
    """Session creation response."""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationTurn(BaseModel):
    """Single turn in conversation."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    emotion: Optional[Dict[str, Any]] = Field(
        default=None, description="Detected emotion (user turns only)"
    )
    timestamp: str = Field(..., description="ISO format timestamp")


class SessionHistoryResponse(BaseModel):
    """Session history response."""

    session_id: str = Field(..., description="Session identifier")
    created_at: str = Field(..., description="Session creation time")
    turns: List[ConversationTurn] = Field(..., description="Conversation turns")
    emotion_timeline: List[Dict[str, Any]] = Field(
        ..., description="Emotion detection history"
    )


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.now)
