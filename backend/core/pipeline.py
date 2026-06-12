"""Conversation pipeline — per-connection state machine with barge-in.

States: LISTENING -> TRANSCRIBING -> GENERATING/SPEAKING -> LISTENING
Audio frames keep flowing through VAD in every state; speech during
GENERATING/SPEAKING cancels the in-flight turn (barge-in).
"""

import asyncio
import time
from typing import Any, Awaitable, Callable

import numpy as np

from backend.core.segmenter import SentenceSegmenter, clean_for_speech

SendJSON = Callable[[dict[str, Any]], Awaitable[None]]
SendBytes = Callable[[bytes], Awaitable[None]]


class LatencyStats:
    """Rolling per-stage latency, surfaced via /api/health."""

    def __init__(self) -> None:
        self.last: dict[str, float] = {}

    def record(self, stage: str, ms: float) -> None:
        self.last[stage] = round(ms, 1)


class ConversationPipeline:
    def __init__(
        self,
        *,
        stt,
        tts,
        llm,
        turn_detector,
        db,
        system_prompt: str,
        context_tokens: int,
        send_json: SendJSON,
        send_bytes: SendBytes,
        stats: LatencyStats,
    ):
        self.stt = stt
        self.tts = tts
        self.llm = llm
        self.turns = turn_detector
        self.db = db
        self.system_prompt = system_prompt
        self.context_tokens = context_tokens
        self.send_json = send_json
        self.send_bytes = send_bytes
        self.stats = stats

        self.session_id: str | None = None
        self.muted = False
        self._turn_task: asyncio.Task | None = None

    # ------------------------------------------------------------------ input

    async def set_session(self, session_id: str | None) -> str:
        if session_id and await self.db.session_exists(session_id):
            self.session_id = session_id
        else:
            self.session_id = await self.db.create_session()
        return self.session_id

    async def handle_audio(self, pcm_bytes: bytes) -> None:
        """Continuous 16 kHz int16 mono frames from the client mic."""
        if self.muted:
            return
        pcm = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        for event in self.turns.process(pcm):
            if event.kind == "speech_start":
                await self._barge_in()
                await self.send_json({"type": "state", "state": "listening"})
            elif event.kind == "utterance":
                self._start_turn(audio=event.audio)

    async def handle_text(self, text: str) -> None:
        """Typed message — same pipeline, skips STT."""
        text = text.strip()
        if not text:
            return
        await self._barge_in()
        self._start_turn(text=text)

    async def shutdown(self) -> None:
        await self._cancel_turn()

    # ------------------------------------------------------------------- turn

    def _start_turn(self, audio: np.ndarray | None = None, text: str | None = None) -> None:
        self._turn_task = asyncio.create_task(self._run_turn(audio, text))

    async def _barge_in(self) -> None:
        if self._turn_task and not self._turn_task.done():
            await self._cancel_turn()
            await self.send_json({"type": "interrupted"})

    async def _cancel_turn(self) -> None:
        if self._turn_task and not self._turn_task.done():
            self._turn_task.cancel()
            try:
                await self._turn_task
            except asyncio.CancelledError:
                pass
        self._turn_task = None

    async def _run_turn(self, audio: np.ndarray | None, text: str | None) -> None:
        assert self.session_id is not None
        loop = asyncio.get_running_loop()
        assistant_text = ""
        detected_lang = "en"
        try:
            # 1. Transcribe (voice turns only)
            if text is None:
                await self.send_json({"type": "state", "state": "transcribing"})
                t0 = time.perf_counter()
                stt_result = await loop.run_in_executor(None, self.stt.transcribe, audio)
                self.stats.record("stt_ms", (time.perf_counter() - t0) * 1000)
                text = stt_result.text
                detected_lang = stt_result.language
                if not text:
                    await self.send_json({"type": "state", "state": "listening"})
                    return
                await self.send_json({
                    "type": "user_transcript",
                    "text": text,
                    "language": detected_lang,
                    "language_probability": stt_result.language_probability,
                })

            await self.db.add_message(self.session_id, "user", text)

            # 2. Build windowed history
            messages = await self._windowed_messages()

            # 3. Stream LLM -> segment -> TTS, all overlapped
            await self.send_json({"type": "state", "state": "generating"})
            segmenter = SentenceSegmenter()
            t_first_token: float | None = None
            t_first_audio: float | None = None
            t0 = time.perf_counter()
            speaking = False

            async def speak(sentence: str) -> None:
                nonlocal speaking, t_first_audio
                spoken = clean_for_speech(sentence)
                if not spoken:
                    return
                pcm = await loop.run_in_executor(
                    None, self.tts.synthesize, spoken, detected_lang
                )
                if not pcm:
                    return
                if not speaking:
                    speaking = True
                    await self.send_json({"type": "state", "state": "speaking"})
                if t_first_audio is None:
                    t_first_audio = time.perf_counter()
                    self.stats.record("first_audio_ms", (t_first_audio - t0) * 1000)
                await self.send_bytes(pcm)

            async for delta in self.llm.stream_chat(messages):
                if t_first_token is None:
                    t_first_token = time.perf_counter()
                    self.stats.record("llm_ttft_ms", (t_first_token - t0) * 1000)
                assistant_text += delta
                await self.send_json({"type": "assistant_delta", "text": delta})
                for sentence in segmenter.feed(delta):
                    await speak(sentence)

            for sentence in segmenter.flush():
                await speak(sentence)

            await self.send_json({"type": "assistant_done", "text": assistant_text})
            await self.db.add_message(self.session_id, "assistant", assistant_text)
            await self.send_json({"type": "state", "state": "listening"})

        except asyncio.CancelledError:
            # Barge-in or disconnect: persist whatever was said so far
            if assistant_text:
                await self.db.add_message(self.session_id, "assistant", assistant_text)
            raise
        except Exception as e:
            await self.send_json({"type": "error", "message": "Something went wrong, try again."})
            print(f"[pipeline] turn failed: {type(e).__name__}: {e}")
            await self.send_json({"type": "state", "state": "listening"})

    async def _windowed_messages(self) -> list[dict[str, str]]:
        """System prompt + as many recent turns as fit the context budget.

        Uses a ~4 chars/token heuristic; llama.cpp enforces the hard limit.
        """
        budget_chars = (self.context_tokens - self.llm.max_tokens) * 4
        budget_chars -= len(self.system_prompt)

        history = await self.db.get_messages(self.session_id)
        kept: list[dict[str, str]] = []
        used = 0
        for msg in reversed(history):
            cost = len(msg["content"])
            if used + cost > budget_chars and kept:
                break
            kept.append({"role": msg["role"], "content": msg["content"]})
            used += cost
        kept.reverse()

        return [{"role": "system", "content": self.system_prompt}, *kept]
