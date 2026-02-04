# 🐳 ClarityMentor Docker Deployment Guide

Complete Docker setup for ClarityMentor with backend, frontend, and optional Redis cache.

## 📋 Prerequisites

### Required
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### For GPU Support
- NVIDIA GPU with CUDA support
- NVIDIA Docker runtime
- nvidia-docker2 installed

---

## 🚀 Quick Start

### Option 1: With GPU (Recommended)

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: CPU Only

```bash
# Use CPU-only configuration
docker-compose -f docker-compose.cpu.yml up -d

# Check logs
docker-compose -f docker-compose.cpu.yml logs -f

# Stop services
docker-compose -f docker-compose.cpu.yml down
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  Host Machine (Your Computer)               │
│                                             │
│  Port 2000 → ┌──────────────────┐          │
│              │  Frontend         │          │
│              │  (Nginx + React)  │          │
│              └────────┬──────────┘          │
│                       │                     │
│              ┌────────▼──────────┐          │
│  Port 2323 → │  Backend          │          │
│              │  (FastAPI)        │          │
│              │  + Models         │          │
│              └────────┬──────────┘          │
│                       │                     │
│              ┌────────▼──────────┐          │
│  Port 2999 → │  Redis Cache      │          │
│              │  (Optional)       │          │
│              └───────────────────┘          │
│                                             │
│  Volumes:                                   │
│  - models/ → /app/models (backend)          │
│  - config/ → /app/config (backend)          │
│  - data/ → /app/data (backend)              │
│  - logs/ → /app/logs (backend)              │
└─────────────────────────────────────────────┘
```

---

## 📦 Services

### 1. Backend (Port 2323)
- **Image:** Custom Python 3.12
- **Purpose:** FastAPI server with ML models
- **Resources:** 4GB RAM, GPU optional
- **Health Check:** `http://localhost:2323/api/health`
- **Startup Time:** ~2 minutes (model loading)

### 2. Frontend (Port 2000)
- **Image:** Nginx Alpine + React build
- **Purpose:** Web UI with voice/text chat
- **Resources:** 256MB RAM
- **Health Check:** `http://localhost:2000/`
- **Startup Time:** ~10 seconds

### 3. Cache (Port 2999)
- **Image:** Redis 7 Alpine
- **Purpose:** Session storage (optional)
- **Resources:** 128MB RAM
- **Health Check:** Redis PING
- **Startup Time:** ~5 seconds

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```env
# Backend
HOST=0.0.0.0
PORT=2323
DEBUG=False

# Model Path (inside container)
MODEL_PATH=/app/models/claritymentor-lora/final

# Redis
REDIS_HOST=cache
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

### Volume Mounts

**Backend volumes (in docker-compose.yml):**

```yaml
volumes:
  # Model files (read-only, ~74MB)
  - ./models/claritymentor-lora/final:/app/models/claritymentor-lora/final:ro
  
  # Config files (read-only)
  - ./config:/app/config:ro
  
  # Data directory (read-write)
  - ./data:/app/data
  
  # Logs (read-write)
  - ./logs:/app/logs
```

**Why mount models as volume?**
- ✅ Models stay on host (not in image)
- ✅ Easy to update models without rebuild
- ✅ Smaller Docker image size
- ✅ Faster builds

---

## 🛠️ Build & Deploy

### Build Images

```bash
# Build both services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend

# Build without cache
docker-compose build --no-cache
```

### Start Services

```bash
# Start all services in background
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Start with logs
docker-compose up

# Start with build
docker-compose up --build -d
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

---

## 📊 Monitoring

### Check Status

```bash
# All services
docker-compose ps

# Detailed info
docker-compose ps -a

# Resources usage
docker stats
```

### View Logs

```bash
# All services
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# Specific service
docker-compose logs backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Health Checks

```bash
# Backend
curl http://localhost:2323/api/health

# Frontend
curl http://localhost:2000/

# Redis
docker-compose exec cache redis-cli ping
```

---

## 🧪 Testing

### Test Backend

```bash
# Health check
curl http://localhost:2323/api/health

# Create session
curl -X POST http://localhost:2323/api/sessions

# Text chat
curl -X POST http://localhost:2323/api/text-chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, how are you?"}'
```

### Test Frontend

Open browser: **http://localhost:2000**

1. Wait for "Backend Online" indicator
2. Click "Start Conversation"
3. Test text mode
4. Switch to voice mode
5. Test voice recording

### Test WebSocket

```bash
# Run test client inside backend container
docker-compose exec backend python -m backend.test_client
```

---

## 🔍 Troubleshooting

### Backend Won't Start

**Check logs:**
```bash
docker-compose logs backend
```

**Common issues:**
- Model files not found → Check volume mount
- Port 2323 in use → Change port in docker-compose.yml
- Out of memory → Increase Docker RAM limit
- GPU not available → Use docker-compose.cpu.yml

**Solution:**
```bash
# Check if model directory is mounted
docker-compose exec backend ls -la /app/models/claritymentor-lora/final/

# Verify config files
docker-compose exec backend ls -la /app/config/

