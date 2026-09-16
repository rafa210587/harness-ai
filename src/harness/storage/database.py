from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic import BaseModel

from harness.llm import Message, ToolCall
from harness.tools.base import ToolResult

_SCHEMA_VERSION = 1


class SessionRecord(BaseModel):
    id: str
    task: str
    status: str
    reason: str | None = None
    created_at: str
    updated_at: str


class EventRecord(BaseModel):
    id: int
    session_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: str


class ArtifactRecord(BaseModel):
    id: str
    session_id: str
    artifact_type: str
    path: str
    created_by: str
    metadata: dict[str, Any]
    created_at: str


class ApprovalRecord(BaseModel):
    id: int
    session_id: str
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    status: str
    reason: str | None = None
    created_at: str
    decided_at: str | None = None

    def tool_call(self) -> ToolCall:
        return ToolCall(id=self.call_id, name=self.tool_name, arguments=self.arguments)


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

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

                CREATE TABLE IF NOT EXISTS approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    call_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
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

                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                    ON sessions(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, id);
                CREATE INDEX IF NOT EXISTS idx_tool_calls_session
                    ON tool_calls(session_id, id);
                CREATE INDEX IF NOT EXISTS idx_approvals_session_status
                    ON approvals(session_id, status, id);
                CREATE INDEX IF NOT EXISTS idx_events_session
                    ON events(session_id, id);
                CREATE INDEX IF NOT EXISTS idx_artifacts_session
                    ON artifacts(session_id, created_at, id);
                """
            )
            await self._ensure_schema_version(db)
            await db.commit()

    async def schema_version(self) -> int:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'")
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Database schema version is not initialized")
        return int(row[0])

    async def _ensure_schema_version(self, db: aiosqlite.Connection) -> None:
        cursor = await db.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'")
        row = await cursor.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO schema_meta(key, value) VALUES ('schema_version', ?)",
                (str(_SCHEMA_VERSION),),
            )
            return

        found = int(row[0])
        if found != _SCHEMA_VERSION:
            raise RuntimeError(
                f"Unsupported database schema version {found}; expected {_SCHEMA_VERSION}"
            )

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

    async def list_sessions(self, limit: int = 20) -> list[SessionRecord]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, task, status, reason, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
        return [SessionRecord(**dict(row)) for row in rows]

    async def get_session(self, session_id: str) -> SessionRecord | None:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, task, status, reason, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            )
            row = await cursor.fetchone()
        return SessionRecord(**dict(row)) if row is not None else None

    async def set_session_status(
        self,
        session_id: str,
        status: str,
        reason: str | None = None,
    ) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE sessions SET status = ?, reason = ?, updated_at = ? WHERE id = ?",
                (status, reason, _utc_now(), session_id),
            )
            await db.commit()

    async def list_messages(self, session_id: str) -> list[Message]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT role, content, tool_call_id, tool_calls_json
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()
        return [
            Message.model_validate(
                {
                    "role": row["role"],
                    "content": row["content"],
                    "tool_call_id": row["tool_call_id"],
                    "tool_calls": json.loads(row["tool_calls_json"]),
                }
            )
            for row in rows
        ]

    async def list_events(self, session_id: str) -> list[EventRecord]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, session_id, event_type, payload_json, created_at
                FROM events
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()
        return [
            EventRecord(
                id=row["id"],
                session_id=row["session_id"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def list_artifacts(self, session_id: str) -> list[ArtifactRecord]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, session_id, artifact_type, path, created_by,
                       metadata_json, created_at
                FROM artifacts
                WHERE session_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()
        return [
            ArtifactRecord(
                id=row["id"],
                session_id=row["session_id"],
                artifact_type=row["artifact_type"],
                path=row["path"],
                created_by=row["created_by"],
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

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

    async def create_approval(
        self,
        session_id: str,
        call: ToolCall,
        reason: str | None,
    ) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO approvals(
                    session_id, call_id, tool_name, arguments_json, status, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    call.id,
                    call.name,
                    json.dumps(call.arguments),
                    "pending",
                    reason,
                    _utc_now(),
                ),
            )
            await db.commit()

    async def get_pending_approval(self, session_id: str) -> ApprovalRecord | None:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, session_id, call_id, tool_name, arguments_json, status,
                       reason, created_at, decided_at
                FROM approvals
                WHERE session_id = ? AND status = 'pending'
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return ApprovalRecord(
            id=row["id"],
            session_id=row["session_id"],
            call_id=row["call_id"],
            tool_name=row["tool_name"],
            arguments=json.loads(row["arguments_json"]),
            status=row["status"],
            reason=row["reason"],
            created_at=row["created_at"],
            decided_at=row["decided_at"],
        )

    async def decide_approval(self, approval_id: int, approved: bool) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE approvals SET status = ?, decided_at = ? WHERE id = ?",
                ("approved" if approved else "denied", _utc_now(), approval_id),
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
        await self.set_session_status(session_id, status, reason)

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
