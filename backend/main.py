"""ClarityMentor v2 backend — FastAPI app factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import rest, ws
from backend.config import settings
from backend.core.llm import LLMClient
from backend.core.pipeline import LatencyStats
from backend.db import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.stats = LatencyStats()
    app.state.system_prompt = settings.system_prompt

    app.state.db = Database(settings.DB_PATH)
    await app.state.db.connect()

    app.state.llm = LLMClient(
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    # ONNX engines: a few hundred MB of RAM, ~20s load, CPU-only
    print("Loading STT (Parakeet TDT 0.6B v3 int8)...")
    from backend.core.stt import ParakeetSTT

    app.state.stt = ParakeetSTT(settings.parakeet_dir)

    print("Loading TTS (Kokoro-82M, voice=%s)..." % settings.TTS_VOICE)
    from backend.core.tts import KokoroTTS

    app.state.tts = KokoroTTS(
        settings.kokoro_model, settings.kokoro_voices, settings.TTS_VOICE, settings.TTS_SPEED
    )

    from backend.core.vad import SileroVAD

    # Each WS connection gets its own VAD (stateful), sharing nothing
    app.state.make_vad = lambda: SileroVAD(settings.silero_model)

    app.state.ready = True
    print("Backend ready.")

    yield

    await app.state.llm.close()
    await app.state.db.close()


app = FastAPI(title="ClarityMentor v2", version="2.0.0", lifespan=lifespan)
app.include_router(rest.router, prefix="/api")
app.include_router(ws.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
