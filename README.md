# Clarity

A fully local voice companion — talk out loud in **English or Tamil**, get a thoughtful voice back. Nothing leaves your machine.

- **Brain:** Qwen3-4B-Instruct-2507 (Q4 GGUF, llama.cpp, GPU)
- **Ears:** faster-whisper large-v3-turbo (CTranslate2, GPU int8) — automatic language detection
- **Voice (EN):** Kokoro-82M, `af_heart` (ONNX, CPU)
- **Voice (TA):** Piper `ta_IN-female-medium` (ONNX, CPU)
- **Turn-taking:** Silero VAD with barge-in — interrupt it mid-sentence by speaking
- **Personas:** pick who you talk to before you begin — **Clarity** (philosophical mentor), **Engineer** (technical sounding board), **General** (just talk), **Coach** (accountability), or **Friend** (remembers you across sessions and greets you first)

## Docker Hub

[![Backend](https://img.shields.io/docker/v/lebiraja/clarity-backend?label=backend&sort=semver)](https://hub.docker.com/r/lebiraja/clarity-backend)
[![Frontend](https://img.shields.io/docker/v/lebiraja/clarity-frontend?label=frontend&sort=semver)](https://hub.docker.com/r/lebiraja/clarity-frontend)

Pre-built images are available on Docker Hub:

```bash
docker pull lebiraja/clarity-backend:latest
docker pull lebiraja/clarity-frontend:latest
```

Or use the full stack with `docker compose`:

```bash
cp .env.example .env
make models   # one-time ~4.5 GB download
docker compose up -d
# open http://localhost:2000 and press Begin
```

| Image | Size | Description |
|-------|------|-------------|
| `lebiraja/clarity-backend` | ~1.8 GB | CUDA runtime + FastAPI + STT/TTS/VAD |
| `lebiraja/clarity-frontend` | ~94 MB | Nginx + Vite SPA |

## VRAM Budget (RTX 4050 6 GB)

| Component | VRAM |
|-----------|------|
| Qwen3-4B Q4_K_M (llama.cpp) | ~3.5 GB |
| Whisper large-v3-turbo int8 | ~1.3 GB |
| Kokoro + Piper + Silero (CPU) | 0 |
| **Total** | **~4.8 GB** |

## Quick Start (from source)

```bash
cp .env.example .env
make models   # one-time ~4.5 GB download
make up
# open http://localhost:2000 and press Begin
```

## Language Support

Speak in English, Tamil, or Tanglish (mixed) — Clarity detects the language automatically and responds in the same language.

| Setting | Default | Description |
|---------|---------|-------------|
| `STT_MODEL` | `large-v3-turbo` | Whisper model for transcription |
| `STT_DEVICE` | `cuda` | `cuda` or `cpu` |
| `PIPER_TAMIL_ENABLED` | `true` | Set `false` to disable Tamil TTS |

Docs: [architecture](docs/architecture.md) · [API](docs/API.md) · [docker](docs/docker.md) · [fixes](docs/FIXES.md) · [tamil support plan](docs/tamil_support_plan.md)

Sized for a 6 GB-VRAM laptop GPU (RTX 4050): ~4.8 GB VRAM total, ~1.1–1.8 s to first reply audio.

The v1 fine-tuning pipeline (datasets, QLoRA training) was removed from the working tree — recover it from git history (`git log --follow -- scripts/training`) if ever needed.
