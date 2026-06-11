# Clarity

A fully local voice companion — talk out loud, get a thoughtful voice back. Nothing leaves your machine.

- **Brain:** Qwen3-4B-Instruct-2507 (Q4 GGUF, llama.cpp, GPU)
- **Ears:** Parakeet TDT 0.6B v3 (ONNX, CPU)
- **Voice:** Kokoro-82M, `af_heart` (ONNX, CPU)
- **Turn-taking:** Silero VAD with barge-in — interrupt it mid-sentence by speaking

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
make models   # one-time ~4 GB download
docker compose up -d
# open http://localhost:2000 and press Begin
```

| Image | Size | Description |
|-------|------|-------------|
| `lebiraja/clarity-backend` | ~544 MB | FastAPI + STT/TTS/VAD models |
| `lebiraja/clarity-frontend` | ~94 MB | Nginx + Vite SPA |

## Quick Start (from source)

```bash
cp .env.example .env
make models   # one-time ~4 GB download
make up
# open http://localhost:2000 and press Begin
```

Docs: [architecture](docs/architecture.md) · [API](docs/API.md) · [docker](docs/docker.md) · [fixes](docs/FIXES.md)

Sized for a 6 GB-VRAM laptop GPU (RTX 4050): ~3.5 GB VRAM for the LLM, audio models on CPU, ~1.3–2.5 s to first reply audio.

The v1 fine-tuning pipeline (datasets, QLoRA training) was removed from the working tree — recover it from git history (`git log --follow -- scripts/training`) if ever needed.
