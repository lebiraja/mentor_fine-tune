"""REST API endpoints."""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.models.request import TextChatRequest, SessionRequest
from backend.models.response import (
    HealthResponse,
    SessionResponse,
    SessionHistoryResponse,
    ConversationTurn,
    ErrorResponse,
)
from backend.core.exceptions import SessionError

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    from backend import main

    return HealthResponse(
        status="healthy" if main.model_service.is_loaded() else "initializing",
        models_loaded=main.model_service.is_loaded(),
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest = None):
    """Create a new conversation session."""
    from backend import main

    session_id = main.session_service.create_session()
    return SessionResponse(session_id=session_id)


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    from backend import main

    try:
        history = main.session_service.get_history(session_id)
        emotion_history = main.session_service.get_session(session_id).emotion_history

        turns = [
            ConversationTurn(
                role=item["role"],
                content=item["content"],
                emotion=item.get("emotion"),
                timestamp=item.get("timestamp", ""),
            )
            for item in history
        ]

        session = main.session_service.get_session(session_id)
        return SessionHistoryResponse(
            session_id=session_id,
            created_at=session.created_at.isoformat(),
            turns=turns,
            emotion_timeline=emotion_history,
        )

    except SessionError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/text-chat")
async def text_chat(request: TextChatRequest):
    """Text-only chat endpoint (optional)."""
    from backend import main

    try:
        # Get or create session
        if request.session_id:
            session = main.session_service.get_session(request.session_id)
            if not session:
                raise SessionError(f"Session {request.session_id} not found")
            session_id = request.session_id
        else:
            session_id = main.session_service.create_session()

        # Detect emotion from text (no audio)
        import numpy as np

        empty_audio = np.array([])
        emotion = main.emotion_service.detect_emotion_blocking(
            empty_audio, request.text
        )

        # Generate response
        history = main.session_service.get_history(session_id)
        messages = []
        for item in history:
            if item["role"] in ["user", "assistant"]:
                messages.append({
                    "role": item["role"],
                    "content": item["content"],
                })

        messages.append({
            "role": "user",
            "content": request.text,
        })

        response_text = await main.llm_service.generate_response(messages, emotion)

        # Save turn
        main.session_service.add_turn(session_id, request.text, emotion, response_text)

        return {
            "session_id": session_id,
            "response": response_text,
            "emotion": emotion,
        }

    except SessionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    from backend import main

    deleted = main.session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {"message": f"Session {session_id} deleted"}
