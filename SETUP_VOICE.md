# Voice System Setup Guide

Step-by-step instructions to set up and run the ClarityMentor voice-to-voice system.

## Prerequisites

- Python 3.8+
- CUDA 11.8+ (for GPU acceleration on RTX 4050)
- Microphone and speakers
- ~4GB available VRAM on RTX 4050
- ~3.5GB disk space for models (auto-downloaded on first run)

## Installation

### 1. Install Voice Dependencies

```bash
cd /home/lebi/projects/mentor

# Install voice-specific packages
pip install -r requirements_voice.txt
```

**What this installs:**
- Audio I/O: sounddevice, librosa
- STT: DistilWhisper via transformers
- TTS: Parler-TTS
- Emotion: SpeechBrain, DistilRoBERTa via transformers
- VAD: Silero VAD (via torch.hub)

### 2. Verify Installation

```bash
# Check GPU availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Check key packages
python -c "import sounddevice; import torch; import transformers; print('✓ All dependencies OK')"
```

### 3. Test Voice I/O

```bash
python tests/test_voice_loop.py
```

**What happens:**
1. Loads STT and TTS models
2. Prompts you to speak
3. Transcribes your speech
4. Converts text back to speech
5. Plays the response

**Expected output:**
```
Listening... speak now
Recorded X.XX seconds of audio
✓ Transcript: [your words]
[audio plays back]
```

### 4. Test Emotion Detection

```bash
python tests/test_emotion.py
```

**What happens:**
- Tests text emotion classification on sample sentences
- Tests speech emotion with synthetic audio patterns
- Tests emotion fusion logic

**Expected output:**
```
Text Emotion Accuracy: 60-100%
[emotion test results]
✓ EMOTION FUSION TEST PASSED
```

### 5. Run Integration Tests

```bash
python tests/test_integration.py
```

**What happens:**
- Verifies all script files exist
- Checks configuration files are valid
- Tests LLM model loading and inference
- Tests emotion augmentation

**Expected output:**
```
✓ Scripts exist
✓ Configuration
✓ Emotion augmentation
✓ LLM response
ALL INTEGRATION TESTS PASSED ✓
```

## Running the System

### Quick Start

```bash
# Method 1: Using shell script
./run_voice.sh

# Method 2: Direct Python
python scripts/voice_inference.py
```

### First Run

The first run will:
1. Download all models from HuggingFace Hub (~3.5GB)
2. Load and initialize the pipeline
3. Prompt you to speak

```
================================================
CLARITYMENTOR - VOICE-TO-VOICE WITH EMOTION
================================================

Speak your thoughts. Press Ctrl+C to exit.

--- Turn 1 ---
============================================================
LISTENING...
============================================================
Listening... speak now
```

### Speak and Interact

1. **Speak naturally** - Talk about what's on your mind
2. **System listens** - Waits for silence to detect you're done
3. **System responds** - Generates emotion-aware philosophical guidance
4. **System speaks** - Plays the response with appropriate emotional tone

Example interaction:
```
You: I feel stuck in my career and don't know what to do
[System detects: sadness, 0.75 confidence]
[Augments prompt: "User is struggling. Validate pain, be gentle"]

ClarityMentor: You're experiencing a real tension between your current
path and where you want to be. This isn't a problem to solve
immediately—it's an invitation to examine what you truly value...

[System speaks response with warm, gentle tone]
```

### Advanced Options

```bash
# Run for limited turns
python scripts/voice_inference.py --turns 5

# Use custom config path
python scripts/voice_inference.py --config /path/to/voice_config.yaml

# Use custom model path
python scripts/voice_inference.py --model-path /path/to/model/final
```

## Troubleshooting

### Issue: "CUDA out of memory"

**Solution:**
1. Ensure no other GPU-intensive processes are running
2. Reduce max_response_tokens in voice_config.yaml (512 → 256)
3. Restart Python to clear GPU memory

```bash
# Check GPU memory
nvidia-smi

# Clear cache
python -c "import torch; torch.cuda.empty_cache()"
```

### Issue: "No audio detected / Microphone not working"

**Solution:**
1. Check microphone:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

2. Check microphone permissions:
```bash
# Linux: Check PulseAudio
pactl list sources

# macOS: Check System Preferences → Security & Privacy
```

3. Test audio directly:
```bash
python -c "
import sounddevice as sd
import numpy as np
audio = sd.rec(int(16000 * 2), samplerate=16000, channels=1)
sd.wait()
print(f'Recorded: {len(audio)} samples')
"
```

