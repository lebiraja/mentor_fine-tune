"""Manual end-to-end check: speak a synthesized question at the live backend.

Run inside the backend container against the running stack:
    docker compose exec backend python tests/e2e_voice_client.py
"""

import asyncio
import json
import time

import numpy as np
import websockets


async def main() -> None:
    from backend.config import settings
    from backend.core.tts import KokoroTTS

    print("Synthesizing the 'user' question...")
    tts = KokoroTTS(settings.kokoro_model, settings.kokoro_voices, "af_heart", 1.0)
    pcm24 = tts.synthesize("I keep putting off things that matter to me. Why do I do that?")
    a24 = np.frombuffer(pcm24, dtype=np.int16).astype(np.float32) / 32768.0
    idx = (np.arange(int(len(a24) * 2 / 3)) * 1.5).astype(int)
    a16 = a24[idx[idx < len(a24)]]
    mic = (np.clip(a16, -1, 1) * 32767).astype(np.int16).tobytes()
    print(f"  {len(a16) / 16000:.1f}s of audio")

    async with websockets.connect("ws://localhost:2323/ws/chat", max_size=10 << 20) as ws:
        await ws.send(json.dumps({"type": "set_session", "session_id": None}))

        # stream like a mic: 64ms chunks, then 1s of silence to end the turn
        chunk = 2048  # bytes = 1024 samples
        for i in range(0, len(mic), chunk):
            await ws.send(mic[i : i + chunk])
        silence = b"\x00\x00" * 1024
        for _ in range(20):
            await ws.send(silence)

        t0 = time.perf_counter()
        transcript = reply = None
        audio_bytes = 0
        first_audio_at = None
        events: list[str] = []

        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
            if isinstance(raw, bytes):
                if first_audio_at is None:
                    first_audio_at = time.perf_counter() - t0
                audio_bytes += len(raw)
                continue
            msg = json.loads(raw)
            events.append(msg["type"])
            if msg["type"] == "user_transcript":
                transcript = msg["text"]
            elif msg["type"] == "assistant_done":
                reply = msg["text"]
            elif msg["type"] == "state" and msg["state"] == "listening" and reply:
                break
            elif msg["type"] == "error":
                raise SystemExit(f"ERROR: {msg['message']}")

        print(f"\nTranscript: {transcript}")
        print(f"\nReply: {reply}")
        print(f"\nFirst audio after end-of-turn: {first_audio_at:.2f}s")
        print(f"TTS audio received: {audio_bytes / 2 / 24000:.1f}s ({audio_bytes} bytes)")
        assert transcript and "putting off" in transcript.lower()
        assert reply and len(reply) > 40
        assert audio_bytes > 24000
        print("\nE2E VOICE TURN: PASS")


if __name__ == "__main__":
    asyncio.run(main())
