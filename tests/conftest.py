"""Shared fixtures — fake engines so protocol/pipeline tests run without models."""

import asyncio
from pathlib import Path

import numpy as np
import pytest

from backend.core.pipeline import ConversationPipeline, LatencyStats
from backend.core.stt import STTResult
from backend.db import Database


class FakeSTT:
    def __init__(self, text: str = "hello there", language: str = "en"):
        self.text = text
        self.language = language

    def transcribe(self, audio, sample_rate: int = 16000) -> STTResult:
        return STTResult(
            text=self.text, language=self.language, language_probability=0.99
        )


class FakeTTS:
    """Mimics TTSRouter.synthesize(text, language) -> bytes."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, language: str = "en") -> bytes:
        self.calls.append((text, language))
        # 10 ms of silence per sentence — enough to assert on
        return b"\x00\x00" * 240


class FakeLLM:
    """Streams a canned reply, optionally hanging forever (for barge-in tests)."""

    def __init__(self, deltas=None, hang: bool = False):
        self.deltas = deltas or ["This is the answer. ", "And a second sentence."]
        self.hang = hang
        self.max_tokens = 400

    async def stream_chat(self, messages):
        for d in self.deltas:
            yield d
        if self.hang:
            await asyncio.Event().wait()

    async def healthy(self) -> bool:
        return True


class FakeTurnDetector:
    def process(self, pcm):
        return []

    def reset(self):
        pass


class Collector:
    """Captures everything the pipeline sends to the 'client'."""

    def __init__(self):
        self.json: list[dict] = []
        self.audio: list[bytes] = []

    async def send_json(self, msg):
        self.json.append(msg)

    async def send_bytes(self, data):
        self.audio.append(data)

    def events(self, type_: str) -> list[dict]:
        return [m for m in self.json if m["type"] == type_]


@pytest.fixture
async def db(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def collector():
    return Collector()


@pytest.fixture
def make_pipeline(db, collector):
    def _make(llm=None, stt=None, tts=None) -> ConversationPipeline:
        return ConversationPipeline(
            stt=stt or FakeSTT(),
            tts=tts or FakeTTS(),
            llm=llm or FakeLLM(),
            turn_detector=FakeTurnDetector(),
            db=db,
            system_prompt="You are a test mentor.",
            context_tokens=8192,
            send_json=collector.send_json,
            send_bytes=collector.send_bytes,
            stats=LatencyStats(),
        )

    return _make
