"""Audio utilities for converting between formats."""

import numpy as np
import io


def bytes_to_array(audio_bytes: bytes, sample_rate: int = 16000) -> np.ndarray:
    """Convert audio bytes to numpy array.

    Assumes audio is PCM 16-bit mono.

    Args:
        audio_bytes: Raw PCM audio bytes
        sample_rate: Sample rate (not used for conversion, just metadata)

    Returns:
        Numpy array of audio samples
    """
    if not audio_bytes:
        return np.array([])

    return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0


def array_to_bytes(audio_array: np.ndarray) -> bytes:
    """Convert numpy array to audio bytes.

    Converts float32 array to PCM 16-bit bytes.

    Args:
        audio_array: Numpy array of audio samples (float32)

    Returns:
        Raw PCM audio bytes
    """
    if audio_array.size == 0:
        return b""

    # Clip to [-1, 1] range
    audio_clipped = np.clip(audio_array, -1.0, 1.0)

    # Convert to int16
    audio_int16 = (audio_clipped * 32767).astype(np.int16)

    # Convert to bytes
    return audio_int16.tobytes()
