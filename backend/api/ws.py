"""WebSocket endpoint — the voice/text conversation channel.

Protocol (client -> server):
  binary frames            16 kHz int16 mono PCM mic audio
  {"type":"set_session","session_id": str|null, "persona": str|null}
  {"type":"user_text","text": str}
  {"type":"mute","muted": bool}

Protocol (server -> client):
  binary frames            24 kHz int16 mono PCM TTS audio
  {"type":"session","session_id": str}
  {"type":"state","state":"listening"|"transcribing"|"generating"|"speaking"}
  {"type":"user_transcript","text": str, "language": str, "language_probability": float}
  {"type":"assistant_delta","text": str}
  {"type":"assistant_done","text": str}
  {"type":"interrupted"}
  {"type":"assistant_greeting","text": str}   # proactive opening (Friend persona)
  {"type":"session","session_id": str, "persona": str}
  {"type":"error","message": str}
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config import settings
from backend.core.pipeline import ConversationPipeline
from backend.core.vad import TurnDetector

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    app = websocket.app
    await websocket.accept()

    turn_detector = TurnDetector(
        vad=app.state.make_vad(),
        threshold=settings.VAD_THRESHOLD,
        min_speech_s=settings.VAD_MIN_SPEECH_S,
        end_silence_s=settings.VAD_END_SILENCE_S,
    )
    pipeline = ConversationPipeline(
        stt=app.state.stt,
        tts=app.state.tts,
        llm=app.state.llm,
        turn_detector=turn_detector,
        db=app.state.db,
        personas=app.state.personas,
        context_tokens=settings.LLM_CONTEXT_TOKENS,
        send_json=websocket.send_json,
        send_bytes=websocket.send_bytes,
        stats=app.state.stats,
    )
    pipeline.allow_barge_in = settings.ALLOW_BARGE_IN
    pipeline.echo_tail_s = settings.ECHO_TAIL_S

    try:
        while True:
            data = await websocket.receive()
            if data.get("type") == "websocket.disconnect":
                break

            if "bytes" in data and data["bytes"] is not None:
                await pipeline.handle_audio(data["bytes"])
            elif "text" in data and data["text"] is not None:
                try:
                    msg = json.loads(data["text"])
                except json.JSONDecodeError:
                    continue

                match msg.get("type"):
                    case "set_session":
                        session_id = await pipeline.set_session(
                            msg.get("session_id"), msg.get("persona")
                        )
                        await websocket.send_json({
                            "type": "session",
                            "session_id": session_id,
                            "persona": pipeline.persona.id,
                        })
                        await websocket.send_json({"type": "state", "state": "listening"})
                    case "user_text":
                        if pipeline.session_id is None:
                            await pipeline.set_session(None)
                            await websocket.send_json({
                                "type": "session",
                                "session_id": pipeline.session_id,
                                "persona": pipeline.persona.id,
                            })
                        await pipeline.handle_text(msg.get("text", ""))
                    case "mute":
                        pipeline.muted = bool(msg.get("muted"))

    except WebSocketDisconnect:
        pass
    finally:
        await pipeline.shutdown()
