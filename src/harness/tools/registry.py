from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from harness.security import SecretRedactor
from harness.tools.base import Tool, ToolResult

CleanupHandler = Callable[[], Awaitable[None]]


class ToolRegistry:
    def __init__(
        self,
        *,
        default_timeout_seconds: int = 300,
        redactor: SecretRedactor | None = None,
    ) -> None:
        if default_timeout_seconds < 1:
            raise ValueError("default_timeout_seconds must be at least 1")
        self._tools: dict[str, Tool] = {}
        self._cleanups: list[CleanupHandler] = []
        self._default_timeout_seconds = default_timeout_seconds
        self._redactor = redactor

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def register_cleanup(self, cleanup: CleanupHandler) -> None:
        self._cleanups.append(cleanup)

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def tools(self) -> tuple[Tool, ...]:
        return tuple(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        try:
            tool = self.get(name)
        except KeyError as exc:
            return self._redact_result(ToolResult.fail(str(exc)))

        try:
            validated = tool.validate_arguments(arguments)
        except ValidationError as exc:
            return self._redact_result(ToolResult.fail(f"Invalid arguments for {name}: {exc}"))

        try:
            result = await asyncio.wait_for(
                tool.execute(validated),
                timeout=self._default_timeout_seconds,
            )
        except TimeoutError:
            result = ToolResult.fail(
                f"Tool {name} timed out after {self._default_timeout_seconds}s",
                retryable=False,
            )
        except Exception as exc:  # boundary: normalize tool implementation failures
            result = ToolResult.fail(f"Tool {name} failed: {exc}")
        return self._redact_result(result)

    async def close(self) -> list[str]:
        errors: list[str] = []
        for cleanup in reversed(self._cleanups):
            try:
                await cleanup()
            except Exception as exc:  # cleanup boundary
                error = f"{type(exc).__name__}: {exc}"
                errors.append(self._redactor.redact_text(error) if self._redactor else error)
        return errors

    def _redact_result(self, result: ToolResult) -> ToolResult:
        if self._redactor is None:
            return result
        return result.model_copy(
            update={
                "output": self._redactor.redact(result.output),
                "error": self._redactor.redact_text(result.error)
                if result.error is not None
                else None,
                "artifacts": [self._redactor.redact_text(path) for path in result.artifacts],
            }
        )

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
