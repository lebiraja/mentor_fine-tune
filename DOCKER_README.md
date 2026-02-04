# 🐳 Docker Quick Start - 60 Seconds

## One-Command Deployment

```bash
./docker-start.sh
```

That's it! The script will:
1. ✅ Check prerequisites
2. ✅ Ask GPU or CPU mode
3. ✅ Build images
4. ✅ Start all services
5. ✅ Wait for health checks
6. ✅ Show access URLs

**Access:** http://localhost:2000 (Frontend) | http://localhost:2323 (Backend)

---

## Manual Deployment

### GPU Mode (Recommended)

```bash
docker-compose up -d
```

### CPU Mode

```bash
docker-compose -f docker-compose.cpu.yml up -d
```

### Check Status

```bash
docker-compose ps
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

---

## What's Included

### Services
- **Frontend (Port 2000)** - React + Nginx
- **Backend (Port 2323)** - FastAPI + ML models
- **Redis (Port 2999)** - Cache (optional)

### Volumes Mounted
- **Models:** `./models/claritymentor-lora/final` → `/app/models/...`
- **Config:** `./config` → `/app/config`
- **Data:** `./data` → `/app/data`
- **Logs:** `./logs` → `/app/logs`

---

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM
- 20GB disk space
- GPU (optional, for faster inference)

---

## Troubleshooting

### Backend won't start
```bash
# Check if model files exist
ls -la models/claritymentor-lora/final/

# View logs
docker-compose logs backend
```

### Port conflict
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:2000"  # Frontend
  - "8081:2323"  # Backend
```

### GPU not working
```bash
# Use CPU version
docker-compose -f docker-compose.cpu.yml up -d
```

---

## Commands Cheat Sheet

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f backend

# Rebuild
docker-compose build --no-cache

# Enter container
docker-compose exec backend bash

# Check resources
docker stats

# Clean up
docker-compose down -v
docker system prune -a
```

---

## Documentation

- **DOCKER_COMPLETE_GUIDE.md** - Full deployment guide (12KB)
- **DOCKER_DEPLOYMENT_SUMMARY.md** - What was done (15KB)
- **docker-compose.yml** - GPU configuration
- **docker-compose.cpu.yml** - CPU-only configuration

---

## Next Steps

1. ✅ Deploy: `./docker-start.sh`
2. ✅ Open: http://localhost:2000
3. ✅ Test text chat
4. ✅ Test voice mode
5. ✅ Check logs: `docker-compose logs -f`

---

**Status:** Production Ready 🚀

**Version:** 2.0.0

**Last Updated:** 2026-02-04
