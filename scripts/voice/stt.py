"""Speech-to-Text using DistilWhisper."""

import numpy as np
import torch
from transformers import (
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    pipeline,
)


class SpeechToText:
    """Convert speech audio to text using DistilWhisper."""

    def __init__(self, config: dict):
        """
        Initialize STT model.

        Args:
            config: Dictionary with STT configuration
                - model_name: HuggingFace model ID
                - language: Language code (e.g., 'en')
                - compute_type: 'float16' or 'float32'
        """
        self.model_name = config.get("model_name", "distil-whisper/distil-medium.en")
        self.language = config.get("language", "en")
        self.compute_type = config.get("compute_type", "float16")

        self.pipe = None
        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load DistilWhisper model and processor."""
        try:
            print(f"Loading STT model: {self.model_name}")

            # Determine device and dtype
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = (
                torch.float16 if self.compute_type == "float16" else torch.float32
            )

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_name)

            # Load model
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model = self.model.to(device)

            # Create pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=torch_dtype,
                device=device,
            )

            print("✓ STT model loaded successfully")

        except Exception as e:
            print(f"Error loading STT model: {e}")
            raise

    def transcribe(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio array (numpy)
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text
        """
        if self.pipe is None:
            raise RuntimeError("STT model not loaded")

        try:
            # Handle empty audio
            if len(audio) == 0:
                return ""

            # Normalize audio
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / (max_val + 1e-8)

            # Transcribe
            # Note: English-only models don't accept language/task parameters
            result = self.pipe(
                audio,
                chunk_length_s=30,
                stride_length_s=5,
                return_timestamps=False,
            )

            text = result.get("text", "").strip()
            return text

        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""

    def unload(self) -> None:
        """Unload model to free VRAM."""
        if self.pipe is not None:
            self.pipe = None
            self.model = None
            self.processor = None

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
