"""ClarityMentor v3 backend — FastAPI app factory (bilingual EN/TA)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import rest, ws
from backend.config import settings
from backend.core.llm import LLMClient
from backend.core.personas import PersonaRegistry
from backend.core.pipeline import LatencyStats
from backend.db import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.stats = LatencyStats()
    app.state.personas = PersonaRegistry()

    app.state.db = Database(settings.DB_PATH)
    await app.state.db.connect()

    app.state.llm = LLMClient(
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    print("Loading STT (Whisper %s, %s, %s)..." % (settings.STT_MODEL, settings.STT_DEVICE, settings.STT_COMPUTE_TYPE))
    from backend.core.stt import WhisperSTT

    app.state.stt = WhisperSTT(
        model_size=settings.STT_MODEL,
        device=settings.STT_DEVICE,
        compute_type=settings.STT_COMPUTE_TYPE,
    )

    print("Loading TTS — English (Kokoro-82M, voice=%s)..." % settings.TTS_VOICE)
    from backend.core.tts import KokoroTTS, PiperTTS, TTSRouter

    kokoro = KokoroTTS(
        settings.kokoro_model, settings.kokoro_voices, settings.TTS_VOICE, settings.TTS_SPEED
    )

    piper_tamil = None
    if settings.PIPER_TAMIL_ENABLED and settings.piper_tamil_model.exists():
        print("Loading TTS — Tamil (Piper)...")
        piper_tamil = PiperTTS(settings.piper_tamil_model, settings.piper_tamil_config)
    elif settings.PIPER_TAMIL_ENABLED:
        print("WARNING: Piper Tamil model not found at %s — Tamil TTS disabled" % settings.piper_tamil_model)

    app.state.tts = TTSRouter(kokoro=kokoro, piper_tamil=piper_tamil)

    from backend.core.vad import SileroVAD

    # Each WS connection gets its own VAD (stateful), sharing nothing
    app.state.make_vad = lambda: SileroVAD(settings.silero_model)

    app.state.ready = True
    print("Backend ready.")

    yield

    await app.state.llm.close()
    await app.state.db.close()


app = FastAPI(title="ClarityMentor v3", version="3.0.0", lifespan=lifespan)
app.include_router(rest.router, prefix="/api")
app.include_router(ws.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