# Check backend logs
docker-compose logs --tail=50 backend
```

### Frontend Build Fails

**Check:**
```bash
docker-compose logs frontend
```

**Common issues:**
- Node modules errors → Clean build: `docker-compose build --no-cache frontend`
- Build timeout → Increase Docker build timeout
- Nginx won't start → Check port 2000

**Solution:**
```bash
# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Model Loading Takes Too Long

**Expected times:**
- First load: 2-3 minutes
- Subsequent loads: 1-2 minutes

**If slower:**
```bash
# Check container resources
docker stats claritymentor-backend

# Check model files
docker-compose exec backend ls -lh /app/models/claritymentor-lora/final/

# Increase memory
# Edit docker-compose.yml, add:
# deploy:
#   resources:
#     limits:
#       memory: 8G
```

### GPU Not Working

**Check NVIDIA runtime:**
```bash
# Verify Docker can see GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If error, install nvidia-docker:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

**Use CPU fallback:**
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

### Port Conflicts

**Change ports in docker-compose.yml:**

```yaml
services:
  backend:
    ports:
      - "3000:2323"  # Change 2323 to 3000
  
  frontend:
    ports:
      - "3001:2000"  # Change 2000 to 3001
```

---

## 📁 File Structure

```
mentor/
├── docker-compose.yml          # Main compose file (with GPU)
├── docker-compose.cpu.yml      # CPU-only version
├── Dockerfile.backend          # Backend image
├── Dockerfile.frontend         # Frontend image
├── .dockerignore              # Build exclusions
├── .env                       # Environment variables
│
├── models/
│   └── claritymentor-lora/
│       └── final/             # ← Mounted to backend
│           ├── adapter_model.safetensors
│           ├── tokenizer.json
│           └── ...
│
├── config/                    # ← Mounted to backend
│   ├── voice_config.yaml
│   ├── emotion_prompts.yaml
│   └── system_prompt.txt
│
├── data/                      # ← Mounted to backend (RW)
│   └── ...
│
└── logs/                      # ← Mounted to backend (RW)
    └── claritymentor.log
```

---

## 🚀 Production Deployment

### Security Hardening

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - DEBUG=False
    # Add secrets
    secrets:
      - api_key
    # Read-only root filesystem
    read_only: true
    # No privilege escalation
    security_opt:
      - no-new-privileges:true

  frontend:
    # Add SSL certificate
    volumes:
      - ./certs:/etc/nginx/certs:ro
```

### Scaling

```bash
# Scale backend (load balancer needed)
docker-compose up -d --scale backend=3

# Use Docker Swarm or Kubernetes for production
```

### Backup

```bash
# Backup volumes
docker run --rm \
  -v claritymentor_redis-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis-backup.tar.gz /data

# Backup logs
tar czf logs-backup.tar.gz logs/
```

---

## 📊 Performance

### Resource Requirements

| Service | CPU | RAM | Disk | Startup |
|---------|-----|-----|------|---------|
| Backend | 2 cores | 4GB | 5GB | 2 min |
| Frontend | 0.5 cores | 256MB | 100MB | 10 sec |
| Redis | 0.1 cores | 128MB | 50MB | 5 sec |
| **Total** | **2.6 cores** | **4.4GB** | **5.2GB** | **2 min** |

### With GPU

- Adds: 2-4GB VRAM
- Speeds up: LLM inference (2x faster)

---

## 🎯 Next Steps

### After Deployment

1. ✅ Verify all services: `docker-compose ps`
2. ✅ Check health: `curl http://localhost:2323/api/health`
3. ✅ Test frontend: Open http://localhost:2000
4. ✅ Test voice mode
5. ✅ Monitor logs: `docker-compose logs -f`

### Maintenance

```bash
# Update code
git pull
docker-compose down
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Cleanup
docker-compose down -v
docker system prune -a
```

---

## 📞 Support

### Useful Commands

```bash
# Enter backend container
docker-compose exec backend bash

# Enter frontend container
docker-compose exec frontend sh

# Check backend Python environment
docker-compose exec backend pip list

# Check nginx config
docker-compose exec frontend nginx -t

# Restart service
docker-compose restart backend
```

### Debug Mode

```bash
# Enable debug logging
docker-compose exec backend \
  python -m uvicorn backend.main:app \
  --host 0.0.0.0 --port 2323 --reload --log-level debug
```

---

## ✅ Checklist

Before deploying:

- [ ] Docker and Docker Compose installed
- [ ] Model files in `models/claritymentor-lora/final/`
- [ ] Config files in `config/`
- [ ] Ports 2000, 2323, 2999 available
- [ ] `.env` file created
- [ ] 8GB RAM available
- [ ] GPU drivers installed (if using GPU)

After deploying:

- [ ] All services running: `docker-compose ps`
- [ ] Backend healthy: `curl http://localhost:2323/api/health`
- [ ] Frontend accessible: http://localhost:2000
- [ ] Voice mode works
- [ ] Logs look normal

---

**Status:** Production Ready 🚀

**Last Updated:** 2026-02-04

**Version:** 2.0.0 - Full Docker Support
