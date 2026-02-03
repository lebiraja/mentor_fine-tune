"""Simple test client for the FastAPI backend."""

import asyncio
import numpy as np
import websockets
import json
from pathlib import Path


async def test_websocket(audio_file: str = None, duration: float = 2.0):
    """Test WebSocket connection and full pipeline.

    Args:
        audio_file: Path to audio file (if not provided, generates silence)
        duration: Duration of silence to generate (seconds)
    """
    uri = "ws://localhost:2323/ws/voice"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n✓ Connected to {uri}")

            # Generate or load audio
            if audio_file and Path(audio_file).exists():
                # Load audio from file
                import soundfile as sf

                audio, sr = sf.read(audio_file)
                if len(audio.shape) > 1:
                    audio = audio[:, 0]  # Convert to mono
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()
                print(f"✓ Loaded audio from {audio_file}")
            else:
                # Generate silence
                sample_rate = 16000
                audio = np.zeros(int(sample_rate * duration), dtype=np.float32)
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()
                print(f"✓ Generated {duration}s of silence")

            # Send audio
            print("\nSending audio...")
            await websocket.send(audio_bytes)

            # Receive responses
            print("\nReceiving responses...\n")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)

                    # Determine if message is binary or text
                    if isinstance(message, bytes):
                        # Binary message (audio)
                        print(f"\n🔊 Received audio ({len(message)} bytes)")
                        break

                    else:
                        # Text message (JSON)
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type", "unknown")

                            if msg_type == "status":
                                print(f"  → {data.get('message')}")
                            elif msg_type == "transcript":
                                print(f"\n📝 Transcript:\n   {data.get('text')}")
                            elif msg_type == "emotion":
                                emo = data.get("data", {})
                                print(
                                    f"\n😊 Emotion:\n"
                                    f"   Primary: {emo.get('primary_emotion')} "
                                    f"({emo.get('confidence'):.2f})"
                                )
                            elif msg_type == "response":
                                print(f"\n🤖 Response:\n   {data.get('text')}")
                            elif msg_type == "error":
                                print(f"\n⚠️  Error: {data.get('message')}")
                            else:
                                print(f"  {msg_type}: {data}")

                        except json.JSONDecodeError:
                            # If not valid JSON, might be audio or error
                            print(f"Received non-JSON message ({len(message)} bytes)")
                            break

                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break

        print("\n✓ Connection closed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    audio_file = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_websocket(audio_file))
