"""Custom exceptions for backend."""


class ServiceError(Exception):
    """Base exception for service errors."""

    pass


class ModelLoadError(ServiceError):
    """Raised when model fails to load."""

    pass


class TranscriptionError(ServiceError):
    """Raised when transcription fails."""

    pass


class EmotionDetectionError(ServiceError):
    """Raised when emotion detection fails."""

    pass


class TTSError(ServiceError):
    """Raised when TTS synthesis fails."""

    pass


class LLMError(ServiceError):
    """Raised when LLM inference fails."""

    pass


class SessionError(ServiceError):
    """Raised when session management fails."""

    pass
