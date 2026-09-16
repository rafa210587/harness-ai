from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from harness.tools.base import Tool, ToolResult

CleanupHandler = Callable[[], Awaitable[None]]


class ToolRegistry:
    def __init__(self, *, default_timeout_seconds: int = 300) -> None:
        if default_timeout_seconds < 1:
            raise ValueError("default_timeout_seconds must be at least 1")
        self._tools: dict[str, Tool] = {}
        self._cleanups: list[CleanupHandler] = []
        self._default_timeout_seconds = default_timeout_seconds

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
            return ToolResult.fail(str(exc))

        try:
            validated = tool.validate_arguments(arguments)
        except ValidationError as exc:
            return ToolResult.fail(f"Invalid arguments for {name}: {exc}")

        try:
            return await asyncio.wait_for(
                tool.execute(validated),
                timeout=self._default_timeout_seconds,
            )
        except TimeoutError:
            return ToolResult.fail(
                f"Tool {name} timed out after {self._default_timeout_seconds}s",
                retryable=False,
            )
        except Exception as exc:  # boundary: normalize tool implementation failures
            return ToolResult.fail(f"Tool {name} failed: {exc}")

    async def close(self) -> list[str]:
        errors: list[str] = []
        for cleanup in reversed(self._cleanups):
            try:
                await cleanup()
            except Exception as exc:  # cleanup boundary
                errors.append(f"{type(exc).__name__}: {exc}")
        return errors

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
