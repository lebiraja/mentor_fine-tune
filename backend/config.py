"""Configuration management for FastAPI backend."""

import os
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 2323
    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

    @property
    def base_dir(self) -> Path:
        """Get base directory."""
        return Path(__file__).parent.parent

    @property
    def config_dir(self) -> Path:
        """Get config directory."""
        return self.base_dir / "config"

    @property
    def models_dir(self) -> Path:
        """Get models directory."""
        return self.base_dir / "models"


def load_voice_config() -> dict:
    """Load voice_config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_emotion_prompts() -> dict:
    """Load emotion_prompts.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "emotion_prompts.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


# Global config instances
settings = Settings()
voice_config = load_voice_config()
emotion_prompts = load_emotion_prompts()
