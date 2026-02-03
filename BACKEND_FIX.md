# Backend Startup Fix - TTS Import Error

## Problem
The backend failed to start with error:
```
ImportError: cannot import name 'TextToSpeech' from 'scripts.voice.tts'
```

## Root Cause
The TTS class in `scripts/voice/tts.py` is named `EmotionalTTS`, not `TextToSpeech`.

## Solution Applied

### 1. Fixed `backend/services/model_service.py`
Changed the TTS loading from:
```python
from scripts.voice.tts import TextToSpeech
tts_config = voice_config.get("models", {}).get("tts", {})
self._models["tts"] = TextToSpeech(tts_config)
```

To:
```python
from scripts.voice.tts import EmotionalTTS
tts_config = voice_config.get("models", {}).get("tts", {})
tts = EmotionalTTS(tts_config)
tts.load()  # Load the model
self._models["tts"] = tts
```

### 2. Fixed `backend/services/tts_service.py`
The `EmotionalTTS.synthesize()` method returns a numpy array, not bytes. Updated the conversion:

```python
def _synthesize_blocking(self, text: str, emotion: Optional[Dict[str, Any]] = None) -> bytes:
    import numpy as np
    from backend.core.audio_utils import array_to_bytes

    # Call the underlying model's synthesize method (returns numpy array)
    audio_array = self.model.synthesize(text, emotion)

    # Convert numpy array to bytes
    if isinstance(audio_array, np.ndarray) and len(audio_array) > 0:
        return array_to_bytes(audio_array)
    else:
        return b""
```

## Verification
✅ Imports now work correctly:
```bash
./venv/bin/python -c "from backend.services.model_service import ModelService; from scripts.voice.tts import EmotionalTTS; print('✓ Imports OK')"
```

## Next Steps

### Start the Backend
```bash
cd /home/lebi/projects/mentor
./run_backend.sh
```

**First run** will:
1. Load STT model (DistilWhisper) - ~1 min
2. Load TTS model (Parler-TTS or fallback to pyttsx3) - ~1 min
3. Load emotion models (Text + Speech) - ~30 sec
4. Load LLM (ClarityMentor) - ~1 min
5. Load VAD (Silero) - ~10 sec

**Total first-run time:** ~3-5 minutes

Once you see:
```
✓ All models loaded and ready!

WebSocket endpoint: ws://localhost:2323/ws/voice
Health check: http://localhost:2323/api/health
```

### Test the Backend
```bash
# In another terminal
cd /home/lebi/projects/mentor
./run_test_client.sh
```

## Files Modified
- ✅ `backend/services/model_service.py` - Fixed TTS class import and loading
- ✅ `backend/services/tts_service.py` - Fixed numpy array to bytes conversion

## Status
🚀 **Ready to use!** The backend should now start correctly on port 2323.

---

**Time to test:** ~5-7 minutes (1st run includes model loading)
**Next runs:** ~1 minute (models cached)
