# Tamil Support — Optimized Implementation Plan

## VRAM Budget (RTX 4050 — 6 GB)

| Component | Model | Runs On | VRAM | Latency |
|-----------|-------|---------|------|---------|
| LLM | Qwen3-4B Q4_K_M | GPU | ~3.5 GB | — |
| STT | faster-whisper `large-v3-turbo` int8 | **GPU** | ~1.3 GB | ~100-150ms |
| TTS (English) | Kokoro-82M ONNX | CPU | 0 | ~200ms |
| TTS (Tamil) | Piper Tamil ONNX | CPU | 0 | ~150ms |
| VAD | Silero | CPU | 0 | ~5ms |
| **Total** | | | **~4.8 GB ✅** | |

> [!TIP]
> Whisper `large-v3-turbo` has **built-in language detection** — it returns the detected language code (`en`, `ta`) alongside the transcription. No separate lang_detect module needed.

## Pipeline Flow

```
User speaks (any language)
    │
    ▼
Silero VAD (CPU) ──── detects speech boundaries
    │
    ▼
faster-whisper large-v3-turbo (GPU, int8)
    │── transcribes audio
    │── detects language (free, built-in)
    │── returns: { text: "...", lang: "ta" | "en" }
    │
    ▼
Qwen3-4B (GPU) ──── responds in detected language
    │
    ▼
TTS Router
    ├── lang == "en" → Kokoro-82M (CPU) → English audio
    └── lang == "ta" → Piper Tamil (CPU) → Tamil audio
    │
    ▼
WebSocket → Browser
```

## Files to Change

### 1. `backend/core/stt.py` — REWRITE
Replace Parakeet with faster-whisper on GPU.

```python
"""Speech-to-text: faster-whisper large-v3-turbo (GPU, int8)."""

from dataclasses import dataclass

import numpy as np


@dataclass
class STTResult:
    text: str
    language: str
    language_probability: float


class WhisperSTT:
    def __init__(self, model_size: str = "large-v3-turbo", device: str = "cuda", compute_type: str = "int8"):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> STTResult:
        """Blocking — call from a thread executor."""
        if audio.size == 0:
            return STTResult(text="", language="en", language_probability=0.0)

        segments, info = self.model.transcribe(
            audio.astype(np.float32),
            beam_size=1,
            language=None,  # auto-detect
            vad_filter=False,  # we handle VAD ourselves
        )
        text = " ".join(seg.text for seg in segments).strip()
        return STTResult(
            text=text,
            language=info.language,
            language_probability=info.language_probability,
        )
```

### 2. `backend/core/tts.py` — REWRITE
Route between Kokoro (English) and Piper (Tamil).

```python
"""TTS router: Kokoro for English, Piper for Tamil."""

from pathlib import Path

import numpy as np

OUTPUT_SAMPLE_RATE = 24000


class KokoroTTS:
    def __init__(self, model_path: Path, voices_path: Path, voice: str, speed: float):
        from kokoro_onnx import Kokoro

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice
        self.speed = speed

    def synthesize(self, text: str) -> tuple[bytes, int]:
        text = text.strip()
        if not text:
            return b"", OUTPUT_SAMPLE_RATE
        samples, sr = self.kokoro.create(text, voice=self.voice, speed=self.speed, lang="en-us")
        clipped = np.clip(samples, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes(), sr


class PiperTTS:
    def __init__(self, model_path: Path, config_path: Path):
        from piper import PiperVoice

        self.voice = PiperVoice.load(str(model_path), config_path=str(config_path))
        self.sample_rate = self.voice.config.sample_rate

    def synthesize(self, text: str) -> tuple[bytes, int]:
        text = text.strip()
        if not text:
            return b"", self.sample_rate
        audio_bytes = b""
        for chunk in self.voice.synthesize_stream_raw(text):
            audio_bytes += chunk
        return audio_bytes, self.sample_rate


class TTSRouter:
    def __init__(self, kokoro: KokoroTTS, piper_tamil: PiperTTS):
        self.kokoro = kokoro
        self.piper_tamil = piper_tamil

    def synthesize(self, text: str, language: str = "en") -> tuple[bytes, int]:
        if language == "ta":
            return self.piper_tamil.synthesize(text)
        return self.kokoro.synthesize(text)
```

