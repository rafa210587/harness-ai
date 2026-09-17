from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Protocol

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, TypeAdapter

from harness.runtime.agent_loop import AgentRunResult, AgentStatus
from harness.storage import SQLiteStore


class EvalScenario(BaseModel):
    name: str
    task: str
    expected_status: AgentStatus = AgentStatus.COMPLETED
    content_contains: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    max_steps: int | None = Field(default=None, ge=1)
    max_tool_errors: int | None = Field(default=None, ge=0)


class EvalCaseResult(BaseModel):
    name: str
    passed: bool
    status: AgentStatus
    steps: int
    duration_ms: int
    tool_errors: int = 0
    verification_failures: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    session_id: str
    missing_required_tools: list[str] = Field(default_factory=list)
    tool_error_details: list[str] = Field(default_factory=list)
    reason: str | None = None


class EvalReport(BaseModel):
    total: int
    passed: int
    success_rate: float
    average_steps: float
    total_tool_errors: int
    total_verification_failures: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cases: list[EvalCaseResult]


class AgentRunner(Protocol):
    async def run(self, task: str) -> AgentRunResult: ...


AgentFactory = Callable[[EvalScenario], AgentRunner]
_SCENARIOS = TypeAdapter(list[EvalScenario])


def load_eval_scenarios(path: Path) -> list[EvalScenario]:
    if not path.is_file():
        raise FileNotFoundError(f"Eval scenario file not found: {path}")
    raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "scenarios" in raw:
        raw = raw["scenarios"]
    if raw is None:
        return []
    return _SCENARIOS.validate_python(raw)


class EvalRunner:
    """Run deterministic or real-agent scenarios without an external eval framework."""

    def __init__(self, agent_factory: AgentFactory, *, store: SQLiteStore | None = None) -> None:
        self._agent_factory = agent_factory
        self._store = store

    async def run(self, scenarios: list[EvalScenario]) -> EvalReport:
        cases: list[EvalCaseResult] = []
        for scenario in scenarios:
            cases.append(await self._run_case(scenario))

        passed = sum(case.passed for case in cases)
        total_steps = sum(case.steps for case in cases)
        total = len(cases)
        return EvalReport(
            total=total,
            passed=passed,
            success_rate=(passed / total) if total else 0.0,
            average_steps=(total_steps / total) if total else 0.0,
            total_tool_errors=sum(case.tool_errors for case in cases),
            total_verification_failures=sum(case.verification_failures for case in cases),
            input_tokens=sum(case.input_tokens for case in cases),
            output_tokens=sum(case.output_tokens for case in cases),
            total_tokens=sum(case.total_tokens for case in cases),
            cases=cases,
        )

    async def _run_case(self, scenario: EvalScenario) -> EvalCaseResult:
        started = perf_counter()
        result = await self._agent_factory(scenario).run(scenario.task)
        tool_errors = 0
        verification_failures = 0
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        completed_tools: set[str] = set()
        tool_error_details: list[str] = []
        if self._store is not None:
            events = await self._store.list_events(result.session_id)
            tool_errors = sum(event.event_type == "TOOL_ERROR" for event in events)
            verification_failures = sum(
                event.event_type == "VERIFICATION_FAILED" for event in events
            )
            for event in events:
                if event.event_type == "TOOL_ERROR":
                    tool = event.payload.get("tool")
                    error = event.payload.get("error")
                    tool_error_details.append(f"{tool}: {error}")
                if event.event_type == "TOOL_COMPLETED":
                    tool_name = event.payload.get("tool")
                    if isinstance(tool_name, str):
                        completed_tools.add(tool_name)
                if event.event_type != "LLM_RESPONSE_RECEIVED":
                    continue
                usage = event.payload.get("usage")
                if not isinstance(usage, dict):
                    continue
                input_tokens += _int_value(usage.get("input_tokens"))
                output_tokens += _int_value(usage.get("output_tokens"))
                total_tokens += _int_value(usage.get("total_tokens"))

        missing_required_tools = sorted(set(scenario.required_tools) - completed_tools)
        passed = result.status is scenario.expected_status
        if scenario.max_steps is not None and result.steps > scenario.max_steps:
            passed = False
        if scenario.max_tool_errors is not None and tool_errors > scenario.max_tool_errors:
            passed = False
        if missing_required_tools:
            passed = False
        if result.content is None and scenario.content_contains:
            passed = False
        elif result.content is not None:
            passed = passed and all(
                expected in result.content for expected in scenario.content_contains
            )

        return EvalCaseResult(
            name=scenario.name,
            passed=passed,
            status=result.status,
            steps=result.steps,
            duration_ms=round((perf_counter() - started) * 1000),
            tool_errors=tool_errors,
            verification_failures=verification_failures,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            session_id=result.session_id,
            missing_required_tools=missing_required_tools,
            tool_error_details=tool_error_details,
            reason=result.reason,
        )


def _int_value(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0
