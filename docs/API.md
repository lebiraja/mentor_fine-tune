# API

Base URL: `http://localhost:2000` (nginx) or `http://127.0.0.1:2324` (backend direct).

## REST

### `GET /api/health`
```json
{
  "status": "healthy" | "degraded",
  "engines_loaded": true,
  "llm_reachable": true,
  "latency_ms": { "stt_ms": 280.1, "llm_ttft_ms": 310.5, "first_audio_ms": 1450.2 }
}
```

### `GET /api/sessions`
`{ "sessions": [{ "id", "title", "created_at", "message_count" }] }`

### `GET /api/sessions/{id}/messages`
`{ "session_id", "messages": [{ "role": "user"|"assistant", "content", "created_at" }] }` — 404 if unknown.

### `DELETE /api/sessions/{id}`
`{ "deleted": "<id>" }` — 404 if unknown.

## WebSocket `/ws/chat`

One connection = one live conversation. Binary frames are audio; text frames are JSON.

### Client → server
| Message | Meaning |
|---|---|
| binary frame | 16 kHz mono **int16 PCM** mic audio, streamed continuously |
| `{"type":"set_session","session_id":"<id>"\|null}` | resume a session (null/unknown ⇒ create new). Send once after connect. |
| `{"type":"user_text","text":"..."}` | typed turn (skips STT, same pipeline) |
| `{"type":"mute","muted":true\|false}` | muted ⇒ server discards mic audio |

### Server → client
| Message | Meaning |
|---|---|
| `{"type":"session","session_id"}` | active session confirmed |
| `{"type":"state","state"}` | `listening` / `transcribing` / `generating` / `speaking` |
| `{"type":"user_transcript","text"}` | what STT heard |
| `{"type":"assistant_delta","text"}` | streaming token(s) |
| `{"type":"assistant_done","text"}` | full reply text |
| `{"type":"interrupted"}` | barge-in happened — flush your playback queue |
| `{"type":"error","message"}` | turn failed; pipeline returns to listening |
| binary frame | 24 kHz mono **int16 PCM** TTS audio chunk (one per sentence) |

Schemas are mirrored in `frontend/src/types/protocol.ts` (Zod).
