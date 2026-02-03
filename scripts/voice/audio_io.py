"""Audio I/O - Microphone capture and speaker playback."""

import numpy as np
import sounddevice as sd
from typing import Optional, Tuple


class AudioIO:
    """Handle audio input from microphone and output to speakers."""

    def __init__(self, config: dict):
        """
        Initialize AudioIO.

        Args:
            config: Dictionary with audio configuration
                - sample_rate: Sampling rate in Hz
                - channels: Number of channels (1 for mono)
                - input_device: Input device ID or None for default
                - output_device: Output device ID or None for default
        """
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.input_device = config.get("input_device")
        self.output_device = config.get("output_device")

    def record_chunk(self, duration: float) -> np.ndarray:
        """
        Record audio chunk from microphone.

        Args:
            duration: Duration in seconds

        Returns:
            numpy array of audio samples
        """
        num_samples = int(self.sample_rate * duration)
        audio = sd.rec(
            num_samples,
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.input_device,
            dtype=np.float32,
        )
        sd.wait()
        return audio.squeeze()

    def record_until_silence(
        self, vad_detector, max_duration: float = 60.0
    ) -> Tuple[np.ndarray, float]:
        """
        Record audio until silence is detected.

        Args:
            vad_detector: VoiceActivityDetector instance
            max_duration: Maximum recording duration in seconds

        Returns:
            (audio_array, duration) tuple
        """
        chunk_duration = 0.5
        audio_chunks = []
        silent_chunks = 0
        max_silent_chunks = int(vad_detector.min_silence_duration / chunk_duration)
        recording_started = False

        print("Listening... speak now")

        try:
            while len(audio_chunks) * chunk_duration < max_duration:
                chunk = self.record_chunk(chunk_duration)
                audio_chunks.append(chunk)

                # Check for speech
                is_speech = vad_detector.is_speech(chunk)

                if is_speech:
                    recording_started = True
                    silent_chunks = 0
                elif recording_started:
                    silent_chunks += 1
                    # Stop if silence detected after speech started
                    if silent_chunks >= max_silent_chunks:
                        break

        except KeyboardInterrupt:
            print("\nRecording cancelled by user")
            return np.array([]), 0.0

        if audio_chunks:
            audio = np.concatenate(audio_chunks)
            duration = len(audio) / self.sample_rate
            return audio, duration
        else:
            return np.array([]), 0.0

    def play_audio(
        self, audio: np.ndarray, sample_rate: Optional[int] = None
    ) -> None:
        """
        Play audio through speakers.

        Args:
            audio: Audio array to play
            sample_rate: Sample rate of audio (uses self.sample_rate if None)
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        if len(audio) == 0:
            return

        # Normalize audio if it's out of range
        max_val = np.max(np.abs(audio))
        if max_val > 1.0:
            audio = audio / max_val

        try:
            sd.play(audio, samplerate=sample_rate, device=self.output_device)
            sd.wait()
        except Exception as e:
            print(f"Error playing audio: {e}")

    def get_device_info(self) -> None:
        """Print available audio devices."""
        print("\nAvailable audio devices:")
        print(sd.query_devices())
