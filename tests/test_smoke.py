"""Smoke tests against the real ONNX models. Run: pytest -m smoke (needs `make models`)."""

import numpy as np
import pytest

from backend.config import settings

pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module")
def tts():
    from backend.core.tts import KokoroTTS

    if not settings.kokoro_model.exists():
        pytest.skip("Kokoro model not downloaded")
    return KokoroTTS(settings.kokoro_model, settings.kokoro_voices, settings.TTS_VOICE, 1.0)


@pytest.fixture(scope="module")
def stt():
    from backend.core.stt import ParakeetSTT

    if not settings.parakeet_dir.exists():
        pytest.skip("Parakeet model not downloaded")
    return ParakeetSTT(settings.parakeet_dir)


def test_tts_produces_audio(tts):
    pcm = tts.synthesize("Hello, this is a quick test of the voice.")
    assert len(pcm) > 24000  # > 0.5s of 24kHz int16 audio
    samples = np.frombuffer(pcm, dtype=np.int16)
    assert np.abs(samples).max() > 500  # not silence


def test_tts_then_stt_roundtrip(tts, stt):
    """The strongest local check: synthesize speech, transcribe it back."""
    import math

    pcm = tts.synthesize("The quick brown fox jumps over the lazy dog.")
    audio_24k = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    # naive 24k -> 16k resample (ratio 3:2) is fine for a smoke test
    idx = (np.arange(int(len(audio_24k) * 2 / 3)) * 1.5).astype(int)
    audio_16k = audio_24k[idx[idx < len(audio_24k)]]

    text = stt.transcribe(audio_16k).lower()
    assert "quick brown fox" in text


def test_vad_distinguishes_speech_from_silence(tts):
    from backend.core.vad import FRAME_SAMPLES, SileroVAD

    if not settings.silero_model.exists():
        pytest.skip("Silero model not downloaded")
    vad = SileroVAD(settings.silero_model)

    silence = np.zeros(FRAME_SAMPLES, dtype=np.float32)
    assert vad.prob(silence) < 0.3

    pcm = tts.synthesize("Testing voice activity detection.")
    audio_24k = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    idx = (np.arange(int(len(audio_24k) * 2 / 3)) * 1.5).astype(int)
    audio_16k = audio_24k[idx[idx < len(audio_24k)]]

    vad.reset()
    mid = len(audio_16k) // 2
    probs = [
        vad.prob(audio_16k[i : i + FRAME_SAMPLES])
        for i in range(0, mid, FRAME_SAMPLES)
        if i + FRAME_SAMPLES <= len(audio_16k)
    ]
    assert max(probs) > 0.5
