# ClarityMentor FastAPI Backend

Clean, modular FastAPI backend for the ClarityMentor voice system with persistent model loading and WebSocket streaming.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend (main.py)                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  WebSocket Handler (/ws/voice)                          │
│  └─ Receives audio bytes                                │
│  └─ Returns: transcript, emotion, response, audio       │
│                                                          │
│  REST Endpoints (/api/*)                                │
│  └─ /health - Service health check                      │
│  └─ /sessions - Create/manage sessions                  │
│  └─ /text-chat - Text-only chat endpoint                │
│                                                          │
│  Service Layer (Singletons)                             │
│  ├─ ModelService - Loads all models once at startup     │
│  ├─ STTService - Speech-to-Text                         │
│  ├─ TTSService - Text-to-Speech                         │
│  ├─ EmotionService - Speech + text emotion fusion       │
│  ├─ LLMService - ClarityMentor inference                │
│  └─ SessionService - Conversation management            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Key Features

- **Singleton Model Loading**: All models load once at startup, kept in memory
- **WebSocket Streaming**: Real-time bidirectional audio/text communication
- **Emotion Fusion**: Dual-channel emotion detection (speech + text)
- **Session Management**: Persistent conversation history per session
- **Error Handling**: Graceful error messages and recovery
- **Async/Await**: Non-blocking I/O for better performance

## Installation

### Install Dependencies

```bash
pip install -r requirements_backend.txt
pip install -r ../requirements_voice.txt  # Existing voice dependencies
```

### Verify Existing Models

The backend reuses your existing trained models:
- `scripts/voice/stt.py` - DistilWhisper
- `scripts/voice/tts.py` - pyttsx3/Parler-TTS
- `scripts/emotion/text_emotion.py` - DistilRoBERTa
- `scripts/emotion/speech_emotion.py` - Speech emotion detector
- `scripts/emotion/fusion.py` - Emotion fusion
- `models/claritymentor-lora/final/` - Your trained LLM

## Running the Server

```bash
# From the backend directory
uvicorn main:app --reload

# Or with custom settings
uvicorn main:app --host 0.0.0.0 --port 8000
```

You should see:
```
========================================================================
CLARITYMENTOR FASTAPI BACKEND - STARTUP
========================================================================

[1/5] Loading STT model (DistilWhisper)...
✓ STT model loaded
[2/5] Loading TTS model (pyttsx3/Parler)...
✓ TTS model loaded
[3/5] Loading emotion models (Text + Speech)...
✓ Emotion models loaded
[4/5] Loading LLM (ClarityMentor)...
✓ LLM model loaded
[5/5] Loading VAD (Silero)...
✓ VAD model loaded

✓ All services initialized and ready!

WebSocket endpoint: ws://localhost:2323/ws/voice
Health check: http://localhost:2323/api/health
```

## API Endpoints

### WebSocket: Voice Streaming

```
ws://localhost:2323/ws/voice
```

**Protocol:**
1. Client sends: Audio bytes (PCM 16-bit mono)
2. Server sends:
   - `{"type": "status", "message": "..."}`
   - `{"type": "transcript", "text": "..."}`
   - `{"type": "emotion", "data": {...}}`
   - `{"type": "response", "text": "..."}`
   - Audio bytes (PCM 16-bit mono)

### REST: Health Check

```bash
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "timestamp": "2026-02-03T12:00:00"
}
```

### REST: Create Session

```bash
POST /api/sessions
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-03T12:00:00"
}
```

### REST: Get Session History

```bash
GET /api/sessions/{session_id}/history
```

Response:
```json
{
  "session_id": "...",
  "created_at": "...",
  "turns": [
    {
      "role": "user",
      "content": "How are you?",
      "emotion": {"primary_emotion": "neutral", "confidence": 0.8},
      "timestamp": "..."
    },
    {
      "role": "assistant",
      "content": "I am well...",
      "emotion": null,
      "timestamp": "..."
    }
  ],
  "emotion_timeline": [...]
}
```

### REST: Text Chat

```bash
POST /api/text-chat
Content-Type: application/json

{
  "text": "How are you?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"  # optional
}
```

Response:
```json
{
  "session_id": "...",
  "response": "I am well...",
  "emotion": {"primary_emotion": "neutral", "confidence": 0.8}
}
```

### REST: Delete Session

```bash
DELETE /api/sessions/{session_id}
```

## Testing

### Test with WebSocket Client

```bash
# Terminal 1: Start server
uvicorn main:app --reload

# Terminal 2: Run test client
python test_client.py

# Or with audio file
python test_client.py /path/to/audio.wav
```

### Performance Comparison

Compare with old CLI:

```bash
# Old CLI (models load every turn: 5-7s)
time ../venv/bin/python ../scripts/voice_inference.py

# New FastAPI (models persistent: 2-3s)
time python test_client.py
```

Expected improvement: **50-60% faster**

## File Structure

```
backend/
├── main.py                 # FastAPI app with lifespan
├── config.py              # Configuration management
├── test_client.py         # Test WebSocket client
├── README.md              # This file
│
├── api/                   # API layer
│   ├── __init__.py
│   ├── websocket.py      # WebSocket handler
│   └── rest.py           # REST endpoints
│
├── services/              # Service layer (singletons)
│   ├── __init__.py
│   ├── model_service.py  # Model management
│   ├── stt_service.py    # Speech-to-text
│   ├── tts_service.py    # Text-to-speech
│   ├── emotion_service.py # Emotion detection
│   ├── llm_service.py    # LLM inference
│   └── session_service.py # Session management
│
├── models/                # Pydantic data models
│   ├── __init__.py
│   ├── request.py        # Request models
│   └── response.py       # Response models
│
└── core/                  # Utilities
    ├── __init__.py
    ├── exceptions.py     # Custom exceptions
    └── audio_utils.py    # Audio conversion
```

## Key Implementation Details

### Singleton Pattern

All services use FastAPI's dependency injection pattern with shared `ModelService` instance:

```python
# main.py
model_service = ModelService()  # Singleton
stt_service = STTService(model_service)
tts_service = TTSService(model_service)
# etc.
```

### Lifespan Context Manager

Models load once at startup, cleaned up at shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await model_service.initialize()  # Load all models once
    yield
    # Shutdown
    await model_service.shutdown()    # Cleanup
```

### Async/Thread Pool

Blocking operations run in thread pools:

```python
# Non-blocking TTS
async def synthesize(self, text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, self._synthesize_blocking, text
    )
```

### WebSocket Protocol

Streaming pipeline with intermediate status updates:

```
1. Receive audio bytes
   ↓
2. Status: "Transcribing..."
3. Send: {"type": "transcript", "text": "..."}
   ↓
4. Status: "Detecting emotion..."
5. Send: {"type": "emotion", "data": {...}}
   ↓
6. Status: "Generating response..."
7. Send: {"type": "response", "text": "..."}
   ↓
8. Status: "Synthesizing speech..."
9. Send: Audio bytes
```

## Troubleshooting

### Models take too long to load

First run will download models from Hugging Face. Subsequent runs use cached models.

### CUDA out of memory

The backend loads all models at startup. If you get OOM:
1. Close other GPU applications
2. Check memory with `nvidia-smi`
3. Reduce `max_response_tokens` in voice_config.yaml

### WebSocket connection refused

Ensure server is running:
```bash
# Check if port 8000 is listening
lsof -i :8000

# Kill if stuck
fuser -k 8000/tcp
```

### Import errors

Ensure you're running from correct directory:
```bash
cd /home/lebi/projects/mentor
uvicorn backend.main:app --reload
```

## Next Steps

1. **Add Frontend**: Create a web UI or mobile app to connect to WebSocket
2. **Add Database**: Store sessions in PostgreSQL/MongoDB instead of memory
3. **Add Authentication**: Implement user accounts and API keys
4. **Add Logging**: Store logs to files for debugging
5. **Add Metrics**: Monitor latency, accuracy, and resource usage
6. **Add Scaling**: Deploy with Docker and Kubernetes for production

## License

Same as ClarityMentor main project.
