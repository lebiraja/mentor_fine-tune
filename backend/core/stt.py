"""Speech-to-text: Parakeet TDT 0.6B v3 int8 ONNX via onnx-asr (CPU)."""

from pathlib import Path

import numpy as np


class ParakeetSTT:
    def __init__(self, model_dir: Path):
        import onnx_asr

        self.model = onnx_asr.load_model(
            "nemo-parakeet-tdt-0.6b-v3", str(model_dir), quantization="int8"
        )

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Blocking — call from a thread executor. `audio` is float32 mono."""
        if audio.size == 0:
            return ""
        text = self.model.recognize(audio.astype(np.float32), sample_rate=sample_rate)
        return (text or "").strip()
