from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from harness.tools.base import Tool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

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
            return await tool.execute(validated)
        except Exception as exc:  # boundary: normalize tool implementation failures
            return ToolResult.fail(f"Tool {name} failed: {exc}")

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
