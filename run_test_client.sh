#!/bin/bash
# Test ClarityMentor FastAPI Backend WebSocket client

set -e

cd "$(dirname "$0")"

echo "========================================================================="
echo "ClarityMentor FastAPI Backend - WebSocket Test Client"
echo "========================================================================="
echo ""
echo "Connecting to: ws://localhost:2323/ws/voice"
echo ""

./venv/bin/python backend/test_client.py "$@"
