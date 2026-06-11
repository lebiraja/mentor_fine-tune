"""Streaming client for the llama.cpp server (OpenAI-compatible API)."""

import json
from typing import AsyncIterator

import httpx


class LLMClient:
    def __init__(self, base_url: str, model: str, max_tokens: int, temperature: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yields text deltas. Cancellation-safe: closing the generator aborts the request."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
        }
        async with self.client.stream(
            "POST", f"{self.base_url}/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[len("data: "):]
                if data.strip() == "[DONE]":
                    break
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {}).get("content")
                if delta:
                    yield delta

    async def healthy(self) -> bool:
        try:
            r = await self.client.get(f"{self.base_url.removesuffix('/v1')}/health")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self.client.aclose()
