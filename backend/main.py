"""FastAPI backend for ClarityMentor voice system."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.config import settings, voice_config, emotion_prompts
from backend.services import (
    ModelService,
    model_service,
    STTService,
    TTSService,
    EmotionService,
    LLMService,
    SessionService,
)


# Initialize services (will be populated on startup)
stt_service: STTService
tts_service: TTSService
emotion_service: EmotionService
llm_service: LLMService
session_service: SessionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    # Startup
    try:
        print("\n" + "=" * 70)
        print("CLARITYMENTOR FASTAPI BACKEND - STARTUP")
        print("=" * 70)

        # Load all models once
        await model_service.initialize()

        # Initialize services with loaded models
        global stt_service, tts_service, emotion_service, llm_service, session_service

        stt_service = STTService(model_service)
        tts_service = TTSService(model_service)
        emotion_service = EmotionService(model_service)
        llm_service = LLMService(model_service, emotion_prompts)
        session_service = SessionService()

        print("\n✓ All services initialized and ready!")
        print("=" * 70)
        print("\nWebSocket endpoint: ws://localhost:2323/ws/voice")
        print("Health check: http://localhost:2323/api/health")
        print("=" * 70 + "\n")

        yield

    except Exception as e:
        print(f"\n✗ Failed to initialize services: {e}")
        raise

    # Shutdown
    finally:
        print("\n" + "=" * 70)
        print("SHUTTING DOWN")
        print("=" * 70)
        await model_service.shutdown()
        print("=" * 70 + "\n")


# Create FastAPI app with lifespan
app = FastAPI(
    title="ClarityMentor Voice API",
    description="Voice-to-voice chat with emotion detection",
    version="1.0.0",
    lifespan=lifespan,
)


# Import and include routers
from backend.api import websocket, rest

app.include_router(websocket.router)
app.include_router(rest.router, prefix="/api")


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
