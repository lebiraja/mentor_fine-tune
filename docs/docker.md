# Docker

## Prerequisites
- Docker + Compose v2
- NVIDIA driver + `nvidia-container-toolkit` (the `llm` service reserves the GPU)
- ~5 GB disk for model weights

## First run
```bash
cp .env.example .env          # set HF_TOKEN (only used for downloads)
make models                   # one-time, ~4 GB into ./models/
make up                       # build + start all three services
```
Open http://localhost:2000. After `make models`, no network is needed at runtime.

## Services & ports
| Service | Container | Host port | Notes |
|---|---|---|---|
| llm | clarity-llm | 127.0.0.1:2380 | llama.cpp server, GPU, loads the GGUF in ~30–60 s |
| backend | clarity-backend |  127.0.0.1:2324 | waits for llm healthcheck; ONNX engines load in ~30 s |
| frontend | clarity-frontend | 2000 | nginx; the only port meant for the browser |

Volumes: `./models/*` mounted read-only; `clarity-data` holds the SQLite db.

## Commands
```bash
make up / make down / make logs
make test          # unit + protocol tests (no models needed)
make test-smoke    # real-model smoke tests (after make models)
make dev           # vite dev server on :5173, proxies to a running backend
make clean         # down + remove volumes
```

## End-to-end voice check (no microphone needed)
Speaks a synthesized question at the live stack and asserts on transcript, reply, and audio:
```bash
docker compose exec -e PYTHONPATH=/app backend python tests/e2e_voice_client.py   # English
docker compose exec -e PYTHONPATH=/app backend python tests/e2e_tamil_client.py   # Tamil
```

## Troubleshooting
- **llm unhealthy** — check `docker compose logs llm`; usually a missing/incomplete GGUF (`make models` resumes).
- **GPU not found** — `nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`.
- **VRAM pressure** (other apps using the GPU): lower `--ctx-size` in `docker-compose.yml`.
- **Backend can't load ONNX models** — paths under `./models/` must match `scripts/download_models.sh` layout.
