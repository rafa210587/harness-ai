import asyncio
from typing import ClassVar

from pydantic import BaseModel

from harness.tools import Tool, ToolRegistry, ToolResult, ToolRisk


class EchoArguments(BaseModel):
    text: str


class EchoTool(Tool):
    name: ClassVar[str] = "echo"
    description: ClassVar[str] = "Echo text."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = EchoArguments

    async def execute(self, arguments: BaseModel) -> ToolResult:
        parsed = EchoArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(parsed.text)


class SlowTool(Tool):
    name: ClassVar[str] = "slow"
    description: ClassVar[str] = "Wait longer than the registry timeout."
    risk: ClassVar[ToolRisk] = ToolRisk.READ

    async def execute(self, arguments: BaseModel) -> ToolResult:
        del arguments
        await asyncio.sleep(1)
        return ToolResult.ok("finished")


async def test_registry_executes_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = await registry.execute("echo", {"text": "hello"})

    assert result.success is True
    assert result.output == "hello"


async def test_registry_rejects_invalid_arguments() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = await registry.execute("echo", {})

    assert result.success is False
    assert "Invalid arguments" in (result.error or "")


async def test_registry_normalizes_unknown_tool() -> None:
    registry = ToolRegistry()

    result = await registry.execute("missing", {})

    assert result.success is False
    assert "Unknown tool" in (result.error or "")


async def test_registry_enforces_global_tool_timeout() -> None:
    registry = ToolRegistry(default_timeout_seconds=1)
    registry.register(SlowTool())

    result = await registry.execute("slow", {})

    assert result.success is False
    assert result.retryable is False
    assert result.error == "Tool slow timed out after 1s"


def test_registry_exposes_openai_compatible_schema() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    schema = registry.schemas()[0]

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["parameters"]["properties"]["text"]["type"] == "string"
