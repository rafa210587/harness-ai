import sqlite3
from pathlib import Path

from harness.llm import Message, ToolCall
from harness.storage import SQLiteStore
from harness.tools import ToolResult


async def test_sqlite_store_persists_session_message_and_tool_call(tmp_path: Path) -> None:
    db_path = tmp_path / "harness.db"
    store = SQLiteStore(db_path)
    await store.initialize()
    await store.create_session("s1", "test task")
    await store.add_message("s1", Message(role="user", content="hello"))
    await store.add_tool_call(
        "s1",
        ToolCall(id="call-1", name="filesystem_list", arguments={"path": "."}),
        ToolResult.ok([{"path": "hello.txt", "type": "file"}]),
    )
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
    assert message_count == 1
    assert tool_count == 1
