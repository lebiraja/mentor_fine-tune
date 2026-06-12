"""Manual end-to-end Tamil check: speak a synthesized Tamil question at the backend.

Run inside the backend container against the running stack:
    docker compose exec -e PYTHONPATH=/app backend python tests/e2e_tamil_client.py

Verifies the full bilingual path: Piper-synthesized Tamil audio → Whisper detects
`ta` → Qwen3 replies in Tamil → Piper speaks it back.
"""

import asyncio
import json
import time

import numpy as np
import websockets


async def main() -> None:
    from backend.config import settings
    from backend.core.tts import OUTPUT_SAMPLE_RATE, PiperTTS, _resample

    if not settings.piper_tamil_model.exists():
        raise SystemExit("Piper Tamil model not downloaded — run `make models`.")

    print("Synthesizing the Tamil 'user' question with Piper...")
    piper = PiperTTS(settings.piper_tamil_model, settings.piper_tamil_config)
    # "Why do I keep worrying about everything?"
    pcm, sr = piper.synthesize("நான் ஏன் எல்லாவற்றையும் பற்றி கவலைப்படுகிறேன்?")
    if sr != OUTPUT_SAMPLE_RATE:
        pcm = _resample(pcm, sr, OUTPUT_SAMPLE_RATE)
    a24 = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    idx = (np.arange(int(len(a24) * 2 / 3)) * 1.5).astype(int)
    a16 = a24[idx[idx < len(a24)]]
    mic = (np.clip(a16, -1, 1) * 32767).astype(np.int16).tobytes()
    print(f"  {len(a16) / 16000:.1f}s of audio")

    async with websockets.connect("ws://localhost:2323/ws/chat", max_size=10 << 20) as ws:
        await ws.send(json.dumps({"type": "set_session", "session_id": None}))

        chunk = 2048
        for i in range(0, len(mic), chunk):
            await ws.send(mic[i : i + chunk])
        for _ in range(25):
            await ws.send(b"\x00\x00" * 1024)

        t0 = time.perf_counter()
        transcript = reply = language = None
        audio_bytes = 0
        first_audio_at = None

        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
            if isinstance(raw, bytes):
                if first_audio_at is None:
                    first_audio_at = time.perf_counter() - t0
                audio_bytes += len(raw)
                continue
            msg = json.loads(raw)
            if msg["type"] == "user_transcript":
                transcript = msg["text"]
                language = msg.get("language")
            elif msg["type"] == "assistant_done":
                reply = msg["text"]
            elif msg["type"] == "state" and msg["state"] == "listening" and reply:
                break
            elif msg["type"] == "error":
                raise SystemExit(f"ERROR: {msg['message']}")

        print(f"\nDetected language: {language}")
        print(f"Transcript: {transcript}")
        print(f"Reply: {reply}")
        print(f"First audio after end-of-turn: {first_audio_at:.2f}s")
        print(f"TTS audio received: {audio_bytes / 2 / 24000:.1f}s ({audio_bytes} bytes)")
        assert language == "ta", f"expected Tamil detection, got {language}"
        assert transcript, "no transcript"
        assert reply and len(reply) > 20, "reply too short"
        assert audio_bytes > 24000, "no Tamil audio returned"
        print("\nE2E TAMIL VOICE TURN: PASS")


if __name__ == "__main__":
    asyncio.run(main())
