#!/bin/bash

# Run ClarityMentor Voice System

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "================================================"
echo "ClarityMentor - Voice-to-Voice with Emotion"
echo "================================================"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

echo "Python version:"
python --version
echo ""

# Check if voice dependencies are installed
echo "Checking dependencies..."
python -c "import sounddevice; import torch; import transformers" 2>/dev/null || {
    echo "Warning: Some dependencies may not be installed"
    echo "Run: pip install -r requirements_voice.txt"
    echo ""
}

# Check GPU
echo "GPU availability:"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    python -c "import torch; print(f'Device: {torch.cuda.get_device_name(0)}')"
    python -c "import torch; mem = torch.cuda.get_device_properties(0).total_memory / 1024**3; print(f'Memory: {mem:.1f}GB')"
else
    echo "Warning: CUDA not available - will use CPU (very slow)"
fi
echo ""

# Run voice inference
echo "Starting voice pipeline..."
echo "Press Ctrl+C to exit"
echo ""

python scripts/voice_inference.py "$@"
