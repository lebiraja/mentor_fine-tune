"""
Voice-to-Voice ClarityMentor with Emotion Detection.

Orchestrates: Audio I/O → STT → Emotion → LLM → TTS
"""

import sys
from pathlib import Path
import yaml
import argparse
import json
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_core import load_claritymentor_model, load_system_prompt, generate_response_core
from voice.audio_io import AudioIO
from voice.vad import VoiceActivityDetector
from voice.stt import SpeechToText
from voice.tts import EmotionalTTS
from voice.model_manager import ModelManager
from emotion.speech_emotion import SpeechEmotionDetector
from emotion.text_emotion import TextEmotionDetector
from emotion.fusion import EmotionFusion
from emotion.prompt_augmenter import PromptAugmenter


class VoiceInferencePipeline:
    """Full voice-to-voice pipeline with emotion detection."""

    def __init__(self, config_path: Path, model_path: Path):
        """
        Initialize voice pipeline.

        Args:
            config_path: Path to voice_config.yaml
            model_path: Path to ClarityMentor LoRA model
        """
        # Load configuration
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.config_dir = config_path.parent
        self.model_path = model_path

        # Initialize components
        print("Initializing Voice Pipeline...\n")

        self.audio_io = AudioIO(self.config["audio"])
        self.vad = VoiceActivityDetector(self.config["vad"])
        self.stt = SpeechToText(self.config["models"]["stt"])
        self.speech_emotion = SpeechEmotionDetector(
            self.config["models"]["speech_emotion"]
        )
        self.text_emotion = TextEmotionDetector(self.config["models"]["text_emotion"])
        self.tts = EmotionalTTS(self.config["models"]["tts"])
        self.fusion = EmotionFusion(self.config)
        self.augmenter = PromptAugmenter(
            self.config_dir / "emotion_prompts.yaml"
        )

        # Model manager (handles GPU memory)
        self.manager = ModelManager(self.config)

        # Load system prompt
        self.base_system_prompt = load_system_prompt(self.config_dir)

        # Conversation history
        self.conversation_history = []
        self.emotion_history = []

    def initialize(self):
        """Load persistent models (LLM and VAD)."""
        print("Loading ClarityMentor LLM (persistent)...")
        self.manager.load_llm_persistent(self.model_path)
        self.manager.load_vad_persistent()
        print("✓ Pipeline ready for voice input\n")

    def process_turn(self) -> dict:
        """
        Process one conversation turn: listen → understand → respond.

        Returns:
            {user_text, emotion, response, success}
        """
        result = {
            "user_text": "",
            "emotion": {},
            "response": "",
            "success": False,
        }

        try:
            # === PHASE 1: Voice Input ===
            print("\n" + "="*60)
            print("LISTENING...")
            print("="*60)

            self.manager.load_stt_pipeline()
            self.manager.load_speech_emotion()

            # Record audio until silence
            audio, duration = self.audio_io.record_until_silence(self.vad)

            if len(audio) == 0:
                print("No audio detected.")
                self.manager.unload_stt_pipeline()
                self.manager.unload_speech_emotion()
                return result

            print(f"Recorded {duration:.2f}s of audio")

            # Transcribe
            print("Transcribing...")
            user_text = self.stt.transcribe(
                audio, sample_rate=self.config["audio"]["sample_rate"]
            )

            if not user_text:
                print("Failed to transcribe audio.")
                self.manager.unload_stt_pipeline()
                self.manager.unload_speech_emotion()
                return result

            print(f"✓ Transcript: {user_text}")

            # Detect speech emotion
            print("Analyzing emotional tone...")
            speech_emo = self.speech_emotion.detect_emotion(
                audio, sample_rate=self.config["audio"]["sample_rate"]
            )
            print(f"  Speech emotion: {speech_emo['emotion']} "
                  f"({speech_emo['confidence']:.2f})")

            self.manager.unload_stt_pipeline()
            self.manager.unload_speech_emotion()

            # === PHASE 2: Text Emotion ===
            print("Analyzing semantic content...")
            self.manager.load_text_emotion()

            text_emo = self.text_emotion.detect_emotion(user_text)
            print(f"  Text emotion: {text_emo['emotion']} "
                  f"({text_emo['confidence']:.2f})")

            self.manager.unload_text_emotion()

            # === PHASE 3: Emotion Fusion ===
            print("Fusing emotion signals...")
            emotion_context = self.fusion.fuse(speech_emo, text_emo)
            print(f"  Final emotion: {emotion_context['primary_emotion']} "
                  f"(agreement: {emotion_context['source_agreement']:.2f})")

            # === PHASE 4: Augment System Prompt ===
            augmented_prompt = self.augmenter.augment_system_prompt(
                self.base_system_prompt, emotion_context
            )

            # === PHASE 5: LLM Inference ===
            print("\n" + "="*60)
            print("THINKING...")
            print("="*60)

            # Build messages with history
            messages = [{"role": "system", "content": augmented_prompt}]
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": user_text})

            response = generate_response_core(
                self.manager.llm_model,
                self.manager.llm_tokenizer,
                messages,
                max_new_tokens=self.config["generation"]["max_response_tokens"],
                temperature=self.config["generation"]["temperature"],
                top_p=self.config["generation"]["top_p"],
            )

            print("✓ Response generated")

            # === PHASE 6: TTS ===
            print("\n" + "="*60)
            print("SPEAKING...")
            print("="*60)

            self.manager.load_tts()
            audio_response = self.tts.synthesize(response, emotion_context)
            self.manager.unload_tts()

            if len(audio_response) == 0:
                print("Failed to synthesize speech.")
                return result

            print("✓ Speech synthesized")

            # === PHASE 7: Playback ===
            print("Playing response...\n")
            self.audio_io.play_audio(audio_response, sample_rate=self.tts.sample_rate)

            # === Update History ===
            self.conversation_history.append({"role": "user", "content": user_text})
            self.conversation_history.append({"role": "assistant", "content": response})
            self.emotion_history.append(emotion_context)

            # Display response
            print("\n" + "="*60)
            print("RESPONSE")
            print("="*60)
            print(f"\n{response}\n")

            result = {
                "user_text": user_text,
                "emotion": emotion_context,
                "response": response,
                "success": True,
            }

            return result

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            return result
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return result

    def run_interactive(self, max_turns: int = None):
        """
        Run interactive voice conversation mode.

        Args:
            max_turns: Maximum number of turns (None for unlimited)
        """
        print("\n" + "="*80)
        print("CLARITYMENTOR - VOICE-TO-VOICE WITH EMOTION DETECTION")
        print("="*80)
        print("\nSpeak your thoughts. Press Ctrl+C to exit.\n")

        turn = 0

        try:
            while max_turns is None or turn < max_turns:
                turn += 1
                print(f"\n--- Turn {turn} ---")
                result = self.process_turn()

                if not result["success"]:
                    print("Turn failed. Try again.\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            self._save_conversation(turn)

    def _save_conversation(self, turns: int) -> None:
        """Save conversation history to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(
                f"/home/lebi/projects/mentor/conversations/conversation_{timestamp}.json"
            )
            output_file.parent.mkdir(parents=True, exist_ok=True)

            conversation_data = {
                "timestamp": timestamp,
                "turns": turns,
                "messages": self.conversation_history,
                "emotions": self.emotion_history,
            }

            with open(output_file, "w") as f:
                json.dump(conversation_data, f, indent=2)

            print(f"✓ Conversation saved to {output_file}")

        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ClarityMentor Voice-to-Voice with Emotion Detection"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/home/lebi/projects/mentor/config/voice_config.yaml"),
        help="Voice configuration file",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("/home/lebi/projects/mentor/models/claritymentor-lora/final"),
        help="Path to ClarityMentor LoRA model",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Maximum number of turns (None for unlimited)",
    )

    args = parser.parse_args()

    # Check model exists
    if not args.model_path.exists():
        print(f"Error: Model not found at {args.model_path}")
        sys.exit(1)

    # Check config exists
    if not args.config.exists():
        print(f"Error: Config not found at {args.config}")
        sys.exit(1)

    # Initialize and run
    pipeline = VoiceInferencePipeline(args.config, args.model_path)
    pipeline.initialize()
    pipeline.run_interactive(max_turns=args.turns)


if __name__ == "__main__":
    main()
