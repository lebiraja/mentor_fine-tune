#!/bin/bash
# ClarityMentor Docker Quick Start Script

set -e

echo "========================================================================="
echo "ClarityMentor Docker Deployment"
echo "========================================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker found: $(docker --version)"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker Compose found: $(docker-compose --version)"

# Check if model files exist
if [ ! -d "models/claritymentor-lora/final" ]; then
    echo -e "${RED}✗ Model files not found${NC}"
    echo "Please ensure models are in: ./models/claritymentor-lora/final/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Model files found"

# Check if config files exist
if [ ! -d "config" ]; then
    echo -e "${RED}✗ Config directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Config files found"

# Create required directories
mkdir -p logs data

echo ""
echo "========================================================================="
echo "Select deployment mode:"
echo "========================================================================="
echo "1) GPU (Recommended - requires NVIDIA GPU)"
echo "2) CPU only (Slower but works everywhere)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        COMPOSE_FILE="docker-compose.yml"
        echo -e "${GREEN}Using GPU mode${NC}"
        
        # Check for NVIDIA Docker
        if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            echo -e "${YELLOW}⚠ Warning: GPU not accessible${NC}"
            echo "Continuing anyway - backend will use CPU"
        else
            echo -e "${GREEN}✓${NC} GPU is accessible"
        fi
        ;;
    2)
        COMPOSE_FILE="docker-compose.cpu.yml"
        echo -e "${GREEN}Using CPU-only mode${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================================================="
echo "Building Docker images..."
echo "========================================================================="
echo ""

docker-compose -f $COMPOSE_FILE build

echo ""
echo "========================================================================="
echo "Starting services..."
echo "========================================================================="
echo ""

docker-compose -f $COMPOSE_FILE up -d

echo ""
echo "========================================================================="
echo "Waiting for services to start..."
echo "========================================================================="
echo ""

# Wait for backend health check
echo "Waiting for backend (this may take 2-3 minutes for model loading)..."
COUNTER=0
MAX_ATTEMPTS=60

while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:2323/api/health &> /dev/null; then
        echo -e "${GREEN}✓${NC} Backend is ready!"
        break
    fi
    echo -n "."
    sleep 5
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗ Backend failed to start${NC}"
    echo "Check logs: docker-compose logs backend"
    exit 1
fi

# Wait for frontend
echo "Waiting for frontend..."
sleep 5

if curl -f http://localhost:2000/ &> /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend is ready!"
else
    echo -e "${YELLOW}⚠ Frontend may not be ready yet${NC}"
    echo "Check logs: docker-compose logs frontend"
fi

echo ""
echo "========================================================================="
echo "✅ ClarityMentor is ready!"
echo "========================================================================="
echo ""
echo "🌐 Frontend:  http://localhost:2000"
echo "🔌 Backend:   http://localhost:2323"
echo "📊 Health:    http://localhost:2323/api/health"
echo "💾 Redis:     localhost:2999"
echo ""
echo "Commands:"
echo "  - View logs:      docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Stop services:  docker-compose -f $COMPOSE_FILE down"
echo "  - Restart:        docker-compose -f $COMPOSE_FILE restart"
echo ""
echo "========================================================================="