### Issue: "STT transcription is poor"

**Solutions:**
1. Speak clearly and at normal volume
2. Reduce background noise
3. Increase VAD min_silence_duration (0.8 → 1.2 seconds)
4. Try different microphone

### Issue: "Emotion detection seems wrong"

**Solutions:**
1. Emotion detection works best when emotion is clear
2. Neutral emotional state defaults to neutral emotion
3. Strong speech emotion (confidence > 0.7) overrides text emotion
4. Check emotion_prompts.yaml is loaded

### Issue: "TTS sounds robotic"

**Solutions:**
1. Parler-TTS quality depends on voice description
2. Adjust voice descriptions in emotion_prompts.yaml
3. Try different emotional phrasing in system prompt

### Issue: "LLM response is slow"

**Solutions:**
1. Reduce max_response_tokens (512 → 256)
2. Increase temperature (0.7 → 0.5) for faster sampling
3. Close other applications
4. Ensure CUDA is working: `nvidia-smi`

### Issue: Models not downloading

**Solution:**
```bash
# Models auto-download from HuggingFace on first run
# To pre-download:
python -c "
from transformers import AutoModel
models = [
    'distil-whisper/distil-medium.en',
    'j-hartmann/emotion-english-distilroberta-base',
]
for m in models:
    AutoModel.from_pretrained(m)
    print(f'Downloaded: {m}')
"
```

## Configuration

### Adjust Voice Parameters

Edit `config/voice_config.yaml`:

```yaml
audio:
  sample_rate: 16000          # Leave as-is (16kHz for speech)
  input_device: null          # Leave null for default mic
  output_device: null         # Leave null for default speaker

vad:
  threshold: 0.5              # Increase to 0.7 for less sensitive
  min_silence_duration: 0.8   # Increase to 1.2 for longer waits

generation:
  max_response_tokens: 512    # Reduce to 256 for faster responses
  temperature: 0.7            # Increase to 1.0 for more creative
  top_p: 0.9                  # Leave as-is
```

### Adjust Emotion Responses

Edit `config/emotion_prompts.yaml` to customize how the system responds to each emotion:

```yaml
anger:
  prompt_addition: |
    [Customize how system responds to anger]
  tts_description: "A calm, steady voice"  # [Customize voice]
```

## Performance Tips

### For Better Accuracy
- Speak clearly at normal volume
- Minimize background noise
- Let the system fully finish before speaking
- Use emotionally distinct phrases (helps emotion detection)

### For Faster Responses
- Reduce max_response_tokens (512 → 256)
- Use a quieter environment (faster VAD detection)
- Pre-warm models: run a test conversation before important use
- Close other GPU applications

### For Better Emotion Detection
- Exaggerate emotional tone slightly in voice
- Use emotionally clear language
- Example (sad): "I feel really down and lost" (vs. vague "I don't know")
- Speech emotion weighted more heavily (0.6 vs text 0.4)

## File Structure After Setup

```
/home/lebi/projects/mentor/
├── config/
│   ├── voice_config.yaml
│   └── emotion_prompts.yaml
├── scripts/
│   ├── voice_inference.py
│   ├── llm_core.py
│   ├── voice/
│   │   ├── audio_io.py
│   │   ├── vad.py
│   │   ├── stt.py
│   │   ├── tts.py
│   │   └── model_manager.py
│   ├── emotion/
│   │   ├── speech_emotion.py
│   │   ├── text_emotion.py
│   │   ├── fusion.py
│   │   └── prompt_augmenter.py
│   └── utils/
│       └── memory_utils.py
├── tests/
│   ├── test_voice_loop.py
│   ├── test_emotion.py
│   └── test_integration.py
├── conversations/              # Auto-created, saved conversations
└── VOICE_SYSTEM.md            # System documentation
```

## Next Steps

1. Run `./run_voice.sh` to start interactive mode
2. Have a conversation with ClarityMentor
3. Check `conversations/` folder for saved conversation history
4. Adjust `config/emotion_prompts.yaml` to customize responses
5. Refer to `VOICE_SYSTEM.md` for technical details

## Support

For issues:
1. Check troubleshooting section above
2. Review VOICE_SYSTEM.md for technical details
3. Check logs and error messages carefully
4. Ensure dependencies are installed: `pip install -r requirements_voice.txt`

---

Enjoy using ClarityMentor's voice system!
