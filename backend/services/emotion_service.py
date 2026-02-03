"""Emotion detection service."""

import numpy as np
import asyncio
from typing import Dict, Any, Optional
from backend.core.exceptions import EmotionDetectionError


class EmotionService:
    """Service for emotion detection and fusion."""

    def __init__(self, model_service):
        """Initialize emotion service.

        Args:
            model_service: ModelService instance containing emotion models
        """
        self.model_service = model_service
        self._text_emotion = None
        self._speech_emotion = None
        self._fusion = None

    @property
    def text_emotion(self):
        """Lazily get text emotion model."""
        if self._text_emotion is None:
            self._text_emotion = self.model_service.get_model("text_emotion")
        return self._text_emotion

    @property
    def speech_emotion(self):
        """Lazily get speech emotion model."""
        if self._speech_emotion is None:
            self._speech_emotion = self.model_service.get_model("speech_emotion")
        return self._speech_emotion

    @property
    def fusion(self):
        """Lazily get emotion fusion model."""
        if self._fusion is None:
            self._fusion = self.model_service.get_model("emotion_fusion")
        return self._fusion

    async def detect_emotion(
        self, audio: np.ndarray, text: str, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """Detect emotion from both audio and text, then fuse.

        Args:
            audio: Audio array (numpy)
            text: Transcribed text
            sample_rate: Sample rate in Hz

        Returns:
            Dict with detected emotion and confidence
        """
        try:
            # Run detections in parallel
            speech_emo_task = asyncio.create_task(
                self._detect_speech_emotion_async(audio, sample_rate)
            )
            text_emo_task = asyncio.create_task(
                self._detect_text_emotion_async(text)
            )

            speech_emo = await speech_emo_task
            text_emo = await text_emo_task

            # Fuse emotions
            fused_emotion = self.fusion.fuse(speech_emo, text_emo)

            return fused_emotion

        except Exception as e:
            raise EmotionDetectionError(f"Emotion detection failed: {e}")

    async def _detect_speech_emotion_async(
        self, audio: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """Detect emotion from speech (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.speech_emotion.detect_emotion, audio, sample_rate
        )

    async def _detect_text_emotion_async(self, text: str) -> Dict[str, Any]:
        """Detect emotion from text (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.text_emotion.detect_emotion, text)

    def detect_emotion_blocking(
        self, audio: np.ndarray, text: str, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """Blocking version of emotion detection (for sync contexts).

        Args:
            audio: Audio array (numpy)
            text: Transcribed text
            sample_rate: Sample rate in Hz

        Returns:
            Dict with detected emotion and confidence
        """
        try:
            # Detect from both sources
            speech_emo = self.speech_emotion.detect_emotion(audio, sample_rate)
            text_emo = self.text_emotion.detect_emotion(text)

            # Fuse emotions
            fused_emotion = self.fusion.fuse(speech_emo, text_emo)

            return fused_emotion

        except Exception as e:
            raise EmotionDetectionError(f"Emotion detection failed: {e}")
