# 🎤 Voice System Fix - WebSocket Handler

## Problem
Voice-to-voice mode was connecting but immediately disconnecting with error:
```
[WS] Unexpected error: Cannot call "receive" once a disconnect message has been received.
```

## Root Cause
WebSocket handler wasn't checking for disconnect messages properly. After client disconnected, calling `receive()` again caused the crash.

## Fix Applied

**File**: `backend/api/websocket.py`

**Before:**
```python
while True:
    data = await websocket.receive()
    
    if "bytes" not in data:
        continue
```

**After:**
```python
while True:
    data = await websocket.receive()
    
    # Check for disconnect
    if data.get("type") == "websocket.disconnect":
        break
    
    if "bytes" not in data:
        continue
```

## How Voice Mode Works

1. **Browser** → Records audio → Sends as WebSocket binary message
2. **Backend** → Receives audio bytes
3. **STT** → Transcribes to text (distil-whisper on GPU)
4. **Emotion** → Detects emotion from audio + text
5. **LLM** → Generates empathetic response (Qwen 1.5B + LoRA)
6. **TTS** → Synthesizes speech (CosyVoice 0.5B with emotion control)
7. **Backend** → Resamples audio to 16kHz and sends bytes back to browser
8. **Browser** → Plays audio response

## Testing Voice Mode

1. Open http://localhost:2000
2. Click **"Voice Mode"** button
3. Click **microphone icon** to start recording
4. Speak your message
5. Click **stop** when done
6. Wait for:
   - Transcription
   - Emotion detection
   - AI response generation
   - Audio synthesis
7. AI response plays automatically

## Backend Status After Fix

Wait ~2-3 minutes for backend to reload all models:
```bash
docker-compose logs -f backend
```

Look for:
```
✓ All models loaded and ready!
Application startup complete
```

## Test Commands

```bash
# Check backend health
curl http://localhost:2323/api/health

# Check WebSocket endpoint exists
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:2323/ws/voice

# Monitor WebSocket connections
docker-compose logs -f backend | grep "\[WS\]"
```

## Expected Logs (Good)

```
[WS] New session: <uuid>
INFO: connection open
[WS] Processing audio...
[WS] Transcription: "Hello, I need help"
[WS] Emotion detected: anxious
[WS] Generated response...
[WS] Session <uuid> disconnected
```

## Common Issues

### Issue: "Backend Offline"
**Solution**: Refresh browser (Ctrl+Shift+R)

### Issue: Microphone permission denied
**Solution**: Allow microphone in browser settings

### Issue: No audio playback
**Solution**: Unmute icon in voice mode

### Issue: Connection drops immediately
**Solution**: Check this fix is applied and backend restarted

## Architecture

```
Frontend (Browser)
  ↓ WebSocket /ws/voice
Nginx Proxy
  ↓ proxy_pass
Backend WebSocket Handler
  ↓
┌─────────────────────────┐
│ 1. Receive audio bytes  │
│ 2. STT (Whisper GPU)    │
│ 3. Emotion Detection    │
│ 4. LLM Response         │
│ 5. TTS (CosyVoice)      │
│ 6. Send audio bytes     │
└─────────────────────────┘
```

## Status

- ✅ WebSocket handler fixed
- ⏳ Backend restarting (loading models)
- ⏳ Wait 2-3 minutes for full readiness
- 🎤 Voice mode will be functional after reload

---

**Test after backend shows "healthy":**
```bash
docker-compose ps
# Wait for: claritymentor-backend (healthy)
```

Then try voice mode in browser!
