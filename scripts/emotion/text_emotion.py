"""Text Emotion/Sentiment Detection using DistilRoBERTa."""

import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from typing import Dict, Any


class TextEmotionDetector:
    """Detect emotions from text using DistilRoBERTa."""

    def __init__(self, config: dict):
        """
        Initialize text emotion detector.

        Args:
            config: Configuration dict with model_name
        """
        self.model_name = config.get(
            "model_name",
            "j-hartmann/emotion-english-distilroberta-base"
        )
        self.pipe = None
        self.model = None
        self.tokenizer = None

    def load(self) -> None:
        """Load text emotion model."""
        if self.pipe is not None:
            return

        try:
            print(f"Loading text emotion model: {self.model_name}")

            device = 0 if torch.cuda.is_available() else -1

            # Load via pipeline
            self.pipe = pipeline(
                "text-classification",
                model=self.model_name,
                device=device,
                top_k=None,  # Return scores for all emotions
            )

            # Also load model and tokenizer for direct access
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )

            if torch.cuda.is_available():
                self.model = self.model.to("cuda")

            print("✓ Text emotion model loaded")

        except Exception as e:
            print(f"Error loading text emotion model: {e}")
            raise

    def detect_emotion(self, text: str) -> Dict[str, Any]:
        """
        Detect emotion from text.

        Args:
            text: Input text

        Returns:
            Dict with emotion, confidence, and scores
        """
        if self.pipe is None:
            self.load()

        try:
            # Handle empty text
            if not text or len(text.strip()) == 0:
                return self._neutral_response()

            # Truncate if too long (DistilRoBERTa has 512 token limit)
            tokens = self.tokenizer.encode(text, truncation=False)
            if len(tokens) > 512:
                text = self.tokenizer.decode(tokens[:512])

            # Classify
            results = self.pipe(text)

            # Parse results - handle nested list format from top_k=None
            if isinstance(results, list):
                if len(results) == 0:
                    return self._neutral_response()

                # Unwrap nested list if present (from top_k=None)
                if isinstance(results[0], list):
                    results = results[0]
                    if len(results) == 0:
                        return self._neutral_response()

                # Now results should be [{'label': ..., 'score': ...}, ...]
                if isinstance(results[0], dict) and 'label' in results[0]:
                    top_emotion = results[0]
                    emotion = top_emotion["label"].lower()
                    confidence = float(top_emotion["score"])
                    scores = {r["label"].lower(): float(r["score"]) for r in results}
                    return {
                        "emotion": emotion,
                        "confidence": confidence,
                        "scores": scores,
                    }

            # If we get here, use neutral
            return self._neutral_response()

        except Exception as e:
            print(f"Error detecting text emotion: {e}")
            return self._neutral_response()

    def _get_all_emotion_scores(
        self, emotion: str, confidence: float
    ) -> Dict[str, float]:
        """Create emotion scores dict with all emotions."""
        emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
        scores = {e: 0.0 for e in emotions}
        if emotion in scores:
            scores[emotion] = confidence
        return scores

    def _neutral_response(self) -> Dict[str, Any]:
        """Return neutral emotion response."""
        return {
            "emotion": "neutral",
            "confidence": 0.5,
            "scores": {
                "anger": 0.0,
                "disgust": 0.0,
                "fear": 0.0,
                "joy": 0.1,
                "neutral": 0.8,
                "sadness": 0.1,
                "surprise": 0.0,
            },
        }

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.pipe is not None:
            self.pipe = None
            self.model = None
            self.tokenizer = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
