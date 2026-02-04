# 🚀 ClarityMentor - Complete Deployment Commands

## Quick Start (Automated)

### One Command - Everything Automated
```bash
./deploy.sh
```

This will:
1. ✅ Check model files exist
2. ✅ Create required directories
3. ✅ Create .env file if missing
4. ✅ Ask GPU or CPU mode
5. ✅ Stop any existing containers
6. ✅ Build Docker images
7. ✅ Start all services
8. ✅ Wait for models to load
9. ✅ Show access URLs

---

## Manual Step-by-Step Commands

### Step 1: Verify Model Files
```bash
# Check if model files exist
ls -la models/claritymentor-lora/final/

# You should see:
# adapter_model.safetensors (74MB)
# tokenizer.json (11MB)
# vocab.json (2.7MB)
# merges.txt (1.6MB)
# + config files
```

### Step 2: Create Required Directories
```bash
mkdir -p logs data
```

### Step 3: Create Environment File (if needed)
```bash
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=2323
DEBUG=False
PYTHONUNBUFFERED=1
MODEL_PATH=/app/models/claritymentor-lora/final
REDIS_HOST=cache
REDIS_PORT=6379
LOG_LEVEL=INFO
EOF
```

### Step 4: Build Docker Images

**Option A: With GPU (Recommended)**
```bash
docker-compose build
```

**Option B: CPU Only**
```bash
docker-compose -f docker-compose.cpu.yml build
```

Build time: 5-10 minutes on first run

### Step 5: Start Services

**Option A: With GPU**
```bash
docker-compose up -d
```

**Option B: CPU Only**
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

### Step 6: Monitor Startup

```bash
# Watch logs (all services)
docker-compose logs -f

# Watch backend only (to see model loading)
docker-compose logs -f backend

# Check container status
docker-compose ps
```

### Step 7: Wait for Models to Load

The backend takes ~2-3 minutes to load models. Watch for:
```
✓ Loading STT model...
✓ Loading TTS model...
✓ Loading emotion models...
✓ Loading LLM model...
✓ All models loaded and ready!
```

### Step 8: Verify Deployment

```bash
# Check backend health
curl http://localhost:2323/api/health

# Should return:
# {"status":"healthy","models_loaded":true,"timestamp":"..."}

# Check frontend
curl http://localhost:2000/

# Should return HTML
```

---

## Model File Mounting (Automatically Done)

The model files are automatically mounted when you start the containers:

```yaml
# In docker-compose.yml
backend:
  volumes:
    # Model files (read-only)
    - ./models/claritymentor-lora/final:/app/models/claritymentor-lora/final:ro
```

**Host Path:**
```
./models/claritymentor-lora/final/
├── adapter_model.safetensors
├── tokenizer.json
├── vocab.json
└── ...
```

**Container Path:**
```
/app/models/claritymentor-lora/final/
├── adapter_model.safetensors
├── tokenizer.json
├── vocab.json
└── ...
```

### Verify Models Are Mounted

```bash
# Check inside container
docker-compose exec backend ls -la /app/models/claritymentor-lora/final/

# You should see all model files listed
```

---

## Access Points

After deployment:

- **Frontend UI:** http://localhost:2000
- **Backend API:** http://localhost:2323
- **API Health:** http://localhost:2323/api/health
- **WebSocket:** ws://localhost:2323/ws/voice
- **Redis:** localhost:2999

---

## Common Commands

### Start/Stop

```bash
# Start services (GPU)
docker-compose up -d

# Start services (CPU)
docker-compose -f docker-compose.cpu.yml up -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart backend only
docker-compose restart backend

# Restart frontend only
docker-compose restart frontend
```

### Check Status

```bash
# Container status
docker-compose ps

# Detailed info
docker-compose ps -a

# Resource usage
docker stats
```

### Enter Containers

```bash
# Enter backend container
docker-compose exec backend bash

# Enter frontend container
docker-compose exec frontend sh

# Run command in backend
docker-compose exec backend python --version
```

### Verify Model Mounting

```bash
# Check models in backend container
docker-compose exec backend ls -la /app/models/claritymentor-lora/final/

# Check config files
docker-compose exec backend ls -la /app/config/

# Check if models are loaded
docker-compose logs backend | grep "Loading"
```

---

## Update Model Files

To update model files without rebuilding:

```bash
# 1. Stop backend
docker-compose stop backend

# 2. Replace model files on host
cp new_model/* models/claritymentor-lora/final/

# 3. Start backend (models will be re-read from mount)
docker-compose start backend

# 4. Watch logs to confirm
docker-compose logs -f backend
```

