"""WebSocket handler for voice streaming."""

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from backend.core.audio_utils import bytes_to_array, array_to_bytes
from backend.core.exceptions import ServiceError

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """WebSocket endpoint for voice streaming.

    Receives audio bytes and returns:
    1. Transcript (JSON)
    2. Emotion (JSON)
    3. Response (JSON)
    4. Audio bytes (binary)
    """
    # Import services from main module (set during startup)
    from backend import main

    await websocket.accept()

    # Create session
    session_id = main.session_service.create_session()
    print(f"\n[WS] New session: {session_id}")

    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive()
            
            # Check for disconnect
            if data.get("type") == "websocket.disconnect":
                break

            if "bytes" not in data:
                continue

            audio_bytes = data["bytes"]

            # Send status update
            await websocket.send_json({"type": "status", "message": "Processing..."})

            try:
                # 1. Convert bytes to numpy array
                audio_array = bytes_to_array(audio_bytes)

                if len(audio_array) == 0:
                    await websocket.send_json(
                        {"type": "error", "message": "No audio detected"}
                    )
                    continue

                # 2. Transcribe
                await websocket.send_json({"type": "status", "message": "Transcribing..."})
                transcript = await main.stt_service.transcribe(audio_array)

                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript,
                })

                if not transcript:
                    await websocket.send_json(
                        {"type": "error", "message": "Could not transcribe audio"}
                    )
                    continue

                # 3. Detect emotion
                await websocket.send_json({
                    "type": "status",
                    "message": "Detecting emotion..."
                })
                emotion = main.emotion_service.detect_emotion_blocking(
                    audio_array, transcript
                )

                await websocket.send_json({
                    "type": "emotion",
                    "data": emotion,
                })

                # 4. Generate response
                await websocket.send_json({
                    "type": "status",
                    "message": "Generating response..."
                })
                history = main.session_service.get_history(session_id)

                # Prepare messages for LLM
                messages = []
                for item in history:
                    if item["role"] in ["user", "assistant"]:
                        messages.append({
                            "role": item["role"],
                            "content": item["content"],
                        })

                # Add current user message
                messages.append({
                    "role": "user",
                    "content": transcript,
                })

                response_text = await main.llm_service.generate_response(
                    messages, emotion
                )

                await websocket.send_json({
                    "type": "response",
                    "text": response_text,
                })

                # 5. Synthesize speech
                await websocket.send_json({
                    "type": "status",
                    "message": "Synthesizing speech..."
                })
                audio_response = await main.tts_service.synthesize(
                    response_text, emotion
                )

                await websocket.send_bytes(audio_response)

                # 6. Save turn to history
                main.session_service.add_turn(
                    session_id, transcript, emotion, response_text
                )

                await websocket.send_json({
                    "type": "status",
                    "message": "Ready for next turn",
                })

            except ServiceError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
                print(f"[WS] Service error: {e}")

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing error: {str(e)}",
                })
                print(f"[WS] Error: {e}")

    except WebSocketDisconnect:
        print(f"[WS] Session {session_id} disconnected")

    except Exception as e:
        print(f"[WS] Unexpected error: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass
