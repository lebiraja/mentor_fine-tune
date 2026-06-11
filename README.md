# Clarity

A fully local voice companion — talk out loud, get a thoughtful voice back. Nothing leaves your machine.

- **Brain:** Qwen3-4B-Instruct-2507 (Q4 GGUF, llama.cpp, GPU)
- **Ears:** Parakeet TDT 0.6B v3 (ONNX, CPU)
- **Voice:** Kokoro-82M, `af_heart` (ONNX, CPU)
- **Turn-taking:** Silero VAD with barge-in — interrupt it mid-sentence by speaking

```bash
cp .env.example .env
make models   # one-time ~4 GB download
make up
# open http://localhost:2000 and press Begin
```

Docs: [architecture](docs/architecture.md) · [API](docs/API.md) · [docker](docs/docker.md) · [fixes](docs/FIXES.md)

Sized for a 6 GB-VRAM laptop GPU (RTX 4050): ~3.5 GB VRAM for the LLM, audio models on CPU, ~2–2.5 s to first reply audio.

The old fine-tuning pipeline (datasets, QLoRA training) is archived under `scripts/training/`.
