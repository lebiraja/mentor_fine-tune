"""Text-to-speech: Kokoro-82M ONNX (CPU), female voice by default."""

from pathlib import Path

import numpy as np

OUTPUT_SAMPLE_RATE = 24000  # Kokoro native


class KokoroTTS:
    def __init__(self, model_path: Path, voices_path: Path, voice: str, speed: float):
        from kokoro_onnx import Kokoro

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice
        self.speed = speed

    def synthesize(self, text: str) -> bytes:
        """Blocking — call from a thread executor. Returns 24 kHz mono int16 PCM."""
        text = text.strip()
        if not text:
            return b""
        samples, sample_rate = self.kokoro.create(
            text, voice=self.voice, speed=self.speed, lang="en-us"
        )
        if sample_rate != OUTPUT_SAMPLE_RATE:
            raise RuntimeError(f"Unexpected Kokoro sample rate {sample_rate}")
        clipped = np.clip(samples, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes()
