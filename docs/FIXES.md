# FIXES

Running log of significant fixes and the reasoning behind them.

## 2026-06-11 — v2 rebuild (branch `v2-rebuild`)

The v1 stack never worked end-to-end. Root causes found in the audit, all addressed by the rebuild rather than patched:

1. **TTS audio never played** — the WebSocket client never set `binaryType = 'arraybuffer'`, so binary frames arrived as Blobs and were fed to `JSON.parse`. v2: set explicitly in `useConversation`.
2. **Text chat 404** — frontend posted `/api/chat`, backend served `/api/text-chat`. v2: one WS protocol for both voice and text, schemas mirrored in Zod.
3. **Startup bricked without the LoRA dir** — model load failure killed the app and the `service_healthy` gate kept the frontend down. v2: stock GGUF served by llama.cpp; backend fails loud and independently.
4. **Raw headerless PCM fed to `decodeAudioData`** — always threw. v2: playback builds AudioBuffers directly from int16 PCM.
5. **Fake emotion detection** — speech "emotion" was an RMS volume heuristic that outvoted the real text classifier. v2: feature removed entirely.
6. **15–60 s silent turns** — fully sequential batch pipeline. v2: streamed tokens → sentence-chunked TTS → streamed playback, with VAD barge-in.
7. **Event-loop blocking inference** — STT/emotion ran synchronously in async handlers. v2: thread executors everywhere.
8. **`asyncio` package in requirements** — the ancient PyPI backport that shadows stdlib. Removed; everything pinned with `==`.
9. **Sessions split-brain + unbounded memory** — WS and REST used different in-memory sessions, never expired. v2: SQLite, one session per conversation, resumable.
10. **CUDA-devel backend image (~8 GB)** — v2 backend is `python:3.12-slim`; only the llama.cpp container uses the GPU.
