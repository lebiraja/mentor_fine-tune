#!/bin/bash
# Start ClarityMentor FastAPI Backend on port 2323

set -e

cd "$(dirname "$0")"

echo "========================================================================="
echo "Starting ClarityMentor FastAPI Backend"
echo "========================================================================="
echo ""
echo "Port: 2323"
echo "WebSocket: ws://localhost:2323/ws/voice"
echo "REST API: http://localhost:2323/api/*"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================================================="
echo ""

./venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 2323 --ws-max-size 10485760
