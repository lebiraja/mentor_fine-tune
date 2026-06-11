"""Silero VAD v5 via raw onnxruntime (no torch) + streaming turn detection."""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import onnxruntime as ort

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512  # 32 ms — the only window size Silero v5 supports at 16 kHz


class SileroVAD:
    """Thin wrapper around the Silero v5 ONNX graph."""

    def __init__(self, model_path: Path):
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(model_path), opts, providers=["CPUExecutionProvider"]
        )
        self.reset()

    def reset(self) -> None:
        self._state = np.zeros((2, 1, 128), dtype=np.float32)

    def prob(self, frame: np.ndarray) -> float:
        """Speech probability for one 512-sample float32 frame."""
        out, self._state = self.session.run(
            None,
            {
                "input": frame.reshape(1, -1),
                "state": self._state,
                "sr": np.array(SAMPLE_RATE, dtype=np.int64),
            },
        )
        return float(out[0][0])


@dataclass
class TurnEvent:
    kind: str  # "speech_start" | "utterance"
    audio: np.ndarray | None = None


@dataclass
class TurnDetector:
    """Feeds arbitrary PCM chunks, emits speech-start and end-of-turn utterances.

    Keeps a small pre-roll so the first syllable isn't clipped.
    """

    vad: SileroVAD
    threshold: float = 0.5
    min_speech_s: float = 0.25
    end_silence_s: float = 0.6
    pre_roll_s: float = 0.3
    max_utterance_s: float = 60.0

    _buf: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.float32))
    _pre_roll: list = field(default_factory=list)
    _speech: list = field(default_factory=list)
    _in_speech: bool = False
    _speech_frames: int = 0
    _silence_frames: int = 0
    _started_emitted: bool = False

    def reset(self) -> None:
        self.vad.reset()
        self._buf = np.empty(0, dtype=np.float32)
        self._pre_roll.clear()
        self._speech.clear()
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0
        self._started_emitted = False

    def process(self, pcm: np.ndarray) -> list[TurnEvent]:
        """Feed float32 mono 16 kHz samples; returns zero or more events."""
        events: list[TurnEvent] = []
        self._buf = np.concatenate([self._buf, pcm])

        frame_s = FRAME_SAMPLES / SAMPLE_RATE
        min_speech_frames = max(1, int(self.min_speech_s / frame_s))
        end_silence_frames = max(1, int(self.end_silence_s / frame_s))
        pre_roll_frames = max(1, int(self.pre_roll_s / frame_s))
        max_frames = int(self.max_utterance_s / frame_s)

        while len(self._buf) >= FRAME_SAMPLES:
            frame = self._buf[:FRAME_SAMPLES]
            self._buf = self._buf[FRAME_SAMPLES:]
            p = self.vad.prob(frame)

            if not self._in_speech:
                self._pre_roll.append(frame)
                if len(self._pre_roll) > pre_roll_frames:
                    self._pre_roll.pop(0)
                if p >= self.threshold:
                    self._speech_frames += 1
                    if self._speech_frames >= min_speech_frames:
                        self._in_speech = True
                        self._speech = list(self._pre_roll)
                        self._silence_frames = 0
                        if not self._started_emitted:
                            self._started_emitted = True
                            events.append(TurnEvent("speech_start"))
                else:
                    self._speech_frames = 0
            else:
                self._speech.append(frame)
                if p < self.threshold * 0.7:  # hysteresis on the way down
                    self._silence_frames += 1
                else:
                    self._silence_frames = 0

                if (
                    self._silence_frames >= end_silence_frames
                    or len(self._speech) >= max_frames
                ):
                    utterance = np.concatenate(self._speech)
                    events.append(TurnEvent("utterance", audio=utterance))
                    self._in_speech = False
                    self._speech = []
                    self._speech_frames = 0
                    self._silence_frames = 0
                    self._started_emitted = False
                    self._pre_roll.clear()

        return events
