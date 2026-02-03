"""Emotion Fusion - Combine speech and text emotions."""

import numpy as np
from typing import Dict, Any


class EmotionFusion:
    """Fuse speech and text emotion detections."""

    EMOTION_CATEGORIES = [
        "anger",
        "disgust",
        "fear",
        "joy",
        "neutral",
        "sadness",
        "surprise",
        "confusion",
    ]

    def __init__(self, config: dict):
        """
        Initialize emotion fusion.

        Args:
            config: Configuration dict with fusion settings
        """
        fusion_config = config.get("fusion", {})
        self.speech_weight = fusion_config.get("speech_weight", 0.6)
        self.text_weight = fusion_config.get("text_weight", 0.4)
        self.conflict_strategy = fusion_config.get(
            "conflict_resolution", "speech_dominant"
        )

    def fuse(
        self,
        speech_emotion: Dict[str, Any],
        text_emotion: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Combine speech and text emotions.

        Args:
            speech_emotion: {emotion, confidence, scores}
            text_emotion: {emotion, confidence, scores}

        Returns:
            {primary_emotion, confidence, secondary_emotion, combined_scores, source_agreement}
        """
        # Normalize scores
        speech_scores = self._normalize_scores(speech_emotion.get("scores", {}))
        text_scores = self._normalize_scores(text_emotion.get("scores", {}))

        # Calculate agreement
        agreement = self._calculate_agreement(
            speech_emotion.get("emotion", "neutral"),
            text_emotion.get("emotion", "neutral"),
            speech_scores,
            text_scores,
        )

        # Apply fusion strategy
        if self.conflict_strategy == "speech_dominant":
            combined = self._speech_dominant_fusion(
                speech_emotion, text_emotion, speech_scores, text_scores
            )
        elif self.conflict_strategy == "averaging":
            combined = self._averaging_fusion(speech_scores, text_scores)
        else:
            combined = self._consensus_fusion(
                speech_emotion, text_emotion, speech_scores, text_scores
            )

        # Find primary and secondary emotions
        sorted_emotions = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_emotions[0]
        secondary = sorted_emotions[1] if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.2 else None

        return {
            "primary_emotion": primary[0],
            "confidence": primary[1],
            "secondary_emotion": secondary[0] if secondary else None,
            "combined_scores": combined,
            "source_agreement": agreement,
            "fusion_method": self.conflict_strategy,
        }

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Ensure all emotion categories are present."""
        normalized = {cat: 0.0 for cat in self.EMOTION_CATEGORIES}
        for emotion, score in scores.items():
            emotion_lower = str(emotion).lower()
            if emotion_lower in normalized:
                normalized[emotion_lower] = float(score)
        return normalized

    def _calculate_agreement(
        self,
        speech_emo: str,
        text_emo: str,
        speech_scores: Dict[str, float],
        text_scores: Dict[str, float],
    ) -> float:
        """Calculate agreement between speech and text emotions."""
        # Cosine similarity of score vectors
        speech_vec = np.array([speech_scores[cat] for cat in self.EMOTION_CATEGORIES])
        text_vec = np.array([text_scores[cat] for cat in self.EMOTION_CATEGORIES])

        norm_speech = np.linalg.norm(speech_vec)
        norm_text = np.linalg.norm(text_vec)

        if norm_speech > 0 and norm_text > 0:
            cosine = np.dot(speech_vec, text_vec) / (norm_speech * norm_text)
        else:
            cosine = 0.0

        # Same top emotion?
        same_emotion = 1.0 if speech_emo.lower() == text_emo.lower() else 0.0

        # Weighted combination
        agreement = 0.6 * cosine + 0.4 * same_emotion
        return float(np.clip(agreement, 0.0, 1.0))

    def _speech_dominant_fusion(
        self,
        speech_emotion: Dict[str, Any],
        text_emotion: Dict[str, Any],
        speech_scores: Dict[str, float],
        text_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Prioritize speech if confident, otherwise average."""
        speech_conf = speech_emotion.get("confidence", 0.5)

        if speech_conf > 0.7:
            # High confidence in speech → weight heavily
            alpha = 0.8
        else:
            # Use configured weights
            alpha = self.speech_weight

        combined = {}
        for cat in self.EMOTION_CATEGORIES:
            combined[cat] = (
                alpha * speech_scores.get(cat, 0.0) +
                (1 - alpha) * text_scores.get(cat, 0.0)
            )
        return combined

    def _averaging_fusion(
        self,
        speech_scores: Dict[str, float],
        text_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Simple weighted average."""
        combined = {}
        for cat in self.EMOTION_CATEGORIES:
            combined[cat] = (
                self.speech_weight * speech_scores.get(cat, 0.0) +
                self.text_weight * text_scores.get(cat, 0.0)
            )
        return combined

    def _consensus_fusion(
        self,
        speech_emotion: Dict[str, Any],
        text_emotion: Dict[str, Any],
        speech_scores: Dict[str, float],
        text_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Only return emotion if both sources agree."""
        speech_emo = speech_emotion.get("emotion", "neutral").lower()
        text_emo = text_emotion.get("emotion", "neutral").lower()

        if speech_emo == text_emo:
            # Agreement → use average
            return self._averaging_fusion(speech_scores, text_scores)
        else:
            # Disagreement → default to neutral
            combined = {cat: 0.0 for cat in self.EMOTION_CATEGORIES}
            combined["neutral"] = 1.0
            return combined
