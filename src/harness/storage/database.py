from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from harness.llm import Message, ToolCall
from harness.tools import ToolResult


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_call_id TEXT,
                    tool_calls_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    call_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );
                """
            )
            await db.commit()

    async def create_session(self, session_id: str, task: str) -> None:
        now = _utc_now()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO sessions(id, task, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, task, "running", now, now),
            )
            await db.commit()

    async def add_message(self, session_id: str, message: Message) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO messages(
                    session_id, role, content, tool_call_id, tool_calls_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    message.role,
                    message.content,
                    message.tool_call_id,
                    json.dumps([call.model_dump(mode="json") for call in message.tool_calls]),
                    _utc_now(),
                ),
            )
            await db.commit()

    async def add_tool_call(
        self,
        session_id: str,
        call: ToolCall,
        result: ToolResult,
    ) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO tool_calls(
                    session_id, call_id, tool_name, arguments_json, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    call.id,
                    call.name,
                    json.dumps(call.arguments),
                    json.dumps(result.model_dump(mode="json"), default=str),
                    _utc_now(),
                ),
            )
            await db.commit()

    async def add_event(self, session_id: str, event_type: str, payload: dict[str, object]) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO events(session_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, event_type, json.dumps(payload, default=str), _utc_now()),
            )
            await db.commit()

    async def finish_session(self, session_id: str, status: str, reason: str | None = None) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE sessions SET status = ?, reason = ?, updated_at = ? WHERE id = ?",
                (status, reason, _utc_now(), session_id),
            )
            await db.commit()

    async def add_artifact(
        self,
        artifact_id: str,
        session_id: str,
        artifact_type: str,
        path: str,
        created_by: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO artifacts(
                    id, session_id, artifact_type, path, created_by, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    session_id,
                    artifact_type,
                    path,
                    created_by,
                    json.dumps(metadata or {}, default=str),
                    _utc_now(),
                ),
            )
            await db.commit()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
