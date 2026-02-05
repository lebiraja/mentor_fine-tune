# 🚀 QUICK START - Speed up Build

## Current Status
If `docker-compose build` is taking >30 min, here's why and what to do:

### Why So Slow?
- **Backend**: Installing ML packages (torch, transformers, etc.) = 20-40 min
- **Frontend**: npm install + build = 5-10 min
- **Total First Build**: 30-50 minutes (NORMAL)

### ✅ What To Do NOW

#### Option 1: LET IT FINISH (Recommended)
```bash
# Check what's happening
docker-compose build --progress=plain

# It will finish eventually!
# Next builds will be MUCH faster (cached)
```

#### Option 2: BUILD ONLY FRONTEND FIRST (2 minutes)
```bash
# Cancel current build (Ctrl+C)

# Build only frontend
docker-compose build frontend

# Start frontend + use existing backend
docker-compose up -d frontend cache
```

#### Option 3: SKIP BUILD - Use Simple Python Server
```bash
# Cancel Docker build (Ctrl+C)

# Run backend directly (no Docker)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_backend.txt
python main.py

# In another terminal - run frontend
cd frontend
npm install
npm run dev
```

### ⚡ SPEED UP FUTURE BUILDS

Add to `.dockerignore`:
```
__pycache__
*.pyc
*.pyo
.pytest_cache
.coverage
*.egg-info
dist/
build/
node_modules/
venv/
*.log
```

## 🎯 Recommended: Just Wait!
- First build: 30-50 min ⏱️
- Second build: 2-5 min ⚡ (cached!)
- Model loading: 2-3 min 🧠

**Models mount automatically** - no extra commands needed!
