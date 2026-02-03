# ClarityMentor Docker - Quick Reference

## One-Line Start

```bash
./docker.sh build && ./docker.sh up
```

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 2000 | http://localhost:2000 |
| Backend | 2323 | http://localhost:2323 |
| Backend Docs | 2323 | http://localhost:2323/docs |
| Backend Health | 2323 | http://localhost:2323/api/health |
| Redis Cache | 2999 | localhost:2999 |

## Common Tasks

### Start Everything
```bash
./docker.sh up
```

### View Logs
```bash
./docker.sh logs              # All services
./docker.sh logs-backend      # Backend only
./docker.sh logs-frontend     # Frontend only
```

### Stop Everything
```bash
./docker.sh down
```

### Restart Services
```bash
./docker.sh restart
```

### Check Health
```bash
./docker.sh health
```

### Access Containers
```bash
./docker.sh exec-backend      # Bash shell in backend
./docker.sh exec-frontend     # Bash shell in frontend
./docker.sh exec-cache        # redis-cli in cache
```

### Development Mode (Hot-Reload)
```bash
./docker.sh dev
```
Backend code changes will automatically reload.

### Clean Up
```bash
./docker.sh clean             # Remove containers/volumes
./docker.sh clean-all         # Remove containers/volumes/images
```

## Manual Docker Commands

### Using docker-compose directly

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View running services
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose stop

# Stop and remove
docker-compose down

# Stop, remove, and delete volumes
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache
```

## Troubleshooting

### Check if services are running
```bash
./docker.sh status
```

### Check service health
```bash
./docker.sh health
```

### View backend logs
```bash
./docker.sh logs-backend
```

### Backend fails to start?
```bash
# Check full logs
./docker.sh logs-backend

# Common causes:
# - Port 2323 already in use: sudo lsof -i :2323
# - Not enough RAM: Check docker stats
# - Models not loaded: Check ./models directory exists
```

### Redis not connecting?
```bash
# Test redis connection
./docker.sh exec-cache
> ping
PONG
```

### High memory usage?
```bash
# Monitor resource usage
docker stats
```

## Development Workflow

1. Make code changes in `./backend` or `./sample-ui`
2. For backend hot-reload: `./docker.sh dev`
3. For frontend: Changes are live (served from mounted volume)
4. View logs: `./docker.sh logs`

## Docker Compose Files

- **docker-compose.yml** - Main production configuration
- **docker-compose.dev.yml** - Development overrides (hot-reload)
- **.dockerignore** - Files to exclude from Docker build
- **Dockerfile.backend** - Backend image definition
- **Dockerfile.frontend** - Frontend image definition

## Environment Variables

Edit environment in `docker-compose.yml` or create `.env` file:

```yaml
backend:
  environment:
    - HOST=0.0.0.0
    - PORT=2323
    - DEBUG=False
```

## Network Communication (Inside Docker)

Services can reach each other by service name:

- Backend → Redis: `cache:6379`
- Frontend → Backend: `http://backend:2323`
- Backend → Frontend: `http://frontend:2000`

## Volumes

Models and config are shared between host and container:

```yaml
volumes:
  - ./models:/app/models          # Model files
  - ./config:/app/config           # Config files
  - ./data:/app/data               # Data directory
  - ./logs:/app/logs               # Log files
  - redis-data:/data               # Redis persistence
```

## Performance Tips

1. **Increase Docker memory** if models are slow
2. **Use GPU**: Add nvidia runtime to docker-compose.yml
3. **Hot-reload development**: Use `./docker.sh dev`
4. **Reduce rebuild time**: Don't rebuild if only config changed

## Next Steps

1. Start services: `./docker.sh up`
2. Open frontend: http://localhost:2000
3. Check logs: `./docker.sh logs`
4. See full guide: Read DOCKER_SETUP.md

---

For detailed guide, see: **DOCKER_SETUP.md**
