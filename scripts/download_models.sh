#!/usr/bin/env bash
# One-time model download for ClarityMentor v3. Everything lands in ./models/.
# After this completes, the app needs zero network access (except Whisper's first-run auto-download).
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p models/llm models/kokoro models/silero models/piper-tamil

echo "==> [1/4] LLM: Qwen3-4B-Instruct-2507 Q4_K_M (~2.5 GB)"
if [ ! -f models/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf ]; then
    hf download unsloth/Qwen3-4B-Instruct-2507-GGUF \
        Qwen3-4B-Instruct-2507-Q4_K_M.gguf \
        --local-dir models/llm
else
    echo "    already present, skipping"
fi

echo "==> [2/4] TTS English: Kokoro-82M ONNX + voices (~410 MB)"
KOKORO_BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
[ -f models/kokoro/kokoro-v1.0.onnx ] || curl -L --fail -o models/kokoro/kokoro-v1.0.onnx "$KOKORO_BASE/kokoro-v1.0.onnx"
[ -f models/kokoro/voices-v1.0.bin ]  || curl -L --fail -o models/kokoro/voices-v1.0.bin  "$KOKORO_BASE/voices-v1.0.bin"

echo "==> [3/4] TTS Tamil: Piper ta_IN-female-medium (~60 MB)"
PIPER_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/ta/ta_IN/female/medium"
[ -f models/piper-tamil/ta_IN-female-medium.onnx ] || \
    curl -L --fail -o models/piper-tamil/ta_IN-female-medium.onnx "$PIPER_BASE/ta_IN-female-medium.onnx"
[ -f models/piper-tamil/ta_IN-female-medium.onnx.json ] || \
    curl -L --fail -o models/piper-tamil/ta_IN-female-medium.onnx.json "$PIPER_BASE/ta_IN-female-medium.onnx.json"

echo "==> [4/4] VAD: Silero v5 ONNX (~2 MB)"
[ -f models/silero/silero_vad.onnx ] || curl -L --fail -o models/silero/silero_vad.onnx \
    "https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx"

echo
echo "NOTE: STT (Whisper large-v3-turbo) auto-downloads on first run via HuggingFace cache (~1.5 GB)."
echo
echo "All models downloaded:"
du -sh models/*
