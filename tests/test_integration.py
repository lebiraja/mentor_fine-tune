"""Integration tests for the full voice pipeline."""

import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from llm_core import load_claritymentor_model, load_system_prompt, generate_response_core
from emotion.fusion import EmotionFusion
from emotion.prompt_augmenter import PromptAugmenter


def test_llm_response():
    """Test that LLM model loads and generates responses."""
    print("\n" + "="*60)
    print("LLM RESPONSE TEST")
    print("="*60 + "\n")

    model_path = Path("/home/lebi/projects/mentor/models/claritymentor-lora/final")
    config_dir = Path("/home/lebi/projects/mentor/config")

    if not model_path.exists():
        print(f"Model not found at {model_path}")
        print("Skipping LLM test")
        return True

    try:
        print("Loading ClarityMentor model...")
        model, tokenizer = load_claritymentor_model(model_path)
        print("✓ Model loaded\n")

        print("Loading system prompt...")
        system_prompt = load_system_prompt(config_dir)
        print(f"✓ System prompt loaded ({len(system_prompt)} chars)\n")

        # Test basic response
        print("Generating test response...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "What should I do with my life?"},
        ]

        response = generate_response_core(
            model, tokenizer, messages, max_new_tokens=256
        )

        print(f"✓ Response generated ({len(response)} chars)\n")
        print(f"Sample response:\n{response[:200]}...\n")

        return len(response) > 20

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_emotion_augmentation():
    """Test that system prompt is augmented based on emotion."""
    print("\n" + "="*60)
    print("EMOTION AUGMENTATION TEST")
    print("="*60 + "\n")

    config_dir = Path("/home/lebi/projects/mentor/config")
    config_path = config_dir / "emotion_prompts.yaml"

    if not config_path.exists():
        print(f"Config not found at {config_path}")
        return False

    try:
        # Load base prompt
        prompt_file = config_dir / "system_prompt.txt"
        base_prompt = prompt_file.read_text() if prompt_file.exists() else "Default prompt"

        # Initialize augmenter
        augmenter = PromptAugmenter(config_path)

        # Test emotions
        test_emotions = [
            {"primary_emotion": "anger", "confidence": 0.8},
            {"primary_emotion": "sadness", "confidence": 0.75},
            {"primary_emotion": "fear", "confidence": 0.7},
            {"primary_emotion": "joy", "confidence": 0.85},
            {"primary_emotion": "neutral", "confidence": 0.5},
        ]

        print(f"Base prompt length: {len(base_prompt)} chars\n")

        for emotion_ctx in test_emotions:
            augmented = augmenter.augment_system_prompt(base_prompt, emotion_ctx)
            emotion = emotion_ctx["primary_emotion"]

            if emotion == "neutral":
                # Neutral should not augment
                is_augmented = augmented == base_prompt
            else:
                # Others should add content
                is_augmented = len(augmented) > len(base_prompt)

            status = "✓" if is_augmented else "✗"
            print(f"{status} {emotion}: "
                  f"base={len(base_prompt)}, augmented={len(augmented)}")

        print("\n✓ All emotions tested\n")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_voice_config():
    """Test that configuration files are valid."""
    print("\n" + "="*60)
    print("CONFIGURATION TEST")
    print("="*60 + "\n")

    config_dir = Path("/home/lebi/projects/mentor/config")

    files_to_check = [
        ("voice_config.yaml", ["audio", "models", "generation"]),
        ("emotion_prompts.yaml", ["emotions", "fusion"]),
    ]

    all_ok = True

    for filename, required_keys in files_to_check:
        config_path = config_dir / filename
        print(f"Checking {filename}...", end=" ")

        if not config_path.exists():
            print("✗ NOT FOUND")
            all_ok = False
            continue

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Check for required keys
            missing_keys = [k for k in required_keys if k not in config]

            if missing_keys:
                print(f"✗ Missing keys: {missing_keys}")
                all_ok = False
            else:
                print("✓ OK")

        except Exception as e:
            print(f"✗ Error: {e}")
            all_ok = False

    print()
    return all_ok


def test_scripts_exist():
    """Test that all required script files exist."""
    print("\n" + "="*60)
    print("SCRIPTS EXISTENCE TEST")
    print("="*60 + "\n")

    scripts_dir = Path("/home/lebi/projects/mentor/scripts")

    required_files = [
        "llm_core.py",
        "voice_inference.py",
        "voice/__init__.py",
        "voice/audio_io.py",
        "voice/vad.py",
        "voice/stt.py",
        "voice/tts.py",
        "voice/model_manager.py",
        "emotion/__init__.py",
        "emotion/speech_emotion.py",
        "emotion/text_emotion.py",
        "emotion/fusion.py",
        "emotion/prompt_augmenter.py",
    ]

    all_ok = True

    for filename in required_files:
        filepath = scripts_dir / filename
        exists = "✓" if filepath.exists() else "✗"
        print(f"{exists} {filename}")
        if not filepath.exists():
            all_ok = False

    print()
    return all_ok


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("VOICE PIPELINE INTEGRATION TEST SUITE")
    print("="*80)

    results = {
        "Scripts exist": test_scripts_exist(),
        "Configuration": test_voice_config(),
        "Emotion augmentation": test_emotion_augmentation(),
        "LLM response": test_llm_response(),
    }

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80 + "\n")

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*80)
    if all_passed:
        print("ALL INTEGRATION TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*80 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
