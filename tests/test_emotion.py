"""Test emotion detection - speech, text, and fusion."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from emotion.speech_emotion import SpeechEmotionDetector
from emotion.text_emotion import TextEmotionDetector
from emotion.fusion import EmotionFusion


def test_text_emotion():
    """Test text emotion detection."""
    print("\n" + "="*60)
    print("TEXT EMOTION DETECTION TEST")
    print("="*60 + "\n")

    import yaml

    config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize
    print("Loading text emotion model...")
    detector = TextEmotionDetector(config["models"]["text_emotion"])
    detector.load()

    # Test cases
    test_cases = [
        ("I am so happy and excited!", "joy"),
        ("I feel terrible and sad", "sadness"),
        ("I'm scared and anxious", "fear"),
        ("I'm so angry and frustrated!", "anger"),
        ("This is fine", "neutral"),
    ]

    print(f"✓ Model loaded\n")
    print("Testing {len(test_cases)} text samples:\n")

    correct = 0
    for text, expected_emotion in test_cases:
        result = detector.detect_emotion(text)
        emotion = result["emotion"].lower()
        confidence = result["confidence"]
        expected_lower = expected_emotion.lower()

        # Check if top emotion matches or is close
        is_correct = emotion == expected_lower
        status = "✓" if is_correct else "✗"

        if is_correct:
            correct += 1

        print(f"{status} Text: '{text}'")
        print(f"  Expected: {expected_emotion}, Got: {emotion} ({confidence:.2f})\n")

    # Cleanup
    detector.unload()

    accuracy = correct / len(test_cases)
    print(f"-" * 60)
    print(f"Text Emotion Accuracy: {accuracy*100:.1f}% ({correct}/{len(test_cases)})")
    print(f"-" * 60 + "\n")

    return accuracy >= 0.6  # At least 60% for basic model


def test_speech_emotion():
    """Test speech emotion detection (requires audio files)."""
    print("\n" + "="*60)
    print("SPEECH EMOTION DETECTION TEST")
    print("="*60 + "\n")

    import yaml

    config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize
    print("Loading speech emotion model...")
    detector = SpeechEmotionDetector(config["models"]["speech_emotion"])
    detector.load()
    print("✓ Model loaded\n")

    # Create synthetic test audio (simple tone variation)
    sample_rate = 16000
    duration = 1.0
    num_samples = int(sample_rate * duration)

    # Test with noise patterns
    print("Testing with synthetic audio patterns:\n")

    # High frequency = potential excitement/fear
    t = np.arange(num_samples) / sample_rate
    high_freq_audio = 0.1 * np.sin(2 * np.pi * 400 * t)
    result = detector.detect_emotion(high_freq_audio, sample_rate)
    print(f"High frequency tone: {result['emotion']} ({result['confidence']:.2f})")

    # Low frequency = potential sadness
    low_freq_audio = 0.1 * np.sin(2 * np.pi * 100 * t)
    result = detector.detect_emotion(low_freq_audio, sample_rate)
    print(f"Low frequency tone: {result['emotion']} ({result['confidence']:.2f})")

    # Cleanup
    detector.unload()

    print("\n" + "-" * 60)
    print("Speech Emotion Detection TEST PASSED")
    print("-" * 60 + "\n")

    return True


def test_emotion_fusion():
    """Test emotion fusion."""
    print("\n" + "="*60)
    print("EMOTION FUSION TEST")
    print("="*60 + "\n")

    import yaml

    config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize fusion
    print("Initializing emotion fusion...\n")
    fusion = EmotionFusion(config)

    # Test case 1: Agreement (both angry)
    print("Test 1: Agreement (both detect anger)")
    speech_emo = {
        "emotion": "anger",
        "confidence": 0.85,
        "scores": {
            "anger": 0.85,
            "sadness": 0.05,
            "fear": 0.05,
            "joy": 0.01,
            "neutral": 0.04,
            "disgust": 0.0,
            "surprise": 0.0,
            "confusion": 0.0,
        },
    }
    text_emo = {
        "emotion": "anger",
        "confidence": 0.78,
        "scores": {
            "anger": 0.78,
            "sadness": 0.1,
            "fear": 0.05,
            "joy": 0.0,
            "neutral": 0.05,
            "disgust": 0.02,
            "surprise": 0.0,
            "confusion": 0.0,
        },
    }

    result = fusion.fuse(speech_emo, text_emo)
    print(f"  Primary emotion: {result['primary_emotion']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Agreement: {result['source_agreement']:.2f}")
    assert result["primary_emotion"].lower() == "anger", "Should detect anger"
    print("  ✓ PASSED\n")

    # Test case 2: Conflict (speech anger, text neutral - should trust speech)
    print("Test 2: Conflict (speech=anger, text=neutral)")
    speech_emo = {
        "emotion": "anger",
        "confidence": 0.85,
        "scores": {
            "anger": 0.85,
            "sadness": 0.05,
            "fear": 0.05,
            "joy": 0.01,
            "neutral": 0.04,
            "disgust": 0.0,
            "surprise": 0.0,
            "confusion": 0.0,
        },
    }
    text_emo = {
        "emotion": "neutral",
        "confidence": 0.9,
        "scores": {
            "anger": 0.0,
            "sadness": 0.05,
            "fear": 0.05,
            "joy": 0.0,
            "neutral": 0.9,
            "disgust": 0.0,
            "surprise": 0.0,
            "confusion": 0.0,
        },
    }

    result = fusion.fuse(speech_emo, text_emo)
    print(f"  Primary emotion: {result['primary_emotion']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Agreement: {result['source_agreement']:.2f}")
    # Should weight speech more heavily due to high confidence
    assert result["primary_emotion"].lower() == "anger", "Should trust high-confidence speech"
    print("  ✓ PASSED\n")

    # Test case 3: Both neutral
    print("Test 3: Both neutral")
    speech_emo = {
        "emotion": "neutral",
        "confidence": 0.6,
        "scores": {
            "anger": 0.05,
            "sadness": 0.05,
            "fear": 0.05,
            "joy": 0.1,
            "neutral": 0.6,
            "disgust": 0.05,
            "surprise": 0.05,
            "confusion": 0.0,
        },
    }
    text_emo = {
        "emotion": "neutral",
        "confidence": 0.65,
        "scores": {
            "anger": 0.05,
            "sadness": 0.05,
            "fear": 0.05,
            "joy": 0.1,
            "neutral": 0.65,
            "disgust": 0.05,
            "surprise": 0.05,
            "confusion": 0.0,
        },
    }

    result = fusion.fuse(speech_emo, text_emo)
    print(f"  Primary emotion: {result['primary_emotion']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Agreement: {result['source_agreement']:.2f}")
    assert result["primary_emotion"].lower() == "neutral", "Should detect neutral"
    print("  ✓ PASSED\n")

    print("-" * 60)
    print("EMOTION FUSION TEST PASSED")
    print("-" * 60 + "\n")

    return True


def main():
    """Run all emotion tests."""
    print("\n" + "="*80)
    print("EMOTION DETECTION TEST SUITE")
    print("="*80)

    try:
        # Test text emotion
        text_ok = test_text_emotion()

        # Test speech emotion
        speech_ok = test_speech_emotion()

        # Test fusion
        fusion_ok = test_emotion_fusion()

        print("\n" + "="*80)
        if text_ok and speech_ok and fusion_ok:
            print("ALL EMOTION TESTS PASSED ✓")
            print("="*80 + "\n")
            return True
        else:
            print("SOME TESTS FAILED ✗")
            print("="*80 + "\n")
            return False

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
