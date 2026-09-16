from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from harness.hooks import BeforeToolEvent, HookAction, HookDispatcher
from harness.llm import LLMProvider, Message
from harness.tools import ToolRegistry, ToolResult


class AgentStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class AgentRunResult(BaseModel):
    status: AgentStatus
    content: str | None = None
    steps: int = 0
    session_id: str
    reason: str | None = None


ApprovalHandler = Callable[[BeforeToolEvent], Awaitable[bool]]


class AgentLoop:
    def __init__(
        self,
        provider: LLMProvider,
        tools: ToolRegistry,
        hooks: HookDispatcher | None = None,
        *,
        max_steps: int = 50,
        max_consecutive_errors: int = 5,
        approval_handler: ApprovalHandler | None = None,
    ) -> None:
        self._provider = provider
        self._tools = tools
        self._hooks = hooks or HookDispatcher()
        self._max_steps = max_steps
        self._max_consecutive_errors = max_consecutive_errors
        self._approval_handler = approval_handler

    async def run(
        self,
        task: str,
        *,
        system_prompt: str | None = None,
        session_id: str | None = None,
    ) -> AgentRunResult:
        current_session_id = session_id or uuid4().hex
        messages: list[Message] = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=task))

        consecutive_errors = 0

        for step in range(1, self._max_steps + 1):
            response = await self._provider.complete(messages, tools=self._tools.schemas())

            if not response.tool_calls:
                return AgentRunResult(
                    status=AgentStatus.COMPLETED,
                    content=response.content,
                    steps=step,
                    session_id=current_session_id,
                )

            messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            for call in response.tool_calls:
                tool = self._tools.get(call.name) if call.name in self._tools else None
                if tool is None:
                    result = ToolResult.fail(f"Unknown tool: {call.name}")
                else:
                    event = BeforeToolEvent(
                        session_id=current_session_id,
                        tool_name=call.name,
                        arguments=call.arguments,
                        risk=tool.risk,
                    )
                    decision = await self._hooks.before_tool(event)

                    if decision.action is HookAction.DENY:
                        result = ToolResult.fail(decision.reason or "Tool execution denied")
                    elif decision.action is HookAction.REQUIRE_APPROVAL:
                        if self._approval_handler is None:
                            return AgentRunResult(
                                status=AgentStatus.BLOCKED,
                                steps=step,
                                session_id=current_session_id,
                                reason=decision.reason or "Human approval required",
                            )
                        approved = await self._approval_handler(event)
                        if not approved:
                            result = ToolResult.fail("Human approval denied")
                        else:
                            result = await self._tools.execute(call.name, call.arguments)
                    else:
                        result = await self._tools.execute(call.name, call.arguments)

                messages.append(
                    Message(
                        role="tool",
                        tool_call_id=call.id,
                        content=json.dumps(result.model_dump(mode="json"), default=str),
                    )
                )

                if result.success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= self._max_consecutive_errors:
                        return AgentRunResult(
                            status=AgentStatus.FAILED,
                            steps=step,
                            session_id=current_session_id,
                            reason="Maximum consecutive tool errors reached",
                        )

        return AgentRunResult(
            status=AgentStatus.FAILED,
            steps=self._max_steps,
            session_id=current_session_id,
            reason="Maximum agent steps reached",
        )