---

## Rebuild Images

If you need to rebuild:

```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild backend only
docker-compose build --no-cache backend

# Rebuild frontend only
docker-compose build --no-cache frontend

# Rebuild and restart
docker-compose up -d --build
```

---

## Complete Deployment Flow

### GPU Mode (Recommended)

```bash
# 1. Verify prerequisites
ls -la models/claritymentor-lora/final/

# 2. Build images
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Watch logs
docker-compose logs -f backend

# 5. Wait for "All models loaded and ready!"

# 6. Test health
curl http://localhost:2323/api/health

# 7. Open browser
# Navigate to: http://localhost:2000
```

### CPU Mode

```bash
# 1. Verify prerequisites
ls -la models/claritymentor-lora/final/

# 2. Build images
docker-compose -f docker-compose.cpu.yml build

# 3. Start services
docker-compose -f docker-compose.cpu.yml up -d

# 4. Watch logs
docker-compose -f docker-compose.cpu.yml logs -f backend

# 5. Wait for models to load

# 6. Test health
curl http://localhost:2323/api/health

# 7. Open browser
# Navigate to: http://localhost:2000
```

---

## Troubleshooting Commands

### Model Files Not Found

```bash
# Check on host
ls -la models/claritymentor-lora/final/

# Check mount in container
docker-compose exec backend ls -la /app/models/claritymentor-lora/final/

# Check volume in docker-compose.yml
grep -A 5 "volumes:" docker-compose.yml
```

### Backend Not Starting

```bash
# View logs
docker-compose logs backend

# Check container status
docker-compose ps backend

# Restart backend
docker-compose restart backend

# Check health endpoint
curl http://localhost:2323/api/health
```

### Port Conflicts

```bash
# Check what's using ports
lsof -i :2323
lsof -i :2000

# Kill processes or change ports in docker-compose.yml
```

### Clean Slate

```bash
# Stop everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean Docker system
docker system prune -a

# Start fresh
docker-compose build
docker-compose up -d
```

---

## Testing Commands

### Test Backend API

```bash
# Health check
curl http://localhost:2323/api/health

# Create session
curl -X POST http://localhost:2323/api/sessions

# Send text message
curl -X POST http://localhost:2323/api/text-chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, how are you?"}'
```

### Test Frontend

```bash
# Check if frontend is up
curl http://localhost:2000/

# Check if it returns HTML
curl -I http://localhost:2000/
```

### Test WebSocket

```bash
# From host with Python
python3 << 'EOF'
import websocket
ws = websocket.create_connection('ws://localhost:2323/ws/voice')
print("✓ WebSocket connected")
ws.close()
EOF
```

---

## Monitoring Commands

```bash
# Real-time logs
docker-compose logs -f

# Container stats
docker stats

# Disk usage
docker system df

# Network info
docker network inspect claritymentor-network

# Volume info
docker volume ls
docker volume inspect claritymentor_redis-data
```

---

## All-in-One Command Sheet

```bash
# === SETUP ===
mkdir -p logs data
ls -la models/claritymentor-lora/final/

# === BUILD (GPU) ===
docker-compose build

# === BUILD (CPU) ===
docker-compose -f docker-compose.cpu.yml build

# === START (GPU) ===
docker-compose up -d

# === START (CPU) ===
docker-compose -f docker-compose.cpu.yml up -d

# === MONITOR ===
docker-compose logs -f backend
docker-compose ps
docker stats

# === TEST ===
curl http://localhost:2323/api/health
curl http://localhost:2000/

# === VERIFY MODELS ===
docker-compose exec backend ls -la /app/models/claritymentor-lora/final/

# === STOP ===
docker-compose down

# === CLEAN ===
docker-compose down -v
docker system prune -a
```

---

## Summary

**Easiest Way:**
```bash
./deploy.sh
```

**Manual Way (GPU):**
```bash
docker-compose build && docker-compose up -d
```

**Manual Way (CPU):**
```bash
docker-compose -f docker-compose.cpu.yml build && \
docker-compose -f docker-compose.cpu.yml up -d
```

**Access:**
- Frontend: http://localhost:2000
- Backend: http://localhost:2323

**Model mounting happens automatically via docker-compose.yml volumes!**

---

**Status:** Ready to deploy! 🚀

**Time to deploy:** ~5 minutes (first time), ~1 minute (subsequent)

**Last Updated:** 2026-02-04
