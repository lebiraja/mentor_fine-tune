#!/bin/bash
set -e

# Docker entrypoint for the backend service
# This script ensures the application starts correctly with all required paths

echo "=========================================="
echo "ClarityMentor Backend - Docker Startup"
echo "=========================================="

# Set default values
export PYTHONUNBUFFERED=1
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-2323}
export DEBUG=${DEBUG:-False}

echo "Starting FastAPI application..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Debug: $DEBUG"
echo ""

# Start the application
exec python -m uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    $([ "$DEBUG" = "True" ] && echo "--reload" || echo "")
