"""Backend core utilities."""

from .exceptions import (
    ServiceError,
    ModelLoadError,
    TranscriptionError,
    EmotionDetectionError,
    TTSError,
    LLMError,
    SessionError,
)
from .audio_utils import bytes_to_array, array_to_bytes

__all__ = [
    "ServiceError",
    "ModelLoadError",
    "TranscriptionError",
    "EmotionDetectionError",
    "TTSError",
    "LLMError",
    "SessionError",
    "bytes_to_array",
    "array_to_bytes",
]
