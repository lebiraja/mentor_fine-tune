# Port Configuration Changed to 2323

## Summary of Changes

The FastAPI backend has been configured to use **port 2323** instead of the default port 8000.

## Files Modified

### 1. `backend/config.py`
```python
# Changed from:
PORT: int = 8000

# To:
PORT: int = 2323
```

### 2. `backend/main.py`
```python
# Updated startup messages to show:
print("\nWebSocket endpoint: ws://localhost:2323/ws/voice")
print("Health check: http://localhost:2323/api/health")
```

### 3. `backend/test_client.py`
```python
# Changed from:
uri = "ws://localhost:8000/ws/voice"

# To:
uri = "ws://localhost:2323/ws/voice"
```

### 4. `backend/README.md`
All references to `localhost:8000` → `localhost:2323`

### 5. `BACKEND_QUICKSTART.md`
All references to `localhost:8000` → `localhost:2323`

## New Files Created

### 1. `run_backend.sh` (Executable)
Convenient script to start the backend:
```bash
./run_backend.sh
```

### 2. `run_test_client.sh` (Executable)
Convenient script to test with WebSocket client:
```bash
./run_test_client.sh
```

## Endpoints on Port 2323

### WebSocket
- `ws://localhost:2323/ws/voice` - Voice streaming

### REST API
- `http://localhost:2323/api/health` - Health check
- `http://localhost:2323/api/sessions` - Session management
- `http://localhost:2323/api/text-chat` - Text chat
- `http://localhost:2323/api/sessions/{id}/history` - Get history
- `http://localhost:2323/api/sessions/{id}` - Delete session

## Quick Start with New Port

```bash
cd /home/lebi/projects/mentor

# Terminal 1: Start backend on port 2323
./run_backend.sh

# Terminal 2: Test with WebSocket client
./run_test_client.sh

# Terminal 3 (optional): Test REST endpoints
curl http://localhost:2323/api/health
```

## Verification

All port references have been updated:
- ✅ `backend/config.py` - Default PORT set to 2323
- ✅ `backend/main.py` - Startup messages show 2323
- ✅ `backend/test_client.py` - Test client connects to 2323
- ✅ `backend/README.md` - Documentation updated
- ✅ `BACKEND_QUICKSTART.md` - Quick start updated
- ✅ Startup scripts created for easy execution

## Manual Port Configuration

If you need to use a different port than 2323, simply edit:

```bash
nano backend/config.py
# Find: PORT: int = 2323
# Change to your desired port
```

Or pass port as environment variable:
```bash
PORT=3000 ./venv/bin/python -m uvicorn backend.main:app
```

Or via uvicorn CLI:
```bash
./venv/bin/python -m uvicorn backend.main:app --port 3000
```

## Testing the New Port

```bash
# Test WebSocket
./run_test_client.sh

# Test REST API
curl http://localhost:2323/api/health

# Check if port is listening
lsof -i :2323
```

## Status

✅ **Port 2323 is fully configured and ready to use**

All documentation, scripts, and configuration files have been updated to use port 2323 consistently.

---

**Date:** 2026-02-03
**Status:** Complete
**Action Required:** Run `./run_backend.sh` to start the server
