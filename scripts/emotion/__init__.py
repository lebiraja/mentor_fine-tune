"""Emotion detection modules for ClarityMentor."""

from .speech_emotion import SpeechEmotionDetector
from .text_emotion import TextEmotionDetector
from .fusion import EmotionFusion
from .prompt_augmenter import PromptAugmenter

__all__ = [
    "SpeechEmotionDetector",
    "TextEmotionDetector",
    "EmotionFusion",
    "PromptAugmenter",
]
