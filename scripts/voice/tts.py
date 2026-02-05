"""Text-to-Speech using Parler-TTS with emotion control."""

import numpy as np
import torch
from typing import Optional, Dict, Any


class EmotionalTTS:
    """Generate speech from text with emotion control using Parler-TTS."""

    def __init__(self, config: dict):
        """
        Initialize TTS model.

        Args:
            config: Dictionary with TTS configuration
                - model_name: HuggingFace model ID
                - voice_description: Default voice description
        """
        self.model_name = config.get("model_name", "parler-tts/parler-tts-mini-expresso")
        self.default_voice_desc = config.get(
            "voice_description",
            "A calm, thoughtful male voice speaks clearly"
        )

        self.model = None
        self.tokenizer = None
        self.sample_rate = 24000  # Parler-TTS standard sample rate

    def load(self) -> None:
        """Load TTS model to GPU."""
        if self.model is not None:
            return

        try:
            print(f"Loading TTS model: {self.model_name}")

            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer

            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch_dtype,
            ).to(device)

            print("✓ TTS model loaded successfully")

        except ImportError as e:
            print(f"Warning: parler-tts not available ({e})")
            print("Falling back to pyttsx3 (simpler TTS without emotion control)")
            try:
                import pyttsx3
                self.model = "pyttsx3_fallback"
                self.tts_engine = pyttsx3.init()
                print("✓ Fallback TTS loaded")
            except ImportError:
                print("Error: Neither parler-tts nor pyttsx3 available")
                print("Install one with: pip install pyttsx3")
                raise
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            print("Trying fallback TTS...")
            try:
                import pyttsx3
                self.model = "pyttsx3_fallback"
                self.tts_engine = pyttsx3.init()
                print("✓ Fallback TTS loaded")
            except ImportError:
                raise

    def synthesize(
        self, text: str, emotion_context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Generate speech from text with optional emotion control.

        Args:
            text: Text to synthesize
            emotion_context: Optional emotion context dict with:
                - primary_emotion: Detected emotion
                - confidence: Confidence score
                - combined_scores: Emotion scores

        Returns:
            Audio array (24000 Hz for parler-tts, 22050 Hz for pyttsx3)
        """
        if self.model is None:
            self.load()

        if not text or len(text.strip()) == 0:
            return np.array([], dtype=np.float32)

        # Use fallback pyttsx3 if available
        if self.model == "pyttsx3_fallback":
            return self._synthesize_pyttsx3(text)

        try:
            # Get voice description based on emotion
            voice_desc = self._get_voice_description(emotion_context)

            # Create description string
            description = f"{voice_desc}: {text}"

            # Tokenize
            input_ids = self.tokenizer(description, return_tensors="pt").input_ids

            if torch.cuda.is_available():
                input_ids = input_ids.to("cuda")

            # Generate speech
            with torch.no_grad():
                generation = self.model.generate(input_ids=input_ids, do_sample=True)

            # Extract speech tokens and convert to audio
            speech = generation.cpu().numpy().squeeze()

            # Normalize
            if len(speech) > 0:
                max_val = np.max(np.abs(speech))
                if max_val > 0:
                    speech = speech / max_val

            return speech.astype(np.float32)

        except Exception as e:
            print(f"Error during TTS synthesis: {e}")
            return np.array([], dtype=np.float32)

    def _synthesize_pyttsx3(self, text: str) -> np.ndarray:
        """
        Synthesize using pyttsx3 fallback (no neural network).

        Args:
            text: Text to synthesize

        Returns:
            Audio array (resampled to 16000 Hz for consistency)
        """
        try:
            import wave
            import tempfile
            import os

            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            self.tts_engine.save_to_file(text, temp_path)
            self.tts_engine.runAndWait()

            # Read and convert to numpy array
            with wave.open(temp_path, 'rb') as wav_file:
                original_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                # Normalize to float32 [-1, 1]
                audio_data = audio_data.astype(np.float32) / 32768.0

            # Clean up temp file
            os.unlink(temp_path)

            # Resample to 16000 Hz for consistency with frontend
            if original_rate != 16000:
                # Simple linear interpolation resampling
                duration = len(audio_data) / original_rate
                new_length = int(duration * 16000)
                indices = np.linspace(0, len(audio_data) - 1, new_length)
                audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data)
                self.sample_rate = 16000
            else:
                self.sample_rate = original_rate

            return audio_data.astype(np.float32)

        except Exception as e:
            print(f"Error with pyttsx3 synthesis: {e}")
            import traceback
            traceback.print_exc()
            # Return a short silence as fallback
            return np.zeros(16000, dtype=np.float32)  # 1 second of silence at 16kHz

    def _get_voice_description(
        self, emotion_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get voice description based on emotion context.

        Args:
            emotion_context: Emotion detection result

        Returns:
            Voice description string for Parler-TTS
        """
        if emotion_context is None:
            return self.default_voice_desc

        emotion = emotion_context.get("primary_emotion", "neutral")
        confidence = emotion_context.get("confidence", 0.0)

        # Only use emotion-specific voice if confident
        if confidence < 0.5:
            return self.default_voice_desc

        # Map emotions to voice descriptions
        emotion_voices = {
            "anger": "A calm, steady voice that is grounding and measured",
            "sadness": "A warm, gentle voice with compassion and understanding",
            "fear": "A calm, reassuring voice that is stable and clear",
            "joy": "A warm, engaged voice with subtle enthusiasm",
            "confused": "A clear, patient voice that explains things carefully",
            "neutral": "A calm, thoughtful voice speaks clearly with measured pace",
            "surprise": "An engaged, clear voice with natural dynamics",
            "disgust": "A balanced, non-judgmental voice with steady pace",
        }

        return emotion_voices.get(emotion, self.default_voice_desc)

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.model is not None:
            if self.model == "pyttsx3_fallback":
                # pyttsx3 doesn't need VRAM cleanup
                self.tts_engine = None
            else:
                self.model = None
                self.tokenizer = None

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
