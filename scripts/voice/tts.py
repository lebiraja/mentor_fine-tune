"""Text-to-Speech using CosyVoice3 with emotion control."""

import numpy as np
import torch
from typing import Optional, Dict, Any
import os


class EmotionalTTS:
    """Generate speech from text with emotion control using CosyVoice3."""

    def __init__(self, config: dict):
        """
        Initialize TTS model.

        Args:
            config: Dictionary with TTS configuration
                - model_name: ModelScope/HuggingFace model ID
                - voice_description: Default voice description/preset
        """
        self.model_name = config.get("model_name", "FunAudioLLM/CosyVoice2-0.5B")
        self.instruct_text = config.get(
            "instruct_text",
            "Speak in a calm, warm, and friendly tone."
        )

        self.model = None
        self.sample_rate = 24000  # CosyVoice3 uses 24000Hz

    def load(self) -> None:
        """Load TTS model to GPU."""
        if self.model is not None:
            return

        try:
            print(f"Loading TTS model: {self.model_name}")

            # CosyVoice3 for Fun-CosyVoice3-0.5B models, CosyVoice2 for CosyVoice2-0.5B
            if "CosyVoice3" in self.model_name:
                from cosyvoice.cli.cosyvoice import CosyVoice3
                ModelClass = CosyVoice3
            elif "CosyVoice2" in self.model_name:
                from cosyvoice.cli.cosyvoice import CosyVoice2
                ModelClass = CosyVoice2
            else:
                from cosyvoice.cli.cosyvoice import CosyVoice
                ModelClass = CosyVoice

            # CosyVoice handles model download internally via snapshot_download
            self.model = ModelClass(self.model_name)

            # Get sample rate from model
            if hasattr(self.model, 'sample_rate'):
                self.sample_rate = self.model.sample_rate

            # List available speakers
            if hasattr(self.model, 'list_available_spks'):
                spks = self.model.list_available_spks()
                print(f"Available speakers: {spks}")
                if spks:
                    self.default_spk = spks[0]
                else:
                    self.default_spk = None
            else:
                self.default_spk = None

            print(f"✓ CosyVoice TTS model loaded successfully (sample_rate={self.sample_rate})")

        except Exception as e:
            print(f"Error loading CosyVoice TTS model: {e}")
            import traceback
            traceback.print_exc()
            raise

    def synthesize(
        self, text: str, emotion_context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Generate speech from text using CosyVoice.

        Args:
            text: Text to synthesize
            emotion_context: Optional emotion context

        Returns:
            Audio array (1D numpy array of float32)
        """
        if self.model is None:
            self.load()

        if not text or len(text.strip()) == 0:
            return np.array([], dtype=np.float32)

        try:
            # Get instruction based on emotion
            instruction = self._get_voice_instruction(emotion_context)

            audio_chunks = []

            # Try different inference methods based on what's available
            if hasattr(self.model, 'inference_instruct2'):
                # CosyVoice3 uses inference_instruct2 for text-only synthesis
                # inference_instruct2(tts_text, instruct_text, prompt_wav, zero_shot_spk_id='', ...)
                # For text-only, we can pass None for prompt_wav
                for result in self.model.inference_instruct2(
                    text,
                    instruction,
                    prompt_wav=None,
                    stream=False,
                    speed=1.0
                ):
                    if 'tts_speech' in result:
                        audio_chunks.append(result['tts_speech'].cpu().numpy())

            elif hasattr(self.model, 'inference_sft') and self.default_spk:
                # Use SFT inference with a default speaker
                for result in self.model.inference_sft(
                    text,
                    self.default_spk,
                    stream=False,
                    speed=1.0
                ):
                    if 'tts_speech' in result:
                        audio_chunks.append(result['tts_speech'].cpu().numpy())

            elif hasattr(self.model, 'inference_instruct') and self.default_spk:
                # inference_instruct(tts_text, spk_id, instruct_text, ...)
                for result in self.model.inference_instruct(
                    text,
                    self.default_spk,
                    instruction,
                    stream=False,
                    speed=1.0
                ):
                    if 'tts_speech' in result:
                        audio_chunks.append(result['tts_speech'].cpu().numpy())

            else:
                print("Warning: No suitable inference method found")
                return np.array([], dtype=np.float32)

            if not audio_chunks:
                return np.array([], dtype=np.float32)

            # Concatenate chunks and flatten to 1D
            full_audio = np.concatenate(audio_chunks)

            # Ensure 1D array
            if full_audio.ndim > 1:
                full_audio = full_audio.squeeze()

            return full_audio.astype(np.float32)

        except Exception as e:
            print(f"Error during TTS synthesis: {e}")
            import traceback
            traceback.print_exc()
            return np.array([], dtype=np.float32)

    def _get_voice_instruction(
        self, emotion_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get voice instruction/style based on emotion context.
        """
        base_instruction = self.instruct_text

        if emotion_context is None:
            return base_instruction

        emotion = emotion_context.get("primary_emotion", "neutral")

        # Map emotions to instruction modifiers
        emotion_instructions = {
            "anger": "Speak with a slightly frustrated but controlled tone.",
            "sadness": "Speak with a gentle, empathetic, and comforting tone.",
            "fear": "Speak with a calm and reassuring tone to help ease anxiety.",
            "joy": "Speak with a warm, cheerful, and encouraging tone.",
            "confused": "Speak clearly and patiently, offering helpful guidance.",
            "neutral": base_instruction,
            "surprise": "Speak with engaged interest and curiosity.",
            "disgust": "Speak with a calm, understanding, and non-judgmental tone.",
        }

        return emotion_instructions.get(emotion, base_instruction)

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.model is not None:
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("✓ TTS model unloaded")
