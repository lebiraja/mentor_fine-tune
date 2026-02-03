"""GPU Memory Manager - Handle model loading/unloading to fit in 6GB VRAM."""

import torch
import gc
from pathlib import Path
from typing import Optional, Tuple


class ModelManager:
    """Manage loading/unloading of models to fit in 6GB VRAM."""

    def __init__(self, config: dict):
        """
        Initialize model manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_vram_gb = config.get("memory", {}).get("max_vram_gb", 5.5)

        # Persistent models (loaded once at startup)
        self.llm_model = None
        self.llm_tokenizer = None
        self.vad_model = None

        # Transient models (load/unload as needed)
        self.stt_pipe = None
        self.speech_emotion_model = None
        self.text_emotion_model = None
        self.text_emotion_tokenizer = None
        self.tts_model = None
        self.tts_tokenizer = None

    def load_llm_persistent(self, model_path: Path) -> Tuple:
        """
        Load ClarityMentor LLM - keep in memory.

        Args:
            model_path: Path to model

        Returns:
            (model, tokenizer) tuple
        """
        if self.llm_model is None:
            from llm_core import load_claritymentor_model

            print("Loading ClarityMentor (persistent)...")
            self.llm_model, self.llm_tokenizer = load_claritymentor_model(
                model_path
            )
            self._check_vram()
            print(f"✓ LLM loaded. VRAM: {self._get_vram_usage():.2f}GB")

        return self.llm_model, self.llm_tokenizer

    def load_vad_persistent(self) -> None:
        """Load VAD model - keep in memory (tiny)."""
        if self.vad_model is None:
            print("Loading Silero VAD (persistent)...")
            try:
                self.vad_model, _ = torch.hub.load(
                    repo_or_dir="snakers4/silero-vad",
                    model="silero_vad",
                    force_reload=False,
                    onnx=False,
                )
                self.vad_model.eval()
                if torch.cuda.is_available():
                    self.vad_model = self.vad_model.to("cuda")
                print("✓ VAD loaded. VRAM: {:.2f}GB".format(self._get_vram_usage()))
            except Exception as e:
                print(f"Warning: Could not load Silero VAD: {e}")

    def load_stt_pipeline(self) -> None:
        """Load STT pipeline (from voice/stt.py)."""
        if self.stt_pipe is None:
            from voice.stt import SpeechToText

            print("Loading STT pipeline...")
            stt = SpeechToText(self.config["models"]["stt"])
            self.stt_pipe = stt
            self._check_vram()
            print(f"✓ STT loaded. VRAM: {self._get_vram_usage():.2f}GB")

    def unload_stt_pipeline(self) -> None:
        """Unload STT pipeline, free VRAM."""
        if self.stt_pipe is not None:
            print("Unloading STT pipeline...")
            self.stt_pipe.unload()
            self.stt_pipe = None
            self._clear_cuda_cache()
            print(f"✓ STT unloaded. VRAM: {self._get_vram_usage():.2f}GB")

    def load_speech_emotion(self):
        """Load speech emotion model."""
        if self.speech_emotion_model is None:
            from emotion.speech_emotion import SpeechEmotionDetector

            print("Loading speech emotion model...")
            detector = SpeechEmotionDetector(
                self.config["models"]["speech_emotion"]
            )
            detector.load()
            self.speech_emotion_model = detector
            self._check_vram()
            print(f"✓ Speech emotion loaded. VRAM: {self._get_vram_usage():.2f}GB")

    def unload_speech_emotion(self) -> None:
        """Unload speech emotion model."""
        if self.speech_emotion_model is not None:
            print("Unloading speech emotion...")
            self.speech_emotion_model.unload()
            self.speech_emotion_model = None
            self._clear_cuda_cache()
            print(f"✓ Speech emotion unloaded. VRAM: {self._get_vram_usage():.2f}GB")

    def load_text_emotion(self) -> None:
        """Load text emotion model."""
        if self.text_emotion_model is None:
            from emotion.text_emotion import TextEmotionDetector

            print("Loading text emotion model...")
            detector = TextEmotionDetector(self.config["models"]["text_emotion"])
            detector.load()
            self.text_emotion_model = detector
            self._check_vram()
            print(f"✓ Text emotion loaded. VRAM: {self._get_vram_usage():.2f}GB")

    def unload_text_emotion(self) -> None:
        """Unload text emotion model."""
        if self.text_emotion_model is not None:
            print("Unloading text emotion...")
            self.text_emotion_model.unload()
            self.text_emotion_model = None
            self._clear_cuda_cache()
            print(f"✓ Text emotion unloaded. VRAM: {self._get_vram_usage():.2f}GB")

    def load_tts(self) -> None:
        """Load TTS model."""
        if self.tts_model is None:
            from voice.tts import EmotionalTTS

            print("Loading TTS model...")
            tts = EmotionalTTS(self.config["models"]["tts"])
            tts.load()
            self.tts_model = tts
            self._check_vram()
            print(f"✓ TTS loaded. VRAM: {self._get_vram_usage():.2f}GB")

    def unload_tts(self) -> None:
        """Unload TTS model."""
        if self.tts_model is not None:
            print("Unloading TTS...")
            self.tts_model.unload()
            self.tts_model = None
            self._clear_cuda_cache()
            print(f"✓ TTS unloaded. VRAM: {self._get_vram_usage():.2f}GB")

    def _clear_cuda_cache(self) -> None:
        """Aggressively clear CUDA cache."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def _get_vram_usage(self) -> float:
        """Get current VRAM usage in GB."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024**3)
        return 0.0

    def _check_vram(self) -> None:
        """Check if VRAM exceeds limit."""
        usage = self._get_vram_usage()
        if usage > self.max_vram_gb:
            print(f"Warning: VRAM usage ({usage:.2f}GB) exceeds limit ({self.max_vram_gb}GB)")
