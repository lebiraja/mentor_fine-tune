# FIXES

Running log of significant fixes and the reasoning behind them.

## 2026-06-12 — v3 Tamil review fixes

Audit of the bilingual (Tamil+English) change. The pipeline worked end-to-end live
(EN reply in ~3s, TA reply in ~1.6s, correct language detection), but several issues
were found and fixed:

- **Broken unit tests.** STT now returns `STTResult` (text + language) and TTS takes a
  `language` arg, but the test fakes still returned bare strings / single-arg synth.
  Updated `FakeSTT`/`FakeTTS` in `conftest.py`; added tests asserting Tamil detection
  routes through to the TTS engine and typed turns default to English. 27→36 passing.
- **TTS read markdown aloud.** The LLM still emits `*emphasis*`, `` `code` ``, bullets
  and `#` despite the prompt forbidding them, so the voice literally said "asterisk".
  Added `clean_for_speech()` (`segmenter.py`), applied per-sentence before TTS. On-screen
  text is left as generated.
- **`_resample(b"")` crashed** with `ValueError` (np.interp on empty points). Guarded
  empty / <2-sample / same-rate inputs.
- **Protocol drift.** `user_transcript` now carries `language` + `language_probability`;
  added to the ws.py docstring and the frontend Zod schema.
- **Docs.** `architecture.md` still described the v2 Parakeet / python-slim / English-only
  stack — rewritten for v3. Removed a duplicate Tamil plan doc; fixed the README link.
  Added `.obsidian/` to `.gitignore`. Bumped version strings v2→v3.

Note: the design doc predicted latency would *drop* to ~1.8s with GPU STT; in practice
English first-audio is ~3s because Whisper + LLM share the 6 GB GPU and English replies
are longer. Still within the ≤2.5s-ish target for short turns; acceptable.

## 2026-06-11 — repo cleanup after v2 verification

- Removed the v1 training pipeline (`scripts/training/`, `requirements-training.txt`), dataset artifacts (`data/`, `evaluation/`, `reddit_dataset_170/`) and dev caches from the working tree. All of it remains in git history on `v2-rebuild` if ever needed.
- Rewrote `.gitignore` (secrets first: `.env` and variants never committable) and `.dockerignore` (build contexts no longer ship models/docs/caches).
- Silero VAD fix (see below) shipped the same day: the raw ONNX graph needs a 64-sample rolling context prepended to every 512-sample frame, i.e. input `[1, 576]` — without it speech probability sits near zero.

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
