#!/bin/bash
# ClarityMentor - Complete Deployment Commands
# Run this script to build and start everything

echo "========================================================================="
echo "🚀 ClarityMentor Docker Deployment"
echo "========================================================================="
echo ""

# Step 1: Verify model files exist
echo "Step 1: Verifying model files..."
if [ ! -d "models/claritymentor-lora/final" ]; then
    echo "❌ ERROR: Model files not found!"
    echo "Expected path: ./models/claritymentor-lora/final/"
    echo ""
    echo "Please ensure your model files are in:"
    echo "  models/claritymentor-lora/final/"
    echo "    ├── adapter_model.safetensors"
    echo "    ├── tokenizer.json"
    echo "    ├── vocab.json"
    echo "    └── ..."
    exit 1
fi
echo "✅ Model files found"
echo ""

# Step 2: Create required directories
echo "Step 2: Creating required directories..."
mkdir -p logs data
echo "✅ Directories created"
echo ""

# Step 3: Check if .env exists
echo "Step 3: Checking environment file..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from template..."
    cat > .env << 'EOF'
# ClarityMentor Environment Configuration

# Backend Settings
HOST=0.0.0.0
PORT=2323
DEBUG=False
PYTHONUNBUFFERED=1

# Model Path (inside container)
MODEL_PATH=/app/models/claritymentor-lora/final

# Redis Configuration
REDIS_HOST=cache
REDIS_PORT=6379
REDIS_DB=0

# Voice Configuration
SAMPLE_RATE=16000
CHUNK_SIZE=1024

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/claritymentor.log
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi
echo ""

# Step 4: Choose GPU or CPU mode
echo "Step 4: Select deployment mode"
echo "========================================================================="
echo "1) GPU mode (Recommended - requires NVIDIA GPU)"
echo "2) CPU only mode (Works everywhere, slower inference)"
echo ""
read -p "Enter choice [1 or 2]: " mode_choice
echo ""

if [ "$mode_choice" = "1" ]; then
    COMPOSE_FILE="docker-compose.yml"
    echo "✅ Using GPU mode"
    echo ""
    echo "Checking GPU availability..."
    if ! command -v nvidia-smi &> /dev/null; then
        echo "⚠️  WARNING: nvidia-smi not found"
        echo "   GPU may not be available, but continuing anyway..."
        echo "   Backend will fall back to CPU if needed"
    else
        echo "✅ NVIDIA drivers found"
        nvidia-smi --query-gpu=name --format=csv,noheader
    fi
elif [ "$mode_choice" = "2" ]; then
    COMPOSE_FILE="docker-compose.cpu.yml"
    echo "✅ Using CPU-only mode"
else
    echo "❌ Invalid choice"
    exit 1
fi
echo ""

# Step 5: Stop any existing containers
echo "Step 5: Stopping any existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.cpu.yml down 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Step 6: Build images
echo "Step 6: Building Docker images..."
echo "This may take 5-10 minutes on first run..."
echo ""
docker-compose -f $COMPOSE_FILE build
if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi
echo ""
echo "✅ Images built successfully"
echo ""

# Step 7: Start services
echo "Step 7: Starting services..."
docker-compose -f $COMPOSE_FILE up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start services!"
    exit 1
fi
echo "✅ Services started"
echo ""

# Step 8: Wait for backend (models loading)
echo "Step 8: Waiting for backend to load models..."
echo "This typically takes 2-3 minutes..."
echo ""

COUNTER=0
MAX_ATTEMPTS=60

while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
    if curl -sf http://localhost:2323/api/health > /dev/null 2>&1; then
        echo ""
        echo "✅ Backend is ready!"
        break
    fi
    printf "."
    sleep 3
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_ATTEMPTS ]; then
    echo ""
    echo "⚠️  Backend taking longer than expected"
    echo "Check logs: docker-compose logs backend"
else
    echo ""
fi

# Step 9: Wait for frontend
echo ""
echo "Step 9: Checking frontend..."
sleep 5
if curl -sf http://localhost:2000/ > /dev/null 2>&1; then
    echo "✅ Frontend is ready!"
else
    echo "⚠️  Frontend not responding yet"
    echo "Check logs: docker-compose logs frontend"
fi

# Step 10: Show status
echo ""
echo "========================================================================="
echo "🎉 Deployment Complete!"
echo "========================================================================="
echo ""

# Show container status
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "========================================================================="
echo "📍 Access Points"
echo "========================================================================="
echo ""
echo "🌐 Frontend:     http://localhost:2000"
echo "🔌 Backend API:  http://localhost:2323"
echo "📊 Health Check: http://localhost:2323/api/health"
echo "💾 Redis:        localhost:2999"
echo ""

echo "========================================================================="
echo "📂 Volume Mounts (Model Files)"
echo "========================================================================="
echo ""
echo "Host → Container:"
echo "  ./models/claritymentor-lora/final → /app/models/claritymentor-lora/final (read-only)"
echo "  ./config → /app/config (read-only)"
echo "  ./data → /app/data (read-write)"
echo "  ./logs → /app/logs (read-write)"
echo ""

echo "========================================================================="
echo "🛠️  Useful Commands"
echo "========================================================================="
echo ""
echo "View logs (all):      docker-compose -f $COMPOSE_FILE logs -f"
echo "View logs (backend):  docker-compose -f $COMPOSE_FILE logs -f backend"
echo "View logs (frontend): docker-compose -f $COMPOSE_FILE logs -f frontend"
echo ""
echo "Stop services:        docker-compose -f $COMPOSE_FILE down"
echo "Restart backend:      docker-compose -f $COMPOSE_FILE restart backend"
echo "Check status:         docker-compose -f $COMPOSE_FILE ps"
echo ""
echo "Enter backend:        docker-compose -f $COMPOSE_FILE exec backend bash"
echo "Check models:         docker-compose -f $COMPOSE_FILE exec backend ls -la /app/models/claritymentor-lora/final/"
echo ""

echo "========================================================================="
echo "✅ Ready to use!"
echo "========================================================================="
echo ""
echo "Open http://localhost:2000 in your browser and start chatting!"
echo ""
