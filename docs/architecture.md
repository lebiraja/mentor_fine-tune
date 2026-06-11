# Architecture

ClarityMentor v2 is a fully local voice companion: you talk, it talks back. No data leaves the machine after the one-time model download.

## Services (docker compose)

| Service | Image | Hardware | Role |
|---|---|---|---|
| `llm` | `ghcr.io/ggml-org/llama.cpp:server-cuda` | **GPU** (~3.5 GB VRAM) | Qwen3-4B-Instruct-2507 Q4_K_M, OpenAI-compatible streaming API on `:8080` (host: `127.0.0.1:2380`) |
| `backend` | `python:3.12-slim` build | CPU | FastAPI; VAD + STT + TTS + pipeline + SQLite. `:2323` (host: `127.0.0.1:2324`) |
| `frontend` | nginx | — | Built React app; proxies `/api` and `/ws` to backend. `:2000` |

Only the `llm` container touches the GPU. The backend runs all audio models on CPU via ONNX:

- **STT** — NVIDIA Parakeet TDT 0.6B v3 (int8 ONNX, via `onnx-asr`)
- **TTS** — Kokoro-82M (`kokoro-onnx`), voice `af_heart` (female), 24 kHz output
- **VAD** — Silero v5, raw onnxruntime wrapper (no torch)

## Conversation pipeline

Per WebSocket connection (`backend/core/pipeline.py`):

```
client mic ──16kHz PCM frames──▶ TurnDetector (Silero VAD)
                                   │ end-of-speech (0.6s silence)
                                   ▼
                              Parakeet STT
                                   │ transcript
                                   ▼
                    llama.cpp /v1/chat/completions (stream)
                       │ token deltas            │
                       ▼                         ▼
              assistant_delta events      SentenceSegmenter
              (live text in UI)                  │ complete sentences
                                                 ▼
                                            Kokoro TTS
                                                 │ 24kHz PCM chunks
                                                 ▼
                                       binary WS frames ──▶ client playback queue
```

States: `listening → transcribing → generating → speaking → listening`.

**Barge-in:** VAD keeps running while the assistant speaks. New user speech cancels the in-flight LLM stream and TTS tasks, sends `interrupted`, and the client flushes its audio queue. Partial assistant text is persisted.

**Blocking inference** (STT/TTS) runs in thread executors; the event loop never blocks.

**History windowing:** system prompt + most recent turns fitted to the 8k context with a ~4 chars/token heuristic (`pipeline._windowed_messages`).

## Persistence

SQLite (`backend/db.py`) in the `clarity-data` volume: `sessions` and `messages` tables. The first user message becomes the session title. The frontend stores the active session id in `localStorage` and resumes it over the WS.

## Frontend (Quiet Room)

Single screen (`frontend/src/App.tsx`). Three hooks own all the machinery:

- `useMicStream` — AudioWorklet capturing 16 kHz int16 PCM (~64 ms chunks), `echoCancellation: true`
- `usePlayback` — Web Audio queue for gapless 24 kHz playback, instant flush on interrupt
- `useConversation` — WS protocol client (Zod-validated), reconnect, session switching

Latency targets: ~2–2.5 s from end of speech to first audio; per-stage timings exposed at `/api/health`.
