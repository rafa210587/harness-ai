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


def test_registry_exposes_openai_compatible_schema() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    schema = registry.schemas()[0]

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["parameters"]["properties"]["text"]["type"] == "string"
