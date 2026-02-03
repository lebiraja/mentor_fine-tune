"""Test basic voice I/O loop - record, transcribe, synthesize."""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from voice.audio_io import AudioIO
from voice.vad import VoiceActivityDetector
from voice.stt import SpeechToText
from voice.tts import EmotionalTTS


def test_voice_loop():
    """Test full voice loop: mic → STT → TTS → speaker."""

    # Load config
    import yaml

    config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    print("\n" + "="*60)
    print("Voice I/O Loop Test")
    print("="*60 + "\n")

    # Initialize components
    print("1. Initializing audio I/O...")
    audio_io = AudioIO(config["audio"])
    print("   ✓ Audio I/O ready")

    print("2. Initializing VAD...")
    vad = VoiceActivityDetector(config["vad"])
    print("   ✓ VAD ready")

    print("3. Initializing STT...")
    stt = SpeechToText(config["models"]["stt"])
    print("   ✓ STT ready")

    print("4. Initializing TTS...")
    tts = EmotionalTTS(config["models"]["tts"])
    tts.load()
    print("   ✓ TTS ready\n")

    # Record audio
    print("-" * 60)
    print("RECORDING PHASE")
    print("-" * 60)
    print("Speak something (will record until you stop)...\n")

    audio, duration = audio_io.record_until_silence(vad, max_duration=10.0)

    if len(audio) == 0:
        print("No audio recorded. Exiting.")
        return False

    print(f"✓ Recorded {duration:.2f} seconds of audio\n")

    # Transcribe
    print("-" * 60)
    print("TRANSCRIPTION PHASE")
    print("-" * 60)
    print("Transcribing audio...\n")

    text = stt.transcribe(audio, sample_rate=config["audio"]["sample_rate"])

    if not text:
        print("Failed to transcribe. Exiting.")
        return False

    print(f"Transcribed: {text}\n")

    # Synthesize
    print("-" * 60)
    print("SYNTHESIS PHASE")
    print("-" * 60)
    print("Synthesizing response...\n")

    response_text = f"You said: {text}"
    audio_response = tts.synthesize(response_text)

    if len(audio_response) == 0:
        print("Failed to synthesize. Exiting.")
        return False

    print(f"✓ Generated {len(audio_response)} audio samples\n")

    # Play back
    print("-" * 60)
    print("PLAYBACK PHASE")
    print("-" * 60)
    print("Playing back synthesized speech...\n")

    audio_io.play_audio(audio_response, sample_rate=tts.sample_rate)

    print("✓ Playback complete\n")

    # Cleanup
    print("-" * 60)
    print("Cleanup")
    print("-" * 60)
    stt.unload()
    tts.unload()

    print("✓ Models unloaded\n")

    print("="*60)
    print("TEST PASSED - Voice loop working correctly!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_voice_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
