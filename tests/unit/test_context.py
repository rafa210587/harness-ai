from typing import Any

from harness.llm import LLMProvider, LLMResponse, Message, ToolCall
from harness.runtime.context import LLMContextCompactor


class SummaryProvider(LLMProvider):
    def __init__(self, summary: str = "goal and completed work") -> None:
        self.summary = summary
        self.calls: list[list[Message]] = []

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        self.calls.append([message.model_copy(deep=True) for message in messages])
        return LLMResponse(content=self.summary, finish_reason="stop")


async def test_compactor_preserves_leading_system_and_recent_messages() -> None:
    provider = SummaryProvider()
    compactor = LLMContextCompactor(provider, keep_recent=2)
    messages = [
        Message(role="system", content="stable rules"),
        Message(role="user", content="original task"),
        Message(role="assistant", content="old answer"),
        Message(role="user", content="recent question"),
        Message(role="assistant", content="recent answer"),
    ]

    compacted = await compactor.compact(messages)

    assert compacted[0].role == "system"
    assert compacted[0].content == "stable rules"
    assert compacted[1].role == "system"
    assert "Working memory" in (compacted[1].content or "")
    assert [message.content for message in compacted[-2:]] == [
        "recent question",
        "recent answer",
    ]
    assert len(provider.calls) == 1
    assert "original task" in (provider.calls[0][1].content or "")


async def test_compactor_does_not_split_tool_call_from_tool_result() -> None:
    provider = SummaryProvider()
    compactor = LLMContextCompactor(provider, keep_recent=2)
    call = ToolCall(id="call-1", name="filesystem_read", arguments={"path": "a.txt"})
    messages = [
        Message(role="user", content="inspect file"),
        Message(role="assistant", tool_calls=[call]),
        Message(role="tool", tool_call_id="call-1", content="file contents"),
        Message(role="user", content="what next?"),
    ]

    compacted = await compactor.compact(messages)

    recent = compacted[1:]
    assistant_index = next(i for i, message in enumerate(recent) if message.tool_calls)
    assert recent[assistant_index].tool_calls[0].id == "call-1"
    assert recent[assistant_index + 1].role == "tool"
    assert recent[assistant_index + 1].tool_call_id == "call-1"


async def test_compactor_skips_short_context() -> None:
    provider = SummaryProvider()
    compactor = LLMContextCompactor(provider, keep_recent=4)
    messages = [Message(role="user", content="short")]

    compacted = await compactor.compact(messages)

    assert compacted == messages
    assert compacted is not messages
    assert provider.calls == []
