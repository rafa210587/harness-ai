from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel

from harness.hooks import BeforeToolEvent, HookAction, HookDispatcher
from harness.llm import LLMProvider, LLMProviderError, Message
from harness.storage import SQLiteStore
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
        store: SQLiteStore | None = None,
        max_steps: int = 50,
        max_consecutive_errors: int = 5,
        approval_handler: ApprovalHandler | None = None,
    ) -> None:
        self._provider = provider
        self._tools = tools
        self._hooks = hooks or HookDispatcher()
        self._store = store
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

        if self._store is not None:
            await self._store.initialize()
            await self._store.create_session(current_session_id, task)
            await self._store.add_event(current_session_id, "SESSION_STARTED", {})

        if system_prompt:
            await self._append_message(
                current_session_id,
                messages,
                Message(role="system", content=system_prompt),
            )
        await self._append_message(
            current_session_id,
            messages,
            Message(role="user", content=task),
        )

        consecutive_errors = 0

        for step in range(1, self._max_steps + 1):
            llm_started = perf_counter()
            await self._record_event(
                current_session_id,
                "LLM_REQUEST_STARTED",
                {"step": step, "message_count": len(messages)},
            )
            try:
                response = await self._provider.complete(messages, tools=self._tools.schemas())
            except LLMProviderError as exc:
                await self._record_event(
                    current_session_id,
                    "LLM_ERROR",
                    {
                        "step": step,
                        "error": str(exc),
                        "duration_ms": _duration_ms(llm_started),
                    },
                )
                await self._finish_session(current_session_id, AgentStatus.FAILED, str(exc))
                raise

            await self._record_event(
                current_session_id,
                "LLM_RESPONSE_RECEIVED",
                {
                    "step": step,
                    "tool_call_count": len(response.tool_calls),
                    "finish_reason": response.finish_reason or "",
                    "duration_ms": _duration_ms(llm_started),
                },
            )

            if not response.tool_calls:
                if response.content is not None:
                    await self._append_message(
                        current_session_id,
                        messages,
                        Message(role="assistant", content=response.content),
                    )
                result = AgentRunResult(
                    status=AgentStatus.COMPLETED,
                    content=response.content,
                    steps=step,
                    session_id=current_session_id,
                )
                await self._finish_session(current_session_id, result.status)
                return result

            await self._append_message(
                current_session_id,
                messages,
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                ),
            )

            for call in response.tool_calls:
                tool_started = perf_counter()
                await self._record_event(
                    current_session_id,
                    "TOOL_STARTED",
                    {"step": step, "tool": call.name, "call_id": call.id},
                )
                tool = self._tools.get(call.name) if call.name in self._tools else None
                if tool is None:
                    tool_result = ToolResult.fail(f"Unknown tool: {call.name}")
                else:
                    event = BeforeToolEvent(
                        session_id=current_session_id,
                        tool_name=call.name,
                        arguments=call.arguments,
                        risk=tool.risk,
                    )
                    decision = await self._hooks.before_tool(event)

                    if decision.action is HookAction.DENY:
                        tool_result = ToolResult.fail(decision.reason or "Tool execution denied")
                    elif decision.action is HookAction.REQUIRE_APPROVAL:
                        if self._approval_handler is None:
                            reason = decision.reason or "Human approval required"
                            await self._record_event(
                                current_session_id,
                                "APPROVAL_REQUIRED",
                                {"tool": call.name, "reason": reason},
                            )
                            result = AgentRunResult(
                                status=AgentStatus.BLOCKED,
                                steps=step,
                                session_id=current_session_id,
                                reason=reason,
                            )
                            await self._finish_session(current_session_id, result.status, reason)
                            return result

                        approved = await self._approval_handler(event)
                        await self._record_event(
                            current_session_id,
                            "APPROVAL_DECIDED",
                            {"tool": call.name, "approved": approved},
                        )
                        if not approved:
                            tool_result = ToolResult.fail("Human approval denied")
                        else:
                            tool_result = await self._tools.execute(call.name, call.arguments)
                    else:
                        tool_result = await self._tools.execute(call.name, call.arguments)

                if self._store is not None:
                    await self._store.add_tool_call(current_session_id, call, tool_result)

                await self._record_event(
                    current_session_id,
                    "TOOL_COMPLETED" if tool_result.success else "TOOL_ERROR",
                    {
                        "step": step,
                        "tool": call.name,
                        "call_id": call.id,
                        "duration_ms": _duration_ms(tool_started),
                        "error": tool_result.error or "",
                    },
                )

                await self._append_message(
                    current_session_id,
                    messages,
                    Message(
                        role="tool",
                        tool_call_id=call.id,
                        content=json.dumps(tool_result.model_dump(mode="json"), default=str),
                    ),
                )

                if tool_result.success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= self._max_consecutive_errors:
                        reason = "Maximum consecutive tool errors reached"
                        result = AgentRunResult(
                            status=AgentStatus.FAILED,
                            steps=step,
                            session_id=current_session_id,
                            reason=reason,
                        )
                        await self._finish_session(current_session_id, result.status, reason)
                        return result

        reason = "Maximum agent steps reached"
        result = AgentRunResult(
            status=AgentStatus.FAILED,
            steps=self._max_steps,
            session_id=current_session_id,
            reason=reason,
        )
        await self._finish_session(current_session_id, result.status, reason)
        return result

    async def _append_message(
        self,
        session_id: str,
        messages: list[Message],
        message: Message,
    ) -> None:
        messages.append(message)
        if self._store is not None:
            await self._store.add_message(session_id, message)

    async def _record_event(
        self,
        session_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        if self._store is not None:
            await self._store.add_event(session_id, event_type, payload)

    async def _finish_session(
        self,
        session_id: str,
        status: AgentStatus,
        reason: str | None = None,
    ) -> None:
        if self._store is not None:
            await self._store.finish_session(session_id, status.value, reason)
            await self._store.add_event(
                session_id,
                "SESSION_FINISHED",
                {"status": status.value, "reason": reason or ""},
            )


def _duration_ms(started: float) -> int:
    return round((perf_counter() - started) * 1000)
