"""SQLite persistence for sessions and messages."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New conversation',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        self.path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None, "Database not connected"
        return self._db

    async def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        await self.db.execute(
            "INSERT INTO sessions (id, created_at) VALUES (?, ?)", (session_id, _now())
        )
        await self.db.commit()
        return session_id

    async def session_exists(self, session_id: str) -> bool:
        cur = await self.db.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
        return await cur.fetchone() is not None

    async def list_sessions(self) -> list[dict[str, Any]]:
        cur = await self.db.execute(
            """SELECT s.id, s.title, s.created_at, COUNT(m.id) AS message_count
               FROM sessions s LEFT JOIN messages m ON m.session_id = s.id
               GROUP BY s.id ORDER BY s.created_at DESC"""
        )
        return [dict(r) for r in await cur.fetchall()]

    async def delete_session(self, session_id: str) -> bool:
        cur = await self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await self.db.commit()
        return cur.rowcount > 0

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        await self.db.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, _now()),
        )
        # First user message becomes the session title
        if role == "user":
            await self.db.execute(
                """UPDATE sessions SET title = ?
                   WHERE id = ? AND title = 'New conversation'""",
                (content[:60], session_id),
            )
        await self.db.commit()

    async def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        cur = await self.db.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
