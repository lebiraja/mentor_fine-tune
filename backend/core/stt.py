"""Speech-to-text: faster-whisper large-v3-turbo (GPU int8, multilingual)."""

from dataclasses import dataclass

import numpy as np


@dataclass
class STTResult:
    text: str
    language: str
    language_probability: float


class WhisperSTT:
    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "int8",
    ):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> STTResult:
        """Blocking — call from a thread executor. `audio` is float32 mono."""
        if audio.size == 0:
            return STTResult(text="", language="en", language_probability=0.0)

        segments, info = self.model.transcribe(
            audio.astype(np.float32),
            beam_size=1,
            language=None,
            vad_filter=False,
        )
        text = " ".join(seg.text for seg in segments).strip()

        lang = info.language or "en"
        prob = info.language_probability or 0.0
        if prob < 0.7:
            lang = "en"

        return STTResult(text=text, language=lang, language_probability=prob)
