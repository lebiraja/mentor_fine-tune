"""Smoke tests against the real models. Run: pytest -m smoke (needs `make models`)."""

import numpy as np
import pytest

from backend.config import settings

pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module")
def tts_kokoro():
    from backend.core.tts import KokoroTTS

    if not settings.kokoro_model.exists():
        pytest.skip("Kokoro model not downloaded")
    return KokoroTTS(settings.kokoro_model, settings.kokoro_voices, settings.TTS_VOICE, 1.0)


@pytest.fixture(scope="module")
def tts_router():
    from backend.core.tts import KokoroTTS, PiperTTS, TTSRouter

    if not settings.kokoro_model.exists():
        pytest.skip("Kokoro model not downloaded")
    kokoro = KokoroTTS(settings.kokoro_model, settings.kokoro_voices, settings.TTS_VOICE, 1.0)

    piper = None
    if settings.piper_tamil_model.exists():
        piper = PiperTTS(settings.piper_tamil_model, settings.piper_tamil_config)
    return TTSRouter(kokoro=kokoro, piper_tamil=piper)


@pytest.fixture(scope="module")
def stt():
    from backend.core.stt import WhisperSTT

    return WhisperSTT(
        model_size=settings.STT_MODEL,
        device="cpu",
        compute_type="int8",
    )


def test_tts_english_produces_audio(tts_kokoro):
    pcm, sr = tts_kokoro.synthesize("Hello, this is a quick test of the voice.")
    assert len(pcm) > 24000  # > 0.5s of 24kHz int16 audio
    samples = np.frombuffer(pcm, dtype=np.int16)
    assert np.abs(samples).max() > 500


def test_tts_router_english(tts_router):
    pcm = tts_router.synthesize("This is an English test.", language="en")
    assert len(pcm) > 24000
    samples = np.frombuffer(pcm, dtype=np.int16)
    assert np.abs(samples).max() > 500


def test_tts_router_tamil(tts_router):
    if tts_router.piper_tamil is None:
        pytest.skip("Piper Tamil model not downloaded")
    pcm = tts_router.synthesize("வணக்கம், இது ஒரு சோதனை.", language="ta")
    assert len(pcm) > 1000
    samples = np.frombuffer(pcm, dtype=np.int16)
    assert np.abs(samples).max() > 100


def test_stt_english_roundtrip(tts_kokoro, stt):
    """Synthesize English speech, transcribe it back."""
    pcm, _ = tts_kokoro.synthesize("The quick brown fox jumps over the lazy dog.")
    audio_24k = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    idx = (np.arange(int(len(audio_24k) * 2 / 3)) * 1.5).astype(int)
    audio_16k = audio_24k[idx[idx < len(audio_24k)]]

    result = stt.transcribe(audio_16k)
    assert "quick brown fox" in result.text.lower()
    assert result.language == "en"


def test_stt_empty_audio(stt):
    result = stt.transcribe(np.array([], dtype=np.float32))
    assert result.text == ""
    assert result.language == "en"


def test_vad_distinguishes_speech_from_silence(tts_kokoro):
    from backend.core.vad import FRAME_SAMPLES, SileroVAD

    if not settings.silero_model.exists():
        pytest.skip("Silero model not downloaded")
    vad = SileroVAD(settings.silero_model)

    silence = np.zeros(FRAME_SAMPLES, dtype=np.float32)
    assert vad.prob(silence) < 0.3

    pcm, _ = tts_kokoro.synthesize("Testing voice activity detection.")
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
