# 🐳 Docker Commands Cheatsheet - ClarityMentor

Quick reference for your daily Docker workflow.

---

## 🚀 Start/Stop Services

```bash
# Production (GPU) - Standard mode
docker-compose up -d

# Development (Hot Reload) - NO REBUILDS NEEDED! ⭐
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# CPU Only (No GPU)
docker-compose -f docker-compose.cpu.yml up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 🔄 Rebuild Containers

```bash
# First time build (all services)
docker-compose build --parallel

# Rebuild everything (fresh)
docker-compose build --no-cache

# Rebuild only backend
docker-compose build backend

# Rebuild only frontend
docker-compose build frontend

# Rebuild and restart specific service
docker-compose build backend && docker-compose up -d backend
```

---

## 📊 Monitor & Debug

```bash
# Check service status
docker-compose ps

# View all logs (live)
docker-compose logs -f

# View backend logs
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# Check resource usage
docker stats

# Check disk usage
docker system df
```

---

## 🔍 Inspect & Debug

```bash
# Shell into backend container
docker-compose exec backend bash

# Shell into frontend container
docker-compose exec frontend sh

# Check GPU in backend
docker-compose exec backend nvidia-smi

# Test backend API
docker-compose exec backend curl http://localhost:2323/api/health

# Check Python in backend
docker-compose exec backend python --version

# List running processes in backend
docker-compose exec backend ps aux
```

---

## 🔧 Service Management

```bash
# Restart single service (no rebuild)
docker-compose restart backend

# Restart all services
docker-compose restart

# Stop single service
docker-compose stop backend

# Start single service
docker-compose start backend

# View service configuration
docker-compose config

# Validate compose file
docker-compose config --quiet
```

---

## 🧹 Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all

# Prune all unused Docker data
docker system prune -a

# Remove dangling images
docker image prune

# Remove unused volumes
docker volume prune
```

---

## 🔬 Health Checks

```bash
# Check backend health
curl http://localhost:2323/api/health

# Check frontend
curl http://localhost:2000

# Check Redis
docker-compose exec cache redis-cli ping

# Detailed health status
docker inspect claritymentor-backend | grep -A 10 Health
```

---

## 📦 Image Management

```bash
# List Docker images
docker images

# List ClarityMentor images
docker images | grep claritymentor

# Remove specific image
docker rmi mentor-backend

# Pull base images
docker pull nvidia/cuda:12.1.0-devel-ubuntu22.04
docker pull node:20-alpine
docker pull nginx:alpine
```

---

## 🌐 Network Management

```bash
# List networks
docker network ls

# Inspect ClarityMentor network
docker network inspect mentor_claritymentor-network

# Test connectivity between services
docker-compose exec frontend ping backend
docker-compose exec backend ping cache
```

---

## 📝 Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect mentor_redis-data

# Backup volume data
docker run --rm -v mentor_redis-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Restore volume data
docker run --rm -v mentor_redis-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

---

## 🐛 Troubleshooting

```bash
# View container details
docker inspect claritymentor-backend

# Check environment variables
docker-compose exec backend env

# Check disk space in container
docker-compose exec backend df -h

# Check container logs from start
docker-compose logs --no-log-prefix backend

# Follow logs with timestamps
docker-compose logs -f -t backend

# Export logs to file
docker-compose logs --no-log-prefix backend > backend.log
```

---

## ⚡ Development Workflow

```bash
# Morning: Start dev mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Watch logs
docker-compose logs -f backend

# Edit code - auto reloads! ✨
# - backend/*.py → Backend reloads automatically
# - frontend/src/* → Frontend needs rebuild

# Evening: Stop
docker-compose down
```

---

## 🚨 Emergency Commands

```bash
# Kill all containers immediately
docker kill $(docker ps -q)

# Stop specific container by name
docker stop claritymentor-backend

# Force remove all ClarityMentor containers
docker rm -f $(docker ps -aq --filter name=claritymentor)

# Check if ports are in use
sudo lsof -i :2323  # Backend
sudo lsof -i :2000  # Frontend
sudo lsof -i :2999  # Redis

# Restart Docker daemon (if needed)
sudo systemctl restart docker
```

---

## 🔐 Security Checks

```bash
# Scan image for vulnerabilities (if installed)
docker scan mentor-backend

# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View container resource limits
docker stats --no-stream

# Check exposed ports
docker port claritymentor-backend
```

---

## 💡 Pro Tips

### Enable BuildKit (Faster Builds)
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Aliases for Quick Access
```bash
# Add to ~/.bashrc or ~/.zshrc
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'
alias dcps='docker-compose ps'
alias dcexec='docker-compose exec'

# Development mode
alias dcdev='docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d'
```

### Watch Mode for Logs
```bash
# Install watch if not available
sudo apt install watch  # Ubuntu/Debian
brew install watch      # macOS

# Watch container status
watch -n 1 'docker-compose ps'
```

---

## 📌 Common Issues & Solutions

### Issue: Port already in use
```bash
# Find process using port
sudo lsof -i :2323
# Kill process
sudo kill -9 <PID>
```

### Issue: GPU not detected
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
# Reinstall NVIDIA Container Toolkit if needed
```

### Issue: Out of disk space
```bash
# Clean up everything
docker system prune -a --volumes
# Check space
docker system df
```

### Issue: Container won't start
```bash
# Check logs
docker-compose logs backend
# Check events
docker events
```

---

**Remember**: With dev mode, you rarely need to rebuild! 🚀

Just start once and edit code freely - changes apply automatically!
