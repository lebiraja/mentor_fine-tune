"""REST endpoints: health + session management."""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    app = request.app
    llm_ok = await app.state.llm.healthy()
    return {
        "status": "healthy" if app.state.ready and llm_ok else "degraded",
        "engines_loaded": app.state.ready,
        "llm_reachable": llm_ok,
        "latency_ms": app.state.stats.last,
    }


@router.get("/sessions")
async def list_sessions(request: Request):
    return {"sessions": await request.app.state.db.list_sessions()}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, request: Request):
    db = request.app.state.db
    if not await db.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": await db.get_messages(session_id)}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    if not await request.app.state.db.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
