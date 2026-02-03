"""Prompt Augmenter - Modify system prompt based on emotion context."""

import yaml
from pathlib import Path
from typing import Dict, Any


class PromptAugmenter:
    """Modify system prompt based on detected emotion."""

    def __init__(self, emotion_config_path: Path):
        """
        Initialize prompt augmenter.

        Args:
            emotion_config_path: Path to emotion_prompts.yaml
        """
        self.config_path = Path(emotion_config_path)
        self.emotion_configs = self._load_emotion_config()

    def _load_emotion_config(self) -> Dict[str, Any]:
        """Load emotion configuration from YAML."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: {self.config_path} not found. Using default configs.")
            return self._get_default_configs()
        except Exception as e:
            print(f"Error loading emotion config: {e}")
            return self._get_default_configs()

    def augment_system_prompt(
        self, base_prompt: str, emotion_context: Dict[str, Any]
    ) -> str:
        """
        Augment system prompt based on detected emotion.

        Args:
            base_prompt: Original system prompt
            emotion_context: Output from EmotionFusion

        Returns:
            Augmented prompt
        """
        # Check confidence threshold
        confidence = emotion_context.get("confidence", 0.0)
        thresholds = self.emotion_configs.get("thresholds", {})
        high_conf_threshold = thresholds.get("high_confidence", 0.7)

        if confidence < 0.5:
            # Not confident enough
            return base_prompt

        emotion = emotion_context.get("primary_emotion", "neutral")

        # Get emotion-specific addition
        emotions_config = self.emotion_configs.get("emotions", {})
        emotion_config = emotions_config.get(emotion, {})
        addition = emotion_config.get("prompt_addition", "")

        if not addition or len(addition.strip()) == 0:
            # No modification for this emotion
            return base_prompt

        # Insert emotion context after philosophical foundation
        # but before the response structure
        augmented = f"""{base_prompt}

---

EMOTION CONTEXT:
{addition}

---
"""
        return augmented

    def get_voice_description(
        self, emotion_context: Dict[str, Any]
    ) -> str:
        """
        Get voice description for TTS based on emotion.

        Args:
            emotion_context: Output from EmotionFusion

        Returns:
            Voice description string
        """
        confidence = emotion_context.get("confidence", 0.0)

        if confidence < 0.5:
            # Not confident, use neutral
            emotion = "neutral"
        else:
            emotion = emotion_context.get("primary_emotion", "neutral")

        emotions_config = self.emotion_configs.get("emotions", {})
        emotion_config = emotions_config.get(emotion, {})
        voice_desc = emotion_config.get(
            "tts_description",
            "A calm, thoughtful voice speaks clearly with measured pace"
        )

        return voice_desc

    def _get_default_configs(self) -> Dict[str, Any]:
        """Return default emotion configurations."""
        return {
            "emotions": {
                "anger": {
                    "prompt_addition": (
                        "The user is expressing anger or frustration. "
                        "Acknowledge their frustration directly without dismissing it."
                    ),
                    "tts_description": "A calm, steady voice that is grounding",
                },
                "sadness": {
                    "prompt_addition": (
                        "The user is experiencing sadness. "
                        "Show genuine understanding of their pain. Be gentle."
                    ),
                    "tts_description": "A warm, gentle voice with compassion",
                },
                "fear": {
                    "prompt_addition": (
                        "The user is expressing fear or anxiety. "
                        "Ground them in reality and help them identify what they can control."
                    ),
                    "tts_description": "A calm, reassuring voice that is stable",
                },
                "joy": {
                    "prompt_addition": (
                        "The user seems happy or excited. "
                        "Engage warmly while deepening their reflection."
                    ),
                    "tts_description": "A warm, engaged voice with enthusiasm",
                },
                "neutral": {
                    "prompt_addition": "",
                    "tts_description": "A calm, thoughtful voice speaks clearly",
                },
            },
            "thresholds": {"high_confidence": 0.7, "low_confidence": 0.3},
            "fusion": {
                "speech_weight": 0.6,
                "text_weight": 0.4,
                "conflict_resolution": "speech_dominant",
            },
        }
