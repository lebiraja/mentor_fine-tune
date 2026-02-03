# Voice System Installation Guide

## Quick Install

```bash
# This should work without dependency conflicts
pip install -r requirements_voice.txt
```

## If You Get Dependency Conflicts

The issue: Parler-TTS requires `transformers==4.46.1` but your main requirements need `transformers>=4.57.0`.

**Solution**: Install in two steps:

```bash
# Step 1: Install all dependencies EXCEPT parler-tts
pip install sounddevice soundfile librosa torchaudio speechbrain webrtcvad scipy pyttsx3

# Step 2: Install parler-tts without its conflicting dependencies
pip install --no-deps git+https://github.com/huggingface/parler-tts.git
```

## TTS Options

### Option 1: Parler-TTS (Recommended - Neural, Emotion-Controlled)
```bash
pip install --no-deps git+https://github.com/huggingface/parler-tts.git
```

**Pros:**
- High-quality neural speech synthesis
- Emotion-controlled voice characteristics
- Natural-sounding output

**Cons:**
- Version conflict with newer transformers
- Requires downloading ~900MB of models

### Option 2: pyttsx3 (Default Fallback - Simple, No ML)
Already included in `requirements_voice.txt`

**Pros:**
- Zero dependency conflicts
- Works offline with system TTS engines
- No model downloads needed
- Works immediately

**Cons:**
- Lower quality audio
- No emotion control
- Limited voice options
- More robotic sounding

## Verification

After installation, verify everything works:

```bash
# Test basic functionality
python -c "
import sounddevice
import torch
import transformers
import speechbrain
print('✓ All core dependencies installed')
"

# Test voice loop
python tests/test_voice_loop.py

# Test emotion detection
python tests/test_emotion.py
```

## What's Installed

### Required Dependencies
- **sounddevice** - Microphone/speaker I/O
- **librosa** - Audio processing
- **torchaudio** - Audio utilities for PyTorch
- **pyttsx3** - Fallback TTS (no ML models)
- **speechbrain** - Emotion detection
- **webrtcvad** - Voice activity detection

### Optional but Recommended
- **parler-tts** - Neural TTS with emotion control

### Already in main requirements.txt
- torch
- transformers
- numpy
- pyyaml

## Troubleshooting

### "ModuleNotFoundError: No module named 'parler_tts'"

**Cause**: Parler-TTS not installed due to dependency conflict

**Solution**: Install with `pip install --no-deps git+https://github.com/huggingface/parler-tts.git`

**Workaround**: System will automatically fall back to pyttsx3 (simpler TTS)

### "No module named 'pyttsx3'"

```bash
pip install pyttsx3
```

### "No audio input detected"

Check your microphone:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### "CUDA out of memory"

- Reduce `max_response_tokens` in config/voice_config.yaml (512 → 256)
- Disable parler-tts (will use pyttsx3 instead)

## Running the System

After successful installation:

```bash
./run_voice.sh
```

Or with custom options:

```bash
python scripts/voice_inference.py --turns 5
```

## Notes

- The voice system will work with either TTS option
- If parler-tts isn't available, pyttsx3 automatically takes over
- No functionality is lost, just reduced audio quality
- You can install parler-tts anytime later with the 2-step approach

---

**Ready?** Try: `python tests/test_voice_loop.py`
