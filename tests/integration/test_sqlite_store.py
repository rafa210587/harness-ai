import sqlite3
from pathlib import Path

import pytest

from harness.llm import Message, ToolCall
from harness.storage import SQLiteStore
from harness.tools import ToolResult


async def test_sqlite_store_persists_session_message_and_tool_call(tmp_path: Path) -> None:
    db_path = tmp_path / "harness.db"
    store = SQLiteStore(db_path)
    await store.initialize()
    await store.create_session("s1", "test task")
    await store.add_message("s1", Message(role="user", content="hello"))
    await store.add_message(
        "s1",
        Message(
            role="assistant",
            tool_calls=[ToolCall(id="call-1", name="filesystem_list", arguments={"path": "."})],
        ),
    )
    await store.add_tool_call(
        "s1",
        ToolCall(id="call-1", name="filesystem_list", arguments={"path": "."}),
        ToolResult.ok([{"path": "hello.txt", "type": "file"}]),
    )
    await store.add_event("s1", "TEST_EVENT", {"value": 1})
    await store.finish_session("s1", "completed")

    with sqlite3.connect(db_path) as db:
        session = db.execute("SELECT task, status FROM sessions WHERE id = ?", ("s1",)).fetchone()
        message_count = db.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?", ("s1",)
        ).fetchone()[0]
        tool_count = db.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE session_id = ?", ("s1",)
        ).fetchone()[0]

    assert session == ("test task", "completed")
    assert message_count == 2
    assert tool_count == 1
    assert await store.schema_version() == 1

    loaded = await store.get_session("s1")
    assert loaded is not None
    assert loaded.task == "test task"
    assert loaded.status == "completed"

    sessions = await store.list_sessions()
    assert [item.id for item in sessions] == ["s1"]

    messages = await store.list_messages("s1")
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[1].tool_calls[0].name == "filesystem_list"

    events = await store.list_events("s1")
    assert len(events) == 1
    assert events[0].event_type == "TEST_EVENT"
    assert events[0].payload == {"value": 1}


async def test_sqlite_store_rejects_incompatible_schema_version(tmp_path: Path) -> None:
    db_path = tmp_path / "harness.db"
    store = SQLiteStore(db_path)
    await store.initialize()

    with sqlite3.connect(db_path) as db:
        db.execute(
            "UPDATE schema_meta SET value = '99' WHERE key = 'schema_version'"
        )
        db.commit()

    with pytest.raises(RuntimeError, match="Unsupported database schema version 99"):
        await store.initialize()


async def test_sqlite_store_persists_and_lists_artifacts(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "harness.db")
    await store.initialize()
    await store.create_session("s1", "artifact task")

    await store.add_artifact(
        "artifact-1",
        "s1",
        "png",
        "artifacts/render.png",
        "blender_render",
        {"frame": 1},
    )

    artifacts = await store.list_artifacts("s1")

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.id == "artifact-1"
    assert artifact.artifact_type == "png"
    assert artifact.path == "artifacts/render.png"
    assert artifact.created_by == "blender_render"
    assert artifact.metadata == {"frame": 1}


async def test_sqlite_store_persists_and_decides_approval(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "harness.db")
    await store.initialize()
    await store.create_session("s1", "dangerous task")
    call = ToolCall(id="call-1", name="shell_run", arguments={"command": "echo hi"})

    await store.create_approval("s1", call, "approval required")
    pending = await store.get_pending_approval("s1")

    assert pending is not None
    assert pending.call_id == "call-1"
    assert pending.tool_call() == call

    await store.decide_approval(pending.id, True)

    assert await store.get_pending_approval("s1") is None
