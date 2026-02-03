# Getting Started with ClarityMentor Docker

## What Was Created

Your project has been fully dockerized! Here's what was set up:

### Docker Files Created

```
.dockerignore                    # Files to exclude from Docker build
.env.example                     # Example environment variables
Dockerfile.backend               # Backend service Docker image
Dockerfile.frontend              # Frontend service Docker image
docker-compose.yml               # Main Docker Compose configuration
docker-compose.dev.yml           # Development overrides (hot-reload)
docker-entrypoint.sh             # Backend startup script
docker.sh                        # Helper script for Docker operations
DOCKER_SETUP.md                  # Detailed Docker documentation
DOCKER_QUICK_REFERENCE.md        # Quick reference guide
```

### Services Configuration

| Service | Port | Purpose |
|---------|------|---------|
| Backend (FastAPI) | 2323 | Main API with WebSocket support for voice |
| Frontend (Web UI) | 2000 | HTML/CSS/JavaScript sample interface |
| Cache (Redis) | 2999 | Caching and session management |

## Quick Start

### Step 1: Build Docker Images

```bash
cd /home/lebi/projects/mentor
./docker.sh build
```

This will:
- Build the backend image with all Python dependencies
- Build the frontend image with HTTP server
- Include all model files in the backend image

### Step 2: Start Services

```bash
./docker.sh up
```

Services will start in order:
1. Redis Cache (2999) - Starts first
2. Backend (2323) - Loads models and initializes services
3. Frontend (2000) - Waits for backend to be healthy, then starts

### Step 3: Verify Everything Works

```bash
./docker.sh health
```

Or manually:
```bash
# Check frontend
curl http://localhost:2000

# Check backend
curl http://localhost:2323/api/health

# Check cache
docker exec claritymentor-cache redis-cli ping
```

### Step 4: Access Services

- **Frontend UI**: http://localhost:2000
- **Backend API**: http://localhost:2323
- **API Documentation**: http://localhost:2323/docs
- **Redis CLI**: `./docker.sh exec-cache`

## How the Docker Setup Works

### Model Files

Model files are:
- **Copied** into the Docker image during build
- **Also mounted** from `./models` directory for easy updates
- **Persistent** across container restarts

### Configuration Files

Configuration files in `./config/` are:
- **Mounted** as volumes (not copied)
- **Hot-editable** - changes take effect immediately
- **Shared** with the container at `/app/config`

### Frontend Assets

Frontend files from `./sample-ui/` are:
- **Mounted** as volumes for development
- **Served** by Node.js http-server on port 2000
- **Auto-reload** when files change

## Helper Script: `./docker.sh`

Instead of typing long docker-compose commands, use the helper:

```bash
# Build
./docker.sh build

# Start
./docker.sh up

# Stop
./docker.sh down

# View logs
./docker.sh logs
./docker.sh logs-backend

# Check status
./docker.sh status
./docker.sh health

# Access containers
./docker.sh exec-backend
./docker.sh exec-frontend
./docker.sh exec-cache

# Development mode with hot-reload
./docker.sh dev

# Clean up
./docker.sh clean
```

Run `./docker.sh help` for all available commands.

## Directory Structure

```
mentor/
├── backend/                      # FastAPI backend source code
├── sample-ui/                    # Frontend HTML/CSS/JS
├── models/                       # ML models (mounted in container)
├── config/                       # Configuration files (mounted in container)
├── data/                         # Data directory (mounted in container)
├── logs/                         # Application logs (created by container)
│
├── Dockerfile.backend            # Backend image definition
├── Dockerfile.frontend           # Frontend image definition
├── docker-compose.yml            # Main Docker Compose config
├── docker-compose.dev.yml        # Development overrides
├── docker-entrypoint.sh          # Backend startup script
├── docker.sh                     # Helper script
├── .dockerignore                 # Files to exclude from build
└── .env.example                  # Example environment variables
```

## Common Workflows

### Development (with hot-reload)

```bash
# Start with auto-reload for backend code
./docker.sh dev

# Make changes to backend code in ./backend/
# Changes are auto-reload thanks to Uvicorn reload mode

# View logs
./docker.sh logs
```

### Production

```bash
# Start normally (DEBUG=False)
./docker.sh up

# View logs
./docker.sh logs
```

### Debugging

```bash
# View real-time logs
./docker.sh logs -f

# Access backend container
./docker.sh exec-backend bash

# Run commands in backend
docker exec -it claritymentor-backend python -c "print('hello')"

# View redis data
./docker.sh exec-cache
# Commands: KEYS *, GET key_name, etc.
```

### After Making Code Changes

```bash
# If you modified backend code
docker-compose up -d  # Hot-reload will handle it if using ./docker.sh dev

# If you modified requirements.txt
./docker.sh build
./docker.sh up

# If you modified frontend
./docker.sh up  # It's already mounted as volume

# If you modified config files
# Changes are immediate (configs are mounted)
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
./docker.sh logs

# View specific service logs
./docker.sh logs-backend
./docker.sh logs-frontend

# Check if ports are available
sudo lsof -i :2323  # Backend
sudo lsof -i :2000  # Frontend
sudo lsof -i :2999  # Cache
```

### Models Not Loading

```bash
# Verify models are in place
ls -la models/

# Check container's models directory
docker exec claritymentor-backend ls -la /app/models/

# View backend logs for errors
./docker.sh logs-backend
```

### Memory Issues

```bash
# Check resource usage
docker stats

# Increase Docker's memory limit (in Docker Desktop preferences)
```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :2323

# Either stop that process or change port in docker-compose.yml
```

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env with your settings
```

Or edit directly in `docker-compose.yml`:

```yaml
backend:
  environment:
    - HOST=0.0.0.0
    - PORT=2323
    - DEBUG=False
```

## Next Steps

1. **Build and start**: `./docker.sh build && ./docker.sh up`
2. **Check health**: `./docker.sh health`
3. **Open frontend**: http://localhost:2000
4. **View API docs**: http://localhost:2323/docs
5. **Read full guide**: `DOCKER_SETUP.md`

## Need Help?

- **Quick reference**: See `DOCKER_QUICK_REFERENCE.md`
- **Detailed guide**: See `DOCKER_SETUP.md`
- **Script help**: Run `./docker.sh help`
- **View logs**: Run `./docker.sh logs`

## Summary

✅ **Backend Dockerized** - FastAPI with all dependencies
✅ **Frontend Dockerized** - Static web server for sample-ui
✅ **Cache Dockerized** - Redis for caching/sessions
✅ **Models Included** - Copied into images from ./models
✅ **Config Mounted** - Hot-editable configuration files
✅ **Helper Script** - Easy `./docker.sh` commands
✅ **Documentation** - Comprehensive guides included
✅ **Ports Configured** - 2323 (backend), 2000 (frontend), 2999 (cache)

**Ready to start? Run: `./docker.sh build && ./docker.sh up`**

---

For detailed information, see the other documentation files:
- `DOCKER_SETUP.md` - Comprehensive setup guide
- `DOCKER_QUICK_REFERENCE.md` - Quick command reference
