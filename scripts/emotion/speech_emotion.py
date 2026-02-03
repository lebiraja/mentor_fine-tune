"""Speech Emotion Detection using SenseVoice."""

import numpy as np
import torch
from typing import Dict, Any, Optional


class SpeechEmotionDetector:
    """Detect emotions from speech prosody."""

    def __init__(self, config: dict):
        """
        Initialize speech emotion detector.

        Args:
            config: Configuration dict with model_name
        """
        self.model_name = config.get(
            "model_name", "FunAudioLLM/SenseVoice-Small"
        )
        self.model = None
        self.processor = None

    def load(self) -> None:
        """Load speech emotion model."""
        if self.model is not None:
            return

        try:
            print(f"Loading speech emotion model: {self.model_name}")

            # Try to import and load SenseVoice
            try:
                from transformers import AutoModel, AutoProcessor

                device = "cuda:0" if torch.cuda.is_available() else "cpu"

                self.processor = AutoProcessor.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                ).to(device)

                print("✓ Speech emotion model loaded")

            except Exception as e:
                # Fallback: Use simple feature-based emotion detection
                print(
                    f"Advanced emotion models not available ({type(e).__name__})"
                )
                print("Using simple feature-based emotion detection fallback")
                self.model = "feature_based_fallback"

        except Exception as e:
            print(f"Error loading speech emotion model: {e}")
            # Still usable with fallback
            self.model = "feature_based_fallback"

    def _load_speechbrain(self) -> None:
        """Load SpeechBrain emotion model as fallback."""
        try:
            from speechbrain.pretrained import EncoderClassifier

            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"},
            )
            print("✓ SpeechBrain emotion model loaded")
        except Exception as e:
            print(f"Error loading SpeechBrain: {e}")
            raise

    def detect_emotion(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Detect emotion from audio.

        Args:
            audio: Audio array (numpy)
            sample_rate: Sample rate in Hz

        Returns:
            Dict with emotion, confidence, and scores
        """
        if self.model is None:
            self.load()

        try:
            # Handle empty audio
            if len(audio) == 0:
                return self._neutral_response()

            # Normalize audio
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val

            # Detect emotion based on loaded model type
            if self.model == "feature_based_fallback":
                # Simple feature-based detection
                return self._detect_emotion_features(audio, sample_rate)
            elif hasattr(self.model, "from_hparams"):
                # SpeechBrain model
                return self._detect_emotion_speechbrain(audio, sample_rate)
            else:
                # SenseVoice model
                return self._detect_emotion_sensevoice(audio, sample_rate)

        except Exception as e:
            print(f"Error detecting speech emotion: {e}")
            return self._neutral_response()

    def _detect_emotion_sensevoice(
        self, audio: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """Detect emotion using SenseVoice."""
        import torch

        try:
            # Prepare input
            inputs = self.processor(
                audio, sampling_rate=sample_rate, return_tensors="pt"
            )

            if torch.cuda.is_available():
                for key in inputs:
                    inputs[key] = inputs[key].to("cuda")

            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Parse outputs
            # SenseVoice returns emotion, language, and event info
            if hasattr(outputs, "emotion"):
                emotion = outputs.emotion
            else:
                # Fallback: assume basic emotion classification
                emotion = "neutral"
                confidence = 0.5

            return {
                "emotion": emotion,
                "confidence": 0.7,
                "scores": self._get_emotion_scores(emotion),
            }

        except Exception as e:
            print(f"Error in SenseVoice detection: {e}")
            return self._neutral_response()

    def _detect_emotion_speechbrain(
        self, audio: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """Detect emotion using SpeechBrain wav2vec2-IEMOCAP."""
        import torch
        import torchaudio

        try:
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio).float()

            # Resample if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(
                    sample_rate, 16000
                )
                audio_tensor = resampler(audio_tensor)

            # Unsqueeze for batch dimension
            audio_tensor = audio_tensor.unsqueeze(0)

            if torch.cuda.is_available():
                audio_tensor = audio_tensor.to("cuda")

            # Get prediction
            with torch.no_grad():
                outputs = self.model.classify_batch(audio_tensor)

            # Parse outputs
            # SpeechBrain returns logits, take argmax
            predictions = outputs[0]
            emotion_idx = torch.argmax(predictions).item()

            emotions = [
                "anger",
                "sadness",
                "fear",
                "joy",
                "neutral",
                "confusion",
            ]
            emotion = emotions[emotion_idx] if emotion_idx < len(emotions) else "neutral"

            # Get confidence (softmax of predictions)
            probs = torch.nn.functional.softmax(predictions, dim=-1)
            confidence = float(probs[emotion_idx].cpu())

            return {
                "emotion": emotion,
                "confidence": confidence,
                "scores": self._get_emotion_scores(emotion, confidence),
            }

        except Exception as e:
            print(f"Error in SpeechBrain detection: {e}")
            return self._neutral_response()

    def _get_emotion_scores(
        self, emotion: str, confidence: float = 0.7
    ) -> Dict[str, float]:
        """Create emotion scores dict."""
        emotions = [
            "anger",
            "sadness",
            "fear",
            "joy",
            "neutral",
            "confusion",
            "surprise",
            "disgust",
        ]
        scores = {e: 0.0 for e in emotions}

        if emotion in scores:
            scores[emotion] = confidence
        else:
            scores["neutral"] = confidence

        return scores

    def _detect_emotion_features(
        self, audio: np.ndarray, sample_rate: int
    ) -> Dict[str, Any]:
        """
        Simple feature-based emotion detection.
        Uses energy and spectral features as proxies.
        """
        try:
            # Energy (RMS)
            rms = np.sqrt(np.mean(audio**2))

            # Simple emotion heuristics based on energy
            if rms > 0.1:
                emotion = "anger"
                confidence = 0.65
            elif rms > 0.05:
                emotion = "joy"
                confidence = 0.60
            elif rms < 0.02:
                emotion = "sadness"
                confidence = 0.60
            else:
                emotion = "neutral"
                confidence = 0.70

            return {
                "emotion": emotion,
                "confidence": confidence,
                "scores": self._get_emotion_scores(emotion, confidence),
            }

        except Exception as e:
            print(f"Error in feature-based detection: {e}")
            return self._neutral_response()

    def _neutral_response(self) -> Dict[str, Any]:
        """Return neutral emotion response."""
        return {
            "emotion": "neutral",
            "confidence": 0.5,
            "scores": {e: 0.0 for e in [
                "anger", "sadness", "fear", "joy", "neutral",
                "confusion", "surprise", "disgust"
            ]},
        }

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.model is not None:
            self.model = None
            self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
