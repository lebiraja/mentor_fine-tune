"""Voice Activity Detection using Silero VAD."""

import torch
import numpy as np
from typing import Optional


class VoiceActivityDetector:
    """Detect voice activity in audio using Silero VAD."""

    def __init__(self, config: dict):
        """
        Initialize VAD detector.

        Args:
            config: Dictionary with VAD configuration
                - threshold: Voice probability threshold (0-1)
                - min_speech_duration: Minimum speech duration in seconds
                - min_silence_duration: Minimum silence to consider speech ended
                - padding_duration: Padding before/after speech
        """
        self.threshold = config.get("threshold", 0.5)
        self.min_speech_duration = config.get("min_speech_duration", 0.5)
        self.min_silence_duration = config.get("min_silence_duration", 0.8)
        self.padding_duration = config.get("padding_duration", 0.3)

        # Load Silero VAD model
        self.model = None
        self.sample_rate = None
        self._load_model()

    def _load_model(self) -> None:
        """Load Silero VAD model from PyTorch Hub."""
        try:
            self.model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self.model.eval()
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
            print("✓ Silero VAD loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load Silero VAD: {e}")
            print("Falling back to simple energy-based detection")
            self.model = None

    def is_speech(self, audio: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Detect if audio chunk contains speech.

        Args:
            audio: Audio samples (numpy array)
            sample_rate: Sample rate of audio

        Returns:
            True if speech detected, False otherwise
        """
        if self.model is not None:
            try:
                # Silero VAD requires 512 samples at 16000Hz (32ms chunks)
                # Resample if necessary
                if len(audio) != 512 or sample_rate != 16000:
                    # Resample to 16000Hz and take only 512 samples
                    if sample_rate != 16000:
                        factor = sample_rate / 16000
                        resampled = audio[::int(factor)] if factor > 1 else np.repeat(audio, int(1/factor))
                    else:
                        resampled = audio

                    # Take last 512 samples or pad with zeros
                    if len(resampled) >= 512:
                        audio_chunk = resampled[-512:].astype(np.float32)
                    else:
                        audio_chunk = np.pad(resampled, (512 - len(resampled), 0), mode='constant').astype(np.float32)
                else:
                    audio_chunk = audio.astype(np.float32)

                # Convert to torch tensor
                audio_tensor = torch.from_numpy(audio_chunk).float()
                if torch.cuda.is_available():
                    audio_tensor = audio_tensor.to("cuda")

                # Get VAD confidence (Silero VAD expects 16000Hz, 512 samples)
                with torch.no_grad():
                    confidence = self.model(audio_tensor, 16000).item()

                return confidence > self.threshold

            except Exception as e:
                print(f"VAD error: {e}, falling back to energy detection")
                return self._energy_based_detection(audio)
        else:
            return self._energy_based_detection(audio)

    def _energy_based_detection(self, audio: np.ndarray) -> bool:
        """
        Fallback: Detect speech based on energy/RMS.

        Args:
            audio: Audio samples

        Returns:
            True if energy indicates speech
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio**2))

        # Simple threshold (adjust as needed)
        energy_threshold = 0.02
        return rms > energy_threshold

    def detect_speech_segments(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> list:
        """
        Detect speech segments in audio.

        Args:
            audio: Full audio array
            sample_rate: Sample rate

        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        chunk_size = int(sample_rate * 0.1)  # 100ms chunks
        num_chunks = len(audio) // chunk_size

        speech_detected = False
        segment_start = 0
        segments = []

        for i in range(num_chunks):
            chunk = audio[i * chunk_size : (i + 1) * chunk_size]
            is_speech = self.is_speech(chunk, sample_rate)

            if is_speech and not speech_detected:
                # Speech started
                speech_detected = True
                segment_start = i * chunk_size / sample_rate

            elif not is_speech and speech_detected:
                # Speech ended
                speech_detected = False
                segment_end = i * chunk_size / sample_rate
                segments.append((segment_start, segment_end))

        # Handle case where speech extends to end of audio
        if speech_detected:
            segment_end = len(audio) / sample_rate
            segments.append((segment_start, segment_end))

        return segments
