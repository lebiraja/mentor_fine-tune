# ClarityMentor Docker Setup Guide

This guide helps you run the ClarityMentor application using Docker and Docker Compose.

## Architecture

The Docker setup consists of three services:

1. **Backend (FastAPI)** - Port 2323
   - FastAPI server with WebSocket support
   - Voice processing, emotion detection, LLM inference
   - Runs on `http://localhost:2323`

2. **Frontend (Web UI)** - Port 2000
   - Static HTML/CSS/JavaScript interface
   - Serves sample-ui files
   - Runs on `http://localhost:2000`

3. **Cache (Redis)** - Port 2999
   - Optional Redis cache for sessions/caching
   - Can be used for distributed caching

## Prerequisites

- Docker >= 20.10
- Docker Compose >= 2.0
- At least 8GB RAM available for ML models
- GPU (optional but recommended for better performance)

## Quick Start

### 1. Build the Docker Images

```bash
docker-compose build
```

### 2. Start All Services

```bash
docker-compose up -d
```

Services will start in the following order:
- Redis cache starts first
- Backend service starts and waits for models to load
- Frontend service starts after backend is healthy

### 3. Verify Services are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                      STATUS              PORTS
claritymentor-backend    Up (healthy)        0.0.0.0:2323->2323/tcp
claritymentor-frontend   Up                  0.0.0.0:2000->2000/tcp
claritymentor-cache      Up (healthy)        0.0.0.0:2999->6379/tcp
```

## Accessing Services

- **Backend API**: http://localhost:2323
- **Frontend UI**: http://localhost:2000
- **Backend Health Check**: http://localhost:2323/api/health
- **Redis CLI**: `docker exec -it claritymentor-cache redis-cli`

## Useful Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f cache
```

### Stop Services

```bash
docker-compose stop
```

### Restart Services

```bash
docker-compose restart
```

### Remove All Containers and Volumes

```bash
docker-compose down -v
```

### Rebuild After Code Changes

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Model Files

Models are stored in `/app/models` inside the container and mounted from `./models` on the host. This allows:

- Models persist between container restarts
- Easy model updates/swaps
- Model sharing between services

### Loading Large Models

If you have large model files, they will be copied during the Docker build process. This may take time on first build.

## Environment Variables

Edit the `environment` section in `docker-compose.yml`:

```yaml
backend:
  environment:
    - HOST=0.0.0.0
    - PORT=2323
    - DEBUG=False
    - PYTHONUNBUFFERED=1
```

## Networking

All services communicate through a Docker bridge network called `claritymentor-network`.

From backend, you can reach:
- Frontend on `http://frontend:2000`
- Redis on `cache:6379`

From frontend, you can reach backend on `http://backend:2323`

## GPU Support (Optional)

To enable GPU support, add the following to the backend service in `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Requirements:
- NVIDIA Docker runtime installed
- NVIDIA GPU drivers on host

## Troubleshooting

### Backend Won't Start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Not enough RAM for models
- Missing model files
- Port 2323 already in use

### Frontend Can't Connect to Backend

Ensure backend is healthy:
```bash
docker-compose logs backend
curl http://localhost:2323/api/health
```

### High Memory Usage

The ML models require significant memory. Monitor with:
```bash
docker stats
```

### Models Not Loading

Verify models are mounted:
```bash
docker exec claritymentor-backend ls -la /app/models/
```

## Production Deployment

For production:

1. Set `DEBUG=False` in environment variables
2. Use a reverse proxy (Nginx) in front of services
3. Configure proper logging
4. Use environment files for secrets
5. Consider using managed databases instead of Redis
6. Enable resource limits in docker-compose.yml
7. Set up monitoring and health checks

Example production deployment (add to docker-compose.yml):

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 8G
      reservations:
        cpus: '1'
        memory: 4G
```

## Development Mode

For development, use:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

To create `docker-compose.dev.yml`:

```yaml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=True
    volumes:
      - ./backend:/app/backend
      - ./config:/app/config
```

## Data Persistence

Volumes configured:
- `./models` - Model files
- `./data` - Data files
- `./config` - Configuration files
- `./logs` - Application logs
- `redis-data` - Redis persistence

## Updating Code

After code changes:

```bash
docker-compose build --no-cache
docker-compose up -d
```

Or for development with hot reload:

```bash
docker-compose exec backend bash
# Make changes in mounted volumes, they'll auto-reload if DEBUG=True
```

## Next Steps

1. Check logs: `docker-compose logs -f`
2. Test backend: `curl http://localhost:2323/api/health`
3. Open frontend: http://localhost:2000
4. Check the README.md files in respective directories for more details
