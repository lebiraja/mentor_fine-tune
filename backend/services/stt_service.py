"""Speech-to-Text service."""

import numpy as np
from typing import Optional
from backend.core.exceptions import TranscriptionError


class STTService:
    """Service for speech-to-text transcription."""

    def __init__(self, model_service):
        """Initialize STT service.

        Args:
            model_service: ModelService instance containing loaded STT model
        """
        self.model_service = model_service
        self._model = None

    @property
    def model(self):
        """Lazily get the STT model."""
        if self._model is None:
            self._model = self.model_service.get_model("stt")
        return self._model

    async def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio array (numpy)
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            if len(audio) == 0:
                return ""

            # Use the loaded model (no reload)
            text = self.model.transcribe(audio, sample_rate)
            return text

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
