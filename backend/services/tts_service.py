"""Text-to-Speech service."""

import numpy as np
import asyncio
from typing import Optional, Dict, Any
from backend.core.exceptions import TTSError


class TTSService:
    """Service for text-to-speech synthesis."""

    def __init__(self, model_service):
        """Initialize TTS service.

        Args:
            model_service: ModelService instance containing loaded TTS model
        """
        self.model_service = model_service
        self._model = None

    @property
    def model(self):
        """Lazily get the TTS model."""
        if self._model is None:
            self._model = self.model_service.get_model("tts")
        return self._model

    async def synthesize(
        self, text: str, emotion: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            emotion: Emotion context (dict with emotion, confidence, etc.)

        Returns:
            Audio bytes (PCM 16-bit mono)

        Raises:
            TTSError: If synthesis fails
        """
        try:
            if not text or len(text.strip()) == 0:
                return b""

            # Run synthesis in thread pool to avoid blocking
            # (pyttsx3 may have I/O operations)
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None, self._synthesize_blocking, text, emotion
            )
            return audio_bytes

        except Exception as e:
            raise TTSError(f"TTS synthesis failed: {e}")

    def _synthesize_blocking(
        self, text: str, emotion: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Blocking TTS synthesis (runs in thread pool).

        Args:
            text: Text to synthesize
            emotion: Emotion context

        Returns:
            Audio bytes
        """
        try:
            import numpy as np
            from backend.core.audio_utils import array_to_bytes

            # Call the underlying model's synthesize method (returns numpy array)
            audio_array = self.model.synthesize(text, emotion)

            # Convert numpy array to bytes
            if isinstance(audio_array, np.ndarray) and len(audio_array) > 0:
                return array_to_bytes(audio_array)
            else:
                return b""
        except Exception as e:
            raise TTSError(f"TTS synthesis failed: {e}")
