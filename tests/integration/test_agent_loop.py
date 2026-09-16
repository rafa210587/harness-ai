from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel

from harness.hooks import HookDispatcher, PermissionHook
from harness.llm import LLMProvider, LLMResponse, Message, ToolCall
from harness.runtime import AgentLoop, AgentStatus
from harness.storage import SQLiteStore
from harness.tools import (
    FilesystemListTool,
    Tool,
    ToolRegistry,
    ToolResult,
    ToolRisk,
    WorkspacePaths,
)


class FakeProvider(LLMProvider):
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = responses
        self.calls: list[list[Message]] = []

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        self.calls.append([message.model_copy(deep=True) for message in messages])
        return self._responses.pop(0)


class DangerousArguments(BaseModel):
    value: str


class DangerousEchoTool(Tool):
    name: ClassVar[str] = "dangerous_echo"
    description: ClassVar[str] = "Return the provided value after approval."
    risk: ClassVar[ToolRisk] = ToolRisk.DANGEROUS
    arguments_model: ClassVar[type[BaseModel]] = DangerousArguments

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = DangerousArguments.model_validate(arguments.model_dump())
        return ToolResult.ok({"value": args.value})


async def test_agent_loop_executes_tool_and_returns_final_answer(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    registry = ToolRegistry()
    registry.register(FilesystemListTool(WorkspacePaths(tmp_path)))

    provider = FakeProvider(
        [
            LLMResponse(
                tool_calls=[ToolCall(id="call-1", name="filesystem_list", arguments={"path": "."})],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="Found hello.txt", finish_reason="stop"),
        ]
    )

    result = await AgentLoop(provider, registry).run("List files")

    assert result.status is AgentStatus.COMPLETED
    assert result.content == "Found hello.txt"
    assert result.steps == 2
    second_call_messages = provider.calls[1]
    tool_message = next(message for message in second_call_messages if message.role == "tool")
    assert "hello.txt" in (tool_message.content or "")


async def test_agent_loop_blocks_dangerous_tool_without_approval() -> None:
    registry = ToolRegistry()
    registry.register(DangerousEchoTool())
    provider = FakeProvider(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(id="call-1", name="dangerous_echo", arguments={"value": "hello"})
                ],
                finish_reason="tool_calls",
            )
        ]
    )

    loop = AgentLoop(
        provider,
        registry,
        hooks=HookDispatcher([PermissionHook()]),
    )
    result = await loop.run("Run a dangerous tool")

    assert result.status is AgentStatus.BLOCKED
    assert "approval" in (result.reason or "")


async def test_blocked_session_resumes_from_persisted_approval(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(DangerousEchoTool())
    provider = FakeProvider(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(id="call-1", name="dangerous_echo", arguments={"value": "hello"})
                ],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="Approved and completed", finish_reason="stop"),
        ]
    )
    store = SQLiteStore(tmp_path / "harness.db")
    blocked_loop = AgentLoop(
        provider,
        registry,
        hooks=HookDispatcher([PermissionHook()]),
        store=store,
    )

    blocked = await blocked_loop.run("Use the dangerous echo")

    assert blocked.status is AgentStatus.BLOCKED
    pending = await store.get_pending_approval(blocked.session_id)
    assert pending is not None
    assert pending.tool_name == "dangerous_echo"

    async def approve(_event) -> bool:
        return True

    resumed_loop = AgentLoop(
        provider,
        registry,
        hooks=HookDispatcher([PermissionHook()]),
        store=store,
        approval_handler=approve,
    )
    resumed = await resumed_loop.resume(blocked.session_id)

    assert resumed.status is AgentStatus.COMPLETED
    assert resumed.content == "Approved and completed"
    session = await store.get_session(blocked.session_id)
    assert session is not None
    assert session.status == "completed"
    assert await store.get_pending_approval(blocked.session_id) is None
    resumed_messages = provider.calls[-1]
    tool_message = next(message for message in resumed_messages if message.role == "tool")
    assert "hello" in (tool_message.content or "")
