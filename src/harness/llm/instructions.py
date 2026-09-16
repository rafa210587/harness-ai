from __future__ import annotations

from typing import Any

from harness.llm.base import LLMProvider, LLMResponse, Message


class SystemInstructionLLMProvider(LLMProvider):
    """Prepend stable harness instructions without persisting them into session history."""

    def __init__(self, provider: LLMProvider, instruction: str) -> None:
        instruction = instruction.strip()
        if not instruction:
            raise ValueError("instruction must not be empty")
        self._provider = provider
        self._instruction = instruction

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        effective_messages = [
            Message(role="system", content=self._instruction),
            *messages,
        ]
        return await self._provider.complete(effective_messages, tools=tools)