### 3. `backend/config.py` — ADD fields

```python
# Add these to Settings class:
STT_MODEL: str = "large-v3-turbo"
STT_DEVICE: str = "cuda"
STT_COMPUTE_TYPE: str = "int8"

@property
def piper_tamil_model(self) -> Path:
    return self.MODELS_DIR / "piper-tamil" / "ta_IN-female-medium.onnx"

@property
def piper_tamil_config(self) -> Path:
    return self.MODELS_DIR / "piper-tamil" / "ta_IN-female-medium.onnx.json"
```

### 4. `backend/main.py` — UPDATE model loading

Update the lifespan to load WhisperSTT + TTSRouter instead of ParakeetSTT + KokoroTTS.

### 5. `backend/core/voice_session.py` (or wherever WebSocket handler is)

Use `stt_result.language` to pass to `tts.synthesize(text, language=...)`.

### 6. `config/system_prompt.txt` — UPDATE

Add instruction: "Respond in the same language the user speaks. If they speak Tamil, respond in Tamil. If English, respond in English."

### 7. `scripts/download_models.sh` — ADD

```bash
# Whisper large-v3-turbo downloads automatically on first run via faster-whisper
# (cached to ~/.cache/huggingface/hub)

# Piper Tamil voice (~60 MB)
echo "==> Piper Tamil TTS voice"
mkdir -p models/piper-tamil
PIPER_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/ta/ta_IN/female/medium"
[ -f models/piper-tamil/ta_IN-female-medium.onnx ] || \
    curl -L --fail -o models/piper-tamil/ta_IN-female-medium.onnx "$PIPER_BASE/ta_IN-female-medium.onnx"
[ -f models/piper-tamil/ta_IN-female-medium.onnx.json ] || \
    curl -L --fail -o models/piper-tamil/ta_IN-female-medium.onnx.json "$PIPER_BASE/ta_IN-female-medium.onnx.json"
```

### 8. `docker-compose.yml` — ADD volume

```yaml
volumes:
  - ./models/piper-tamil:/app/models/piper-tamil:ro
```

### 9. `requirements.txt` — ADD

```
faster-whisper>=1.1.0
piper-tts>=1.2.0
```

### 10. `Dockerfile.backend` — ADD CUDA support

The backend Dockerfile needs CUDA runtime for faster-whisper GPU inference. Switch base image:

```dockerfile
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
# Install Python 3.12, then pip install requirements
```

## Model Downloads Summary

| Model | Size | Source | Auto-download? |
|-------|------|--------|---------------|
| faster-whisper large-v3-turbo | ~1.5 GB | HuggingFace (cached) | ✅ Yes, on first run |
| Piper Tamil female-medium | ~60 MB | rhasspy/piper-voices | Manual (script) |

## What Gets Removed

- `onnx-asr` from requirements.txt (no longer needed)
- Parakeet model download from script (replaced by Whisper)
- Parakeet volume mount from docker-compose

## Latency Comparison

| Stage | Current (English only) | Optimized (EN + TA) |
|-------|----------------------|---------------------|
| VAD | ~5ms | ~5ms (same) |
| STT | ~200ms (Parakeet, CPU) | **~100-150ms** (Whisper turbo, GPU) |
| LLM | ~800-1500ms | ~800-1500ms (same) |
| TTS | ~200ms (Kokoro, CPU) | ~200ms EN / ~150ms TA |
| **Total** | ~1.3-2.5s | **~1.1-1.8s** |

> [!IMPORTANT]
> Net result: Tamil support **AND** faster overall latency. GPU STT more than compensates for the model switch.
