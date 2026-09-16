from __future__ import annotations

import json
from typing import Protocol

from harness.llm import LLMProvider, Message


class ContextCompactor(Protocol):
    """Produce a smaller context while preserving recent conversational state."""

    async def compact(self, messages: list[Message]) -> list[Message]: ...


class LLMContextCompactor:
    """Summarize older resolved history with the configured LLM provider."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        keep_recent: int = 16,
        max_message_chars: int = 4_000,
    ) -> None:
        if keep_recent < 1:
            raise ValueError("keep_recent must be at least 1")
        if max_message_chars < 256:
            raise ValueError("max_message_chars must be at least 256")
        self._provider = provider
        self._keep_recent = keep_recent
        self._max_message_chars = max_message_chars

    async def compact(self, messages: list[Message]) -> list[Message]:
        if len(messages) <= self._keep_recent:
            return [message.model_copy(deep=True) for message in messages]

        leading_system, history = _split_leading_system(messages)
        if len(history) <= self._keep_recent:
            return [message.model_copy(deep=True) for message in messages]

        desired_cutoff = max(1, len(history) - self._keep_recent)
        cutoff = _safe_cutoff(history, desired_cutoff)
        if cutoff <= 0:
            return [message.model_copy(deep=True) for message in messages]

        old_messages = history[:cutoff]
        recent_messages = history[cutoff:]
        response = await self._provider.complete(
            [
                Message(
                    role="system",
                    content=(
                        "Summarize the supplied earlier agent conversation as compact working memory. "
                        "Preserve the original goal, decisions, constraints, completed actions, important "
                        "tool results, artifact paths, failures, approvals, and remaining work. Do not add "
                        "facts. Return only the working-memory summary."
                    ),
                ),
                Message(role="user", content=_serialize_messages(old_messages, self._max_message_chars)),
            ],
            tools=None,
        )
        summary = (response.content or "").strip()
        if not summary:
            return [message.model_copy(deep=True) for message in messages]

        compacted = [message.model_copy(deep=True) for message in leading_system]
        compacted.append(
            Message(
                role="system",
                content=f"Working memory from earlier conversation:\n{summary}",
            )
        )
        compacted.extend(message.model_copy(deep=True) for message in recent_messages)
        return compacted


def _split_leading_system(messages: list[Message]) -> tuple[list[Message], list[Message]]:
    index = 0
    while index < len(messages) and messages[index].role == "system":
        index += 1
    return messages[:index], messages[index:]


def _safe_cutoff(messages: list[Message], desired: int) -> int:
    cutoff = min(max(desired, 0), len(messages))
    while cutoff > 0 and _crosses_tool_boundary(messages, cutoff):
        cutoff -= 1
    return cutoff


def _crosses_tool_boundary(messages: list[Message], cutoff: int) -> bool:
    prefix_call_ids = {
        call.id
        for message in messages[:cutoff]
        if message.role == "assistant"
        for call in message.tool_calls
    }
    tail_tool_ids = {
        message.tool_call_id
        for message in messages[cutoff:]
        if message.role == "tool" and message.tool_call_id is not None
    }
    if prefix_call_ids & tail_tool_ids:
        return True

    tail_call_ids = {
        call.id
        for message in messages[cutoff:]
        if message.role == "assistant"
        for call in message.tool_calls
    }
    prefix_tool_ids = {
        message.tool_call_id
        for message in messages[:cutoff]
        if message.role == "tool" and message.tool_call_id is not None
    }
    return bool(tail_call_ids & prefix_tool_ids)


def _serialize_messages(messages: list[Message], max_message_chars: int) -> str:
    serialized: list[str] = []
    for message in messages:
        content = message.content or ""
        if len(content) > max_message_chars:
            content = content[:max_message_chars] + "...[truncated]"
        payload = {
            "role": message.role,
            "content": content,
            "tool_call_id": message.tool_call_id,
            "tool_calls": [call.model_dump(mode="json") for call in message.tool_calls],
        }
        serialized.append(json.dumps(payload, ensure_ascii=False, default=str))
    return "\n".join(serialized)
