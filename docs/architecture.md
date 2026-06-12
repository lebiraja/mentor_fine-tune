# Architecture

Clarity v3 is a fully local **bilingual** (English + Tamil) voice companion: you talk in either language, it detects which and talks back in the same one. No data leaves the machine after the one-time model download.

## Services (docker compose)

| Service | Image | Hardware | Role |
|---|---|---|---|
| `llm` | `ghcr.io/ggml-org/llama.cpp:server-cuda` | **GPU** (~3.5 GB VRAM) | Qwen3-4B-Instruct-2507 Q4_K_M, OpenAI-compatible streaming API on `:8080` (host: `127.0.0.1:2380`) |
| `backend` | `nvidia/cuda:12.4.1-runtime` + Python 3.12 | **GPU** (STT) + CPU | FastAPI; VAD + STT + TTS + pipeline + SQLite. `:2323` (host: `127.0.0.1:2324`) |
| `frontend` | nginx | — | Built React app; proxies `/api` and `/ws` to backend. `:2000` |

Engines:

- **STT** — faster-whisper `large-v3-turbo`, **GPU** int8 (CTranslate2). Multilingual with built-in language detection (`info.language` → `en`/`ta`/…). Whisper weights auto-download to the `whisper-cache` volume on first run (~1.5 GB).
- **TTS (English)** — Kokoro-82M (`kokoro-onnx`), voice `af_heart` (female), 24 kHz, CPU.
- **TTS (Tamil)** — Piper `ta_IN-Valluvar-medium` (ONNX), 22.05 kHz, CPU. Resampled to 24 kHz in the router.
- **VAD** — Silero v5, raw onnxruntime wrapper (no torch), CPU.

Both `llm` and `backend` reserve the GPU. They share the RTX 4050's 6 GB: ~3.5 GB (LLM, resident) + ~1.3 GB (Whisper, resident) ≈ 4.8 GB peak. STT and LLM run sequentially within a turn, so they don't spike simultaneously.

## Conversation pipeline

Per WebSocket connection (`backend/core/pipeline.py`):

```
client mic ──16kHz PCM frames──▶ TurnDetector (Silero VAD)
                                   │ end-of-speech (0.6s silence)
                                   ▼
                       faster-whisper STT (GPU)
                                   │ STTResult{text, language, probability}
                                   ▼
                    llama.cpp /v1/chat/completions (stream)
                       │ token deltas            │
                       ▼                         ▼
              assistant_delta events      SentenceSegmenter
              (live text in UI)                  │ complete sentences
                                                 │ clean_for_speech() strips markdown
                                                 ▼
                                     TTSRouter ──en──▶ Kokoro (24 kHz)
                                          │     └─ta──▶ Piper  (22.05→24 kHz)
                                                 │ 24kHz PCM chunks
                                                 ▼
                                       binary WS frames ──▶ client playback queue
```

States: `listening → transcribing → generating → speaking → listening`.

**Language routing:** STT returns the detected language. If `language_probability < 0.7`, it defaults to `en` (safer — Kokoro quality is higher). The detected language is sent to the client in `user_transcript` and routed to the matching TTS engine. Tamil falls back to Kokoro if the Piper model isn't loaded.

**Markdown stripping:** the LLM occasionally emits `*emphasis*`/`` `code` ``/bullets despite the prompt. `clean_for_speech()` (`backend/core/segmenter.py`) removes them before TTS so they aren't read aloud. The on-screen streamed text is left as generated.

**Barge-in:** VAD keeps running while the assistant speaks. New user speech cancels the in-flight LLM stream and TTS tasks, sends `interrupted`, and the client flushes its audio queue. Partial assistant text is persisted.

**Blocking inference** (STT/TTS) runs in thread executors; the event loop never blocks.

**History windowing:** system prompt + most recent turns fitted to the 8k context with a ~4 chars/token heuristic (`pipeline._windowed_messages`).

## Personas (conversational modes)

Before a conversation, the user picks **who they're talking to**. Each persona (`config/personas/*.yaml`, loaded by `backend/core/personas.py`) is a distinct system prompt + behavior flags:

| Persona | Role | Special |
|---|---|---|
| Clarity | philosophical mentor (default) | — |
| Engineer | technical sounding board | — |
| General | open, casual companion | — |
| Coach | next steps + accountability | — |
| Friend | a friend who knows you | `proactive` + `cross_session_memory` |

The persona is **locked per conversation** — stored in the `sessions.persona` column, chosen on the Begin screen, shown in the session drawer. Resuming a saved conversation restores its persona; you can't change a conversation's voice mid-way.

**Friend** is special on two axes:
- *Proactive*: on a fresh Friend conversation the pipeline generates and speaks a greeting first (`assistant_greeting` event) — the user doesn't have to start.
- *Cross-session memory*: when a Friend conversation ends (disconnect, or switching away), the LLM writes a 1–3 sentence summary into the `memories` table. The next Friend conversation injects those summaries into the `{memory}` slot of its prompt, so Friend "remembers" across sessions. Summaries are bounded (most-recent N) so they never blow the context budget. The prompt forbids inventing history not in memory.

## Persistence

SQLite (`backend/db.py`) in the `clarity-data` volume: `sessions` (with `persona`), `messages`, and `memories` (Friend's rolling summaries) tables. The first user message becomes the session title. A lightweight migration (`Database._migrate`) adds the `persona` column to pre-existing DBs. The frontend stores the active session id in `localStorage` and resumes it over the WS.

## Frontend (Quiet Room)

Single screen (`frontend/src/App.tsx`). Three hooks own all the machinery:

- `useMicStream` — AudioWorklet capturing 16 kHz int16 PCM (~64 ms chunks), `echoCancellation: true`
- `usePlayback` — Web Audio queue for gapless 24 kHz playback, instant flush on interrupt
- `useConversation` — WS protocol client (Zod-validated), reconnect, session switching

Latency: ~1.5–3 s from end of speech to first audio (Tamil tends to be faster; English replies are longer). Per-stage timings exposed at `/api/health`.
