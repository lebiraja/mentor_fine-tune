"""Configuration — all knobs env-driven via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    HOST: str = "0.0.0.0"
    PORT: int = 2323
    DEBUG: bool = False

    # llama.cpp server (OpenAI-compatible)
    LLM_BASE_URL: str = "http://localhost:2380/v1"
    LLM_MODEL: str = "qwen3-4b-instruct-2507"
    LLM_MAX_TOKENS: int = 400
    LLM_TEMPERATURE: float = 0.7
    LLM_CONTEXT_TOKENS: int = 8192

    # Model file locations (mounted ro in docker)
    MODELS_DIR: Path = BASE_DIR / "models"

    # Voice
    TTS_VOICE: str = "af_heart"
    TTS_SPEED: float = 1.0

    # VAD turn-taking
    VAD_THRESHOLD: float = 0.5
    VAD_MIN_SPEECH_S: float = 0.25
    VAD_END_SILENCE_S: float = 0.6

    DB_PATH: Path = BASE_DIR / "data" / "clarity.db"

    @property
    def parakeet_dir(self) -> Path:
        return self.MODELS_DIR / "parakeet-v3"

    @property
    def kokoro_model(self) -> Path:
        return self.MODELS_DIR / "kokoro" / "kokoro-v1.0.onnx"

    @property
    def kokoro_voices(self) -> Path:
        return self.MODELS_DIR / "kokoro" / "voices-v1.0.bin"

    @property
    def silero_model(self) -> Path:
        return self.MODELS_DIR / "silero" / "silero_vad.onnx"

    @property
    def system_prompt(self) -> str:
        return (BASE_DIR / "config" / "system_prompt.txt").read_text().strip()


settings = Settings()
