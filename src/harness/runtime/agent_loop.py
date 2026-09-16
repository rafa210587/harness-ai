from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel

from harness.hooks import BeforeToolEvent, HookAction, HookDispatcher
from harness.llm import LLMProvider, LLMProviderError, Message, ToolCall
from harness.runtime.context import ContextCompactor
from harness.runtime.verification import RunVerifier, VerificationRequest
from harness.storage import SQLiteStore
from harness.tools import ToolRegistry, ToolResult, ToolRisk


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
        verifier: RunVerifier | None = None,
        context_compactor: ContextCompactor | None = None,
        max_context_messages: int = 40,
        max_verification_retries: int = 2,
        max_steps: int = 50,
        max_consecutive_errors: int = 5,
        approval_handler: ApprovalHandler | None = None,
    ) -> None:
        if max_context_messages < 1:
            raise ValueError("max_context_messages must be at least 1")
        self._provider = provider
        self._tools = tools
        self._hooks = hooks or HookDispatcher()
        self._store = store
        self._verifier = verifier
        self._context_compactor = context_compactor
        self._max_context_messages = max_context_messages
        self._max_verification_retries = max_verification_retries
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
        return await self._continue(current_session_id, task, messages)

    async def resume(self, session_id: str) -> AgentRunResult:
        if self._store is None:
            raise RuntimeError("Session resume requires persistent storage")

        await self._store.initialize()
        session = await self._store.get_session(session_id)
        if session is None:
            raise ValueError(f"Unknown session: {session_id}")
        if session.status != AgentStatus.BLOCKED.value:
            raise ValueError(f"Session {session_id} is not blocked")

        messages = await self._store.list_messages(session_id)
        approval = await self._store.get_pending_approval(session_id)
        if approval is None:
            raise ValueError(f"Session {session_id} has no pending approval")
        if self._approval_handler is None:
            return AgentRunResult(
                status=AgentStatus.BLOCKED,
                steps=0,
                session_id=session_id,
                reason=approval.reason or "Human approval required",
            )

        call = approval.tool_call()
        tool = self._tools.get(call.name) if call.name in self._tools else None
        event = BeforeToolEvent(
            session_id=session_id,
            tool_name=call.name,
            arguments=call.arguments,
            risk=tool.risk if tool is not None else ToolRisk.DANGEROUS,
        )
        approved = await self._approval_handler(event)
        await self._store.decide_approval(approval.id, approved)
        await self._record_event(
            session_id,
            "APPROVAL_DECIDED",
            {"tool": call.name, "call_id": call.id, "approved": approved},
        )
        await self._store.set_session_status(session_id, "running")
        await self._record_event(session_id, "SESSION_RESUMED", {"call_id": call.id})

        if not approved:
            tool_result = ToolResult.fail("Human approval denied")
        elif tool is None:
            tool_result = ToolResult.fail(f"Unknown tool: {call.name}")
        else:
            tool_result = await self._tools.execute(call.name, call.arguments)

        await self._persist_tool_result(session_id, messages, call, tool_result, step=0)
        consecutive_errors = 0 if tool_result.success else 1

        unresolved = _unresolved_tool_calls(messages)
        if unresolved:
            consecutive_errors, terminal = await self._process_tool_calls(
                session_id,
                messages,
                unresolved,
                step=0,
                consecutive_errors=consecutive_errors,
            )
            if terminal is not None:
                return terminal

        return await self._continue(
            session_id,
            session.task,
            messages,
            initial_consecutive_errors=consecutive_errors,
        )

    async def _continue(
        self,
        session_id: str,
        task: str,
        messages: list[Message],
        *,
        initial_consecutive_errors: int = 0,
    ) -> AgentRunResult:
        consecutive_errors = initial_consecutive_errors
        verification_failures = 0

        for step in range(1, self._max_steps + 1):
            await self._compact_context_if_needed(session_id, messages, step=step)
            llm_started = perf_counter()
            await self._record_event(
                session_id,
                "LLM_REQUEST_STARTED",
                {"step": step, "message_count": len(messages)},
            )
            try:
                response = await self._provider.complete(messages, tools=self._tools.schemas())
            except LLMProviderError as exc:
                await self._record_event(
                    session_id,
                    "LLM_ERROR",
                    {
                        "step": step,
                        "error": str(exc),
                        "duration_ms": _duration_ms(llm_started),
                    },
                )
                await self._finish_session(session_id, AgentStatus.FAILED, str(exc))
                raise

            await self._record_event(
                session_id,
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
                        session_id,
                        messages,
                        Message(role="assistant", content=response.content),
                    )

                if self._verifier is not None:
                    verification_attempt = verification_failures + 1
                    artifacts = await self._artifact_paths(session_id)
                    await self._record_event(
                        session_id,
                        "VERIFICATION_STARTED",
                        {
                            "step": step,
                            "attempt": verification_attempt,
                            "artifact_count": len(artifacts),
                        },
                    )
                    verification = await self._verifier.verify(
                        VerificationRequest(
                            session_id=session_id,
                            task=task,
                            proposed_content=response.content,
                            artifacts=artifacts,
                            attempt=verification_attempt,
                        )
                    )
                    await self._record_event(
                        session_id,
                        "VERIFICATION_PASSED" if verification.passed else "VERIFICATION_FAILED",
                        {
                            "step": step,
                            "attempt": verification_attempt,
                            "feedback": verification.feedback,
                        },
                    )
                    if not verification.passed:
                        verification_failures += 1
                        if verification_failures > self._max_verification_retries:
                            reason = (
                                "Verification failed after "
                                f"{verification_failures} attempts: {verification.feedback}"
                            )
                            result = AgentRunResult(
                                status=AgentStatus.FAILED,
                                content=response.content,
                                steps=step,
                                session_id=session_id,
                                reason=reason,
                            )
                            await self._finish_session(session_id, result.status, reason)
                            return result

                        feedback = verification.feedback or "The proposed result was not accepted."
                        await self._append_message(
                            session_id,
                            messages,
                            Message(
                                role="system",
                                content=(
                                    "Internal verification failed. Continue working on "
                                    "the original task and correct the result before finishing. "
                                    f"Feedback: {feedback}"
                                ),
                            ),
                        )
                        continue

                result = AgentRunResult(
                    status=AgentStatus.COMPLETED,
                    content=response.content,
                    steps=step,
                    session_id=session_id,
                )
                await self._finish_session(session_id, result.status)
                return result

            await self._append_message(
                session_id,
                messages,
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                ),
            )
            consecutive_errors, terminal = await self._process_tool_calls(
                session_id,
                messages,
                response.tool_calls,
                step=step,
                consecutive_errors=consecutive_errors,
            )
            if terminal is not None:
                return terminal

        reason = "Maximum agent steps reached"
        result = AgentRunResult(
            status=AgentStatus.FAILED,
            steps=self._max_steps,
            session_id=session_id,
            reason=reason,
        )
        await self._finish_session(session_id, result.status, reason)
        return result

    async def _process_tool_calls(
        self,
        session_id: str,
        messages: list[Message],
        calls: list[ToolCall],
        *,
        step: int,
        consecutive_errors: int,
    ) -> tuple[int, AgentRunResult | None]:
        for call in calls:
            tool_started = perf_counter()
            await self._record_event(
                session_id,
                "TOOL_STARTED",
                {"step": step, "tool": call.name, "call_id": call.id},
            )
            tool = self._tools.get(call.name) if call.name in self._tools else None
            if tool is None:
                tool_result = ToolResult.fail(f"Unknown tool: {call.name}")
            else:
                event = BeforeToolEvent(
                    session_id=session_id,
                    tool_name=call.name,
                    arguments=call.arguments,
                    risk=tool.risk,
                )
                decision = await self._hooks.before_tool(event)

                if decision.action is HookAction.DENY:
                    tool_result = ToolResult.fail(decision.reason or "Tool execution denied")
                elif decision.action is HookAction.REQUIRE_APPROVAL:
                    reason = decision.reason or "Human approval required"
                    if self._store is not None:
                        await self._store.create_approval(session_id, call, reason)
                    await self._record_event(
                        session_id,
                        "APPROVAL_REQUIRED",
                        {"tool": call.name, "call_id": call.id, "reason": reason},
                    )
                    if self._approval_handler is None:
                        result = AgentRunResult(
                            status=AgentStatus.BLOCKED,
                            steps=step,
                            session_id=session_id,
                            reason=reason,
                        )
                        await self._finish_session(session_id, result.status, reason)
                        return consecutive_errors, result

                    approved = await self._approval_handler(event)
                    if self._store is not None:
                        approval = await self._store.get_pending_approval(session_id)
                        if approval is not None and approval.call_id == call.id:
                            await self._store.decide_approval(approval.id, approved)
                    await self._record_event(
                        session_id,
                        "APPROVAL_DECIDED",
                        {"tool": call.name, "call_id": call.id, "approved": approved},
                    )
                    if not approved:
                        tool_result = ToolResult.fail("Human approval denied")
                    else:
                        tool_result = await self._tools.execute(call.name, call.arguments)
                else:
                    tool_result = await self._tools.execute(call.name, call.arguments)

            await self._persist_tool_result(
                session_id,
                messages,
                call,
                tool_result,
                step=step,
                started=tool_started,
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
                        session_id=session_id,
                        reason=reason,
                    )
                    await self._finish_session(session_id, result.status, reason)
                    return consecutive_errors, result

        return consecutive_errors, None

    async def _persist_tool_result(
        self,
        session_id: str,
        messages: list[Message],
        call: ToolCall,
        result: ToolResult,
        *,
        step: int,
        started: float | None = None,
    ) -> None:
        if self._store is not None:
            await self._store.add_tool_call(session_id, call, result)
            await self._persist_artifacts(session_id, call.name, result)

        await self._record_event(
            session_id,
            "TOOL_COMPLETED" if result.success else "TOOL_ERROR",
            {
                "step": step,
                "tool": call.name,
                "call_id": call.id,
                "duration_ms": _duration_ms(started) if started is not None else 0,
                "error": result.error or "",
            },
        )
        await self._append_message(
            session_id,
            messages,
            Message(
                role="tool",
                tool_call_id=call.id,
                content=json.dumps(result.model_dump(mode="json"), default=str),
            ),
        )

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

    async def _persist_artifacts(
        self,
        session_id: str,
        tool_name: str,
        result: ToolResult,
    ) -> None:
        if self._store is None:
            return
        for artifact_path in result.artifacts:
            artifact_id = uuid4().hex
            suffix = Path(artifact_path).suffix.lower().lstrip(".")
            artifact_type = suffix or "file"
            await self._store.add_artifact(
                artifact_id,
                session_id,
                artifact_type,
                artifact_path,
                tool_name,
            )
            await self._store.add_event(
                session_id,
                "ARTIFACT_CREATED",
                {
                    "artifact_id": artifact_id,
                    "type": artifact_type,
                    "path": artifact_path,
                    "created_by": tool_name,
                },
            )

    async def _artifact_paths(self, session_id: str) -> list[str]:
        if self._store is None:
            return []
        events = await self._store.list_events(session_id)
        paths: list[str] = []
        for event in events:
            if event.event_type != "ARTIFACT_CREATED":
                continue
            path = event.payload.get("path")
            if isinstance(path, str) and path not in paths:
                paths.append(path)
        return paths

    async def _compact_context_if_needed(
        self,
        session_id: str,
        messages: list[Message],
        *,
        step: int,
    ) -> None:
        if self._context_compactor is None or len(messages) <= self._max_context_messages:
            return

        original_count = len(messages)
        started = perf_counter()
        await self._record_event(
            session_id,
            "CONTEXT_COMPACTION_STARTED",
            {"step": step, "message_count": original_count},
        )
        try:
            compacted = await self._context_compactor.compact(messages)
        except Exception as exc:  # plugin boundary: compaction must not crash the agent run
            await self._record_event(
                session_id,
                "CONTEXT_COMPACTION_FAILED",
                {
                    "step": step,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "duration_ms": _duration_ms(started),
                },
            )
            return

        if len(compacted) >= original_count:
            await self._record_event(
                session_id,
                "CONTEXT_COMPACTION_SKIPPED",
                {
                    "step": step,
                    "reason": "no_reduction",
                    "message_count": original_count,
                    "duration_ms": _duration_ms(started),
                },
            )
            return

        messages[:] = compacted
        await self._record_event(
            session_id,
            "CONTEXT_COMPACTED",
            {
                "step": step,
                "before": original_count,
                "after": len(messages),
                "duration_ms": _duration_ms(started),
            },
        )

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


def _unresolved_tool_calls(messages: list[Message]) -> list[ToolCall]:
    resolved_ids = {
        message.tool_call_id
        for message in messages
        if message.role == "tool" and message.tool_call_id is not None
    }
    return [
        call
        for message in messages
        if message.role == "assistant"
        for call in message.tool_calls
        if call.id not in resolved_ids
    ]


def _duration_ms(started: float) -> int:
    return round((perf_counter() - started) * 1000)
