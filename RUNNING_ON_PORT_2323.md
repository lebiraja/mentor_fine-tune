# Running ClarityMentor FastAPI Backend on Port 2323

The backend is now configured to run on **port 2323** instead of the default 8000.

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
cd /home/lebi/projects/mentor

# Terminal 1: Start the backend
./run_backend.sh

# Terminal 2: Test with WebSocket client
./run_test_client.sh
```

### Option 2: Using uvicorn directly

```bash
cd /home/lebi/projects/mentor

# Terminal 1: Start the backend
./venv/bin/python -m uvicorn backend.main:app --port 2323

# Terminal 2: Test with WebSocket client
./venv/bin/python backend/test_client.py
```

### Option 3: Using uvicorn with all options

```bash
cd /home/lebi/projects/mentor

# Terminal 1: Start the backend with reload for development
./venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 2323 --reload

# Terminal 2: Test with WebSocket client
./venv/bin/python backend/test_client.py
```

## Endpoints on Port 2323

### WebSocket
- **Endpoint:** `ws://localhost:2323/ws/voice`
- **Purpose:** Real-time voice streaming
- **Usage:** Send audio bytes, receive transcript + emotion + response + audio

### REST API
- **Health Check:** `http://localhost:2323/api/health`
- **Create Session:** `POST http://localhost:2323/api/sessions`
- **Get History:** `GET http://localhost:2323/api/sessions/{id}/history`
- **Text Chat:** `POST http://localhost:2323/api/text-chat`
- **Delete Session:** `DELETE http://localhost:2323/api/sessions/{id}`

## Example Requests

### Health Check
```bash
curl http://localhost:2323/api/health
```

Response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "timestamp": "2026-02-03T20:07:00"
}
```

### Create Session
```bash
curl -X POST http://localhost:2323/api/sessions
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-03T20:07:00"
}
```

### Text Chat
```bash
curl -X POST http://localhost:2323/api/text-chat \
  -H "Content-Type: application/json" \
  -d '{"text":"How are you today?"}'
```

Response:
```json
{
  "session_id": "550e8400-...",
  "response": "I am doing well, thank you for asking...",
  "emotion": {
    "primary_emotion": "joy",
    "confidence": 0.85
  }
}
```

## WebSocket Test Client

The test client automatically connects to `ws://localhost:2323/ws/voice`:

```bash
# Generate silence and test full pipeline
./run_test_client.sh

# Or use audio file
./run_test_client.sh /path/to/audio.wav
```

## Port Configuration

### Changing the Port

If you need to use a different port, edit `backend/config.py`:

```python
class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 2323  # Change this to your desired port
    DEBUG: bool = True
```

Then update test client in `backend/test_client.py`:

```python
uri = "ws://localhost:2323/ws/voice"  # Update port here
```

## Troubleshooting

### Port already in use

```bash
# Check what's using port 2323
lsof -i :2323

# Kill the process (if it's the old backend)
fuser -k 2323/tcp

# Then restart
./run_backend.sh
```

### Connection refused

```bash
# Make sure the server is running in another terminal
# Check if port 2323 is listening
netstat -tulpn | grep 2323

# Or use lsof
lsof -i :2323
```

### WebSocket connection timeout

```bash
# Make sure server is running and listening
./run_backend.sh

# Then in another terminal, test
./run_test_client.sh
```

## Performance

Expected performance with persistent model loading:

| Metric | Value |
|--------|-------|
| Time per turn | 2-3 seconds |
| Model loading | Once at startup (1-2 min) |
| Subsequent turns | 2-3s each |
| VRAM usage | 3-4GB (persistent) |
| VRAM peak | 3-4GB |

## Integration with Frontend

To connect a frontend (React, Vue, etc.) to the WebSocket:

```javascript
// JavaScript/TypeScript
const ws = new WebSocket('ws://localhost:2323/ws/voice');

ws.onopen = () => {
  // Send audio bytes
  ws.send(audioBuffer);
};

ws.onmessage = (event) => {
  // Receive responses
  if (event.data instanceof ArrayBuffer) {
    // Binary audio data
    const audioData = new Uint8Array(event.data);
  } else {
    // JSON message
    const message = JSON.parse(event.data);
    if (message.type === 'transcript') {
      console.log('Transcript:', message.text);
    } else if (message.type === 'emotion') {
      console.log('Emotion:', message.data);
    } else if (message.type === 'response') {
      console.log('Response:', message.text);
    }
  }
};
```

## Monitoring

### View Startup Output

The startup script will show:
```
=========================================================================
Starting ClarityMentor FastAPI Backend
=========================================================================

Port: 2323
WebSocket: ws://localhost:2323/ws/voice
REST API: http://localhost:2323/api/*

Press Ctrl+C to stop the server
=========================================================================

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

✓ All models loaded and ready!

WebSocket endpoint: ws://localhost:2323/ws/voice
Health check: http://localhost:2323/api/health
```

### Monitor Requests

When requests come in, you'll see:
```
[WS] New session: 550e8400-e29b-41d4-a716-446655440000
[WS] Session 550e8400-... disconnected
```

## Documentation

- **Quick Start:** `BACKEND_QUICKSTART.md`
- **Full API Docs:** `backend/README.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`

---

**Backend Status:** ✅ Running on port 2323

**Next Step:** Run `./run_backend.sh` to start the server!
