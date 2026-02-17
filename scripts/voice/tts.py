"""Text-to-Speech using StyleTTS 2 with emotion control."""

import numpy as np
import torch
from typing import Optional, Dict, Any


class EmotionalTTS:
    """Generate speech from text with emotion control using StyleTTS 2."""

    def __init__(self, config: dict):
        """
        Initialize TTS model.

        Args:
            config: Dictionary with TTS configuration
                - diffusion_steps: Number of diffusion steps (quality vs speed)
                - embedding_scale: Emotional intensity of synthesis
                - alpha: Timbre control parameter
                - beta: Prosody control parameter
        """
        self.diffusion_steps = config.get("diffusion_steps", 5)
        self.embedding_scale = config.get("embedding_scale", 1)
        self.alpha = config.get("alpha", 0.3)
        self.beta = config.get("beta", 0.7)

        self.model = None
        self.sample_rate = 24000  # StyleTTS 2 native sample rate

    def load(self) -> None:
        """Load TTS model to GPU."""
        if self.model is not None:
            return

        try:
            print("Loading TTS model: StyleTTS 2 (LibriTTS)")
            from styletts2 import tts

            self.model = tts.StyleTTS2()
            print(f"StyleTTS 2 loaded (sample_rate={self.sample_rate})")

        except Exception as e:
            print(f"Error loading StyleTTS 2 model: {e}")
            import traceback
            traceback.print_exc()
            raise

    def synthesize(
        self, text: str, emotion_context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Generate speech from text using StyleTTS 2.

        StyleTTS 2 infers prosody and emotion from the text content itself.
        The embedding_scale parameter controls emotional intensity.

        Args:
            text: Text to synthesize
            emotion_context: Optional emotion context (used to adjust embedding_scale)

        Returns:
            Audio array (1D numpy array of float32)
        """
        if self.model is None:
            self.load()

        if not text or len(text.strip()) == 0:
            return np.array([], dtype=np.float32)

        try:
            # Adjust embedding scale based on emotion intensity
            embedding_scale = self._get_embedding_scale(emotion_context)

            # StyleTTS 2 inference() handles up to ~420 chars,
            # long_inference() for longer text
            if len(text) > 400:
                audio = self.model.long_inference(
                    text,
                    output_sample_rate=self.sample_rate,
                    alpha=self.alpha,
                    beta=self.beta,
                    diffusion_steps=self.diffusion_steps,
                    embedding_scale=embedding_scale,
                )
            else:
                audio = self.model.inference(
                    text,
                    output_sample_rate=self.sample_rate,
                    alpha=self.alpha,
                    beta=self.beta,
                    diffusion_steps=self.diffusion_steps,
                    embedding_scale=embedding_scale,
                )

            if audio is None or len(audio) == 0:
                return np.array([], dtype=np.float32)

            # Ensure 1D float32 array
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()

            if audio.ndim > 1:
                audio = audio.squeeze()

            return audio.astype(np.float32)

        except Exception as e:
            print(f"Error during TTS synthesis: {e}")
            import traceback
            traceback.print_exc()
            return np.array([], dtype=np.float32)

    def _get_embedding_scale(
        self, emotion_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Get embedding scale based on emotion context.

        Higher embedding_scale = more emotionally expressive speech.
        """
        base_scale = self.embedding_scale

        if emotion_context is None:
            return base_scale

        emotion = emotion_context.get("primary_emotion", "neutral")

        # Emotions that benefit from higher expressiveness
        emotion_scales = {
            "anger": 1.5,
            "sadness": 1.2,
            "fear": 1.2,
            "joy": 1.5,
            "confused": 1.0,
            "neutral": 1.0,
            "surprise": 1.3,
            "disgust": 1.2,
        }

        return emotion_scales.get(emotion, base_scale)

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.model is not None:
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("TTS model unloaded")
