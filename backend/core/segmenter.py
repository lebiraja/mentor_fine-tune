"""Incremental sentence segmenter — cuts streaming LLM text into TTS-sized chunks."""

import re

_BOUNDARY = re.compile(r"([.!?…]+[\"')\]]?)(\s|$)")
_ABBREVIATIONS = {"mr.", "mrs.", "ms.", "dr.", "st.", "e.g.", "i.e.", "vs.", "etc."}

MIN_CHUNK_CHARS = 12
MAX_CHUNK_CHARS = 300


class SentenceSegmenter:
    """Feed deltas, get back complete sentences as soon as they exist."""

    def __init__(self) -> None:
        self._pending = ""

    def feed(self, delta: str) -> list[str]:
        self._pending += delta
        out: list[str] = []

        while True:
            match = self._find_boundary(self._pending)
            if match is None:
                break
            sentence, rest = match
            out.append(sentence.strip())
            self._pending = rest

        # Safety valve: never let a chunk grow unbounded (TTS quality + latency)
        if len(self._pending) > MAX_CHUNK_CHARS:
            cut = self._pending.rfind(",", 0, MAX_CHUNK_CHARS)
            if cut == -1:
                cut = self._pending.rfind(" ", 0, MAX_CHUNK_CHARS)
            if cut > MIN_CHUNK_CHARS:
                out.append(self._pending[: cut + 1].strip())
                self._pending = self._pending[cut + 1 :]

        return [s for s in out if s]

    def flush(self) -> list[str]:
        rest = self._pending.strip()
        self._pending = ""
        return [rest] if rest else []

    def _find_boundary(self, text: str) -> tuple[str, str] | None:
        for m in _BOUNDARY.finditer(text):
            end = m.end(1)
            candidate = text[:end]
            if len(candidate.strip()) < MIN_CHUNK_CHARS:
                continue
            last_word = candidate.rsplit(None, 1)[-1].lower() if candidate.split() else ""
            if last_word in _ABBREVIATIONS:
                continue
            return candidate, text[end:].lstrip()
        return None
