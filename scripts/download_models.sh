#!/usr/bin/env bash
# One-time model download for ClarityMentor v2. Everything lands in ./models/.
# After this completes, the app needs zero network access.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p models/llm models/parakeet-v3 models/kokoro models/silero

echo "==> [1/4] LLM: Qwen3-4B-Instruct-2507 Q4_K_M (~2.5 GB)"
if [ ! -f models/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf ]; then
    hf download unsloth/Qwen3-4B-Instruct-2507-GGUF \
        Qwen3-4B-Instruct-2507-Q4_K_M.gguf \
        --local-dir models/llm
else
    echo "    already present, skipping"
fi

echo "==> [2/4] STT: Parakeet TDT 0.6B v3 int8 ONNX (~670 MB)"
hf download istupakov/parakeet-tdt-0.6b-v3-onnx \
    config.json vocab.txt nemo128.onnx \
    encoder-model.int8.onnx decoder_joint-model.int8.onnx \
    --local-dir models/parakeet-v3

echo "==> [3/4] TTS: Kokoro-82M ONNX + voices (~410 MB)"
KOKORO_BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
[ -f models/kokoro/kokoro-v1.0.onnx ] || curl -L --fail -o models/kokoro/kokoro-v1.0.onnx "$KOKORO_BASE/kokoro-v1.0.onnx"
[ -f models/kokoro/voices-v1.0.bin ]  || curl -L --fail -o models/kokoro/voices-v1.0.bin  "$KOKORO_BASE/voices-v1.0.bin"

echo "==> [4/4] VAD: Silero v5 ONNX (~2 MB)"
[ -f models/silero/silero_vad.onnx ] || curl -L --fail -o models/silero/silero_vad.onnx \
    "https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx"

echo
echo "All models downloaded:"
du -sh models/*
