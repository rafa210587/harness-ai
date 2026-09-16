from pathlib import Path
from typing import Any

from harness.hooks import HookDispatcher, PermissionHook
from harness.llm import LLMProvider, LLMResponse, Message, ToolCall
from harness.runtime import AgentLoop, AgentStatus
from harness.tools import FilesystemListTool, ShellRunTool, ToolRegistry, WorkspacePaths


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


async def test_agent_loop_blocks_dangerous_tool_without_approval(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(ShellRunTool(WorkspacePaths(tmp_path)))
    provider = FakeProvider(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(id="call-1", name="shell_run", arguments={"command": "echo hi"})
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
    result = await loop.run("Run a command")

    assert result.status is AgentStatus.BLOCKED
    assert "dangerous" in (result.reason or "")
