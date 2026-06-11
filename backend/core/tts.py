"""TTS: Kokoro for English, Piper for Tamil, routed by detected language."""

from pathlib import Path

import numpy as np

OUTPUT_SAMPLE_RATE = 24000  # WebSocket protocol expects 24 kHz int16 mono


class KokoroTTS:
    """English TTS — Kokoro-82M ONNX, female voice by default."""

    def __init__(self, model_path: Path, voices_path: Path, voice: str, speed: float):
        from kokoro_onnx import Kokoro

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice
        self.speed = speed

    def synthesize(self, text: str) -> tuple[bytes, int]:
        text = text.strip()
        if not text:
            return b"", OUTPUT_SAMPLE_RATE
        samples, sr = self.kokoro.create(
            text, voice=self.voice, speed=self.speed, lang="en-us"
        )
        if sr != OUTPUT_SAMPLE_RATE:
            raise RuntimeError(f"Unexpected Kokoro sample rate {sr}")
        clipped = np.clip(samples, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes(), sr


class PiperTTS:
    """Tamil TTS — Piper ONNX voice, CPU."""

    def __init__(self, model_path: Path, config_path: Path):
        from piper import PiperVoice

        self.voice = PiperVoice.load(str(model_path), config_path=str(config_path))
        self.sample_rate: int = self.voice.config.sample_rate

    def synthesize(self, text: str) -> tuple[bytes, int]:
        text = text.strip()
        if not text:
            return b"", self.sample_rate
        chunks: list[np.ndarray] = []
        for chunk in self.voice.synthesize(text):
            chunks.append(chunk.audio_float_array)
        if not chunks:
            return b"", self.sample_rate
        audio = np.concatenate(chunks)
        clipped = np.clip(audio, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes(), self.sample_rate


class TTSRouter:
    """Routes to Kokoro (EN) or Piper (TA) based on detected language."""

    def __init__(self, kokoro: KokoroTTS, piper_tamil: PiperTTS | None = None):
        self.kokoro = kokoro
        self.piper_tamil = piper_tamil

    def synthesize(self, text: str, language: str = "en") -> bytes:
        """Returns 24 kHz mono int16 PCM regardless of which engine ran."""
        if language == "ta" and self.piper_tamil is not None:
            pcm, sr = self.piper_tamil.synthesize(text)
            if pcm and sr != OUTPUT_SAMPLE_RATE:
                pcm = _resample(pcm, sr, OUTPUT_SAMPLE_RATE)
            return pcm

        pcm, _ = self.kokoro.synthesize(text)
        return pcm


def _resample(pcm: bytes, from_rate: int, to_rate: int) -> bytes:
    """Linear interpolation resample — good enough for speech, no heavy deps."""
    samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    ratio = to_rate / from_rate
    new_len = int(len(samples) * ratio)
    indices = np.linspace(0, len(samples) - 1, new_len)
    resampled = np.interp(indices, np.arange(len(samples)), samples)
    return resampled.astype(np.int16).tobytes()
