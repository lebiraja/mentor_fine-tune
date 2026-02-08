"""Singleton service for managing all ML models."""

import sys
import torch
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from backend.config import voice_config, emotion_prompts
from backend.core.exceptions import ModelLoadError


class ModelService:
    """Singleton service that loads and manages all ML models once at startup."""

    _instance: Optional["ModelService"] = None
    _models: Dict[str, Any] = {}
    _loaded: bool = False

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service (called only once)."""
        pass

    async def initialize(self) -> None:
        """Load all models once at startup."""
        if self._loaded:
            return

        print("=" * 60)
        print("Loading all models (this may take a few minutes)...")
        print("=" * 60)

        try:
            # Load STT
            await self._load_stt()

            # Load TTS
            await self._load_tts()

            # Load emotion models
            await self._load_emotion_models()

            # Load LLM
            await self._load_llm()

            # Load VAD
            await self._load_vad()

            self._loaded = True
            print("=" * 60)
            print("✓ All models loaded successfully!")
            print("=" * 60)

        except Exception as e:
            print(f"Error loading models: {e}")
            raise ModelLoadError(f"Failed to initialize models: {e}")

    async def _load_stt(self) -> None:
        """Load Speech-to-Text model."""
        print("\n[1/5] Loading STT model (DistilWhisper)...")
        try:
            from scripts.voice.stt import SpeechToText

            stt_config = voice_config.get("models", {}).get("stt", {})
            self._models["stt"] = SpeechToText(stt_config)
            print("✓ STT model loaded")
        except Exception as e:
            raise ModelLoadError(f"Failed to load STT model: {e}")

    async def _load_tts(self) -> None:
        """Load Text-to-Speech model."""
        print("[2/5] Loading TTS model (CosyVoice)...")
        try:
            from scripts.voice.tts import EmotionalTTS

            tts_config = voice_config.get("models", {}).get("tts", {})
            tts = EmotionalTTS(tts_config)
            tts.load()
            self._models["tts"] = tts
            print("✓ TTS model loaded")
        except Exception as e:
            raise ModelLoadError(f"Failed to load TTS model: {e}")

    async def _load_emotion_models(self) -> None:
        """Load emotion detection models."""
        print("[3/5] Loading emotion models (Text + Speech)...")
        try:
            from scripts.emotion.text_emotion import TextEmotionDetector
            from scripts.emotion.speech_emotion import SpeechEmotionDetector
            from scripts.emotion.fusion import EmotionFusion

            text_emotion_config = voice_config.get("models", {}).get("text_emotion", {})
            self._models["text_emotion"] = TextEmotionDetector(text_emotion_config)
            self._models["text_emotion"].load()

            speech_emotion_config = voice_config.get("models", {}).get(
                "speech_emotion", {}
            )
            self._models["speech_emotion"] = SpeechEmotionDetector(
                speech_emotion_config
            )
            self._models["speech_emotion"].load()

            # Load fusion
            fusion_config = emotion_prompts.get("fusion", {})
            self._models["emotion_fusion"] = EmotionFusion(fusion_config)

            print("✓ Emotion models loaded")
        except Exception as e:
            raise ModelLoadError(f"Failed to load emotion models: {e}")

    async def _load_llm(self) -> None:
        """Load LLM (ClarityMentor)."""
        print("[4/5] Loading LLM (ClarityMentor)...")
        try:
            # Try to import from existing llm_core or inference
            try:
                from scripts.llm_core import (
                    load_claritymentor_model,
                    load_system_prompt,
                )
            except ImportError:
                # Fallback: Import from inference if llm_core doesn't exist
                from scripts.inference import load_model as load_claritymentor_model

                def load_system_prompt(model_dir=None):
                    """Load system prompt from config."""
                    prompt_path = (
                        Path(__file__).parent.parent.parent
                        / "config"
                        / "system_prompt.txt"
                    )
                    if prompt_path.exists():
                        return prompt_path.read_text()
                    return ""

            model_path = str(
                Path(__file__).parent.parent.parent / "models" / "claritymentor-lora" / "final"
            )
            config_path = Path(__file__).parent.parent.parent / "config"

            self._models["llm"], self._models["tokenizer"] = (
                load_claritymentor_model(model_path)
            )
            self._models["system_prompt"] = load_system_prompt(config_path)

            print("✓ LLM model loaded")
        except Exception as e:
            raise ModelLoadError(f"Failed to load LLM model: {e}")

    async def _load_vad(self) -> None:
        """Load Voice Activity Detection model."""
        print("[5/5] Loading VAD (Silero)...")
        try:
            from scripts.voice.vad import VoiceActivityDetector

            vad_config = voice_config.get("vad", {})
            self._models["vad"] = VoiceActivityDetector(vad_config)
            print("✓ VAD model loaded")
        except Exception as e:
            print(f"Warning: VAD model failed to load, will use energy-based detection: {e}")
            # Don't raise, VAD has fallback to energy-based detection

    def get_model(self, name: str) -> Any:
        """Get a loaded model by name.

        Args:
            name: Model name (e.g., 'stt', 'tts', 'text_emotion', etc.)

        Returns:
            The loaded model

        Raises:
            ModelLoadError: If model not found
        """
        if name not in self._models:
            raise ModelLoadError(
                f"Model '{name}' not loaded. Available: {list(self._models.keys())}"
            )
        return self._models[name]

    def is_loaded(self) -> bool:
        """Check if all models are loaded."""
        return self._loaded

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        print("\nShutting down...")

        for model_name, model in self._models.items():
            try:
                if hasattr(model, "unload"):
                    model.unload()
                print(f"✓ Unloaded {model_name}")
            except Exception as e:
                print(f"Warning: Failed to unload {model_name}: {e}")

        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        self._models.clear()
        self._loaded = False


# Global instance
model_service = ModelService()
