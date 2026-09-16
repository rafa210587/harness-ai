import asyncio
from typing import ClassVar

from pydantic import BaseModel

from harness.security import SecretRedactor
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


class NestedSecretTool(Tool):
    name: ClassVar[str] = "nested_secret"
    description: ClassVar[str] = "Return nested output containing a configured secret."
    risk: ClassVar[ToolRisk] = ToolRisk.READ

    def __init__(self, secret: str) -> None:
        self._secret = secret

    async def execute(self, arguments: BaseModel) -> ToolResult:
        del arguments
        return ToolResult.ok(
            {
                "stdout": f"token={self._secret}",
                "nested": [self._secret, {"value": f"prefix-{self._secret}-suffix"}],
            }
        )


class FailingSecretTool(Tool):
    name: ClassVar[str] = "failing_secret"
    description: ClassVar[str] = "Raise an exception containing a configured secret."
    risk: ClassVar[ToolRisk] = ToolRisk.READ

    def __init__(self, secret: str) -> None:
        self._secret = secret

    async def execute(self, arguments: BaseModel) -> ToolResult:
        del arguments
        raise RuntimeError(f"provider returned {self._secret}")


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


async def test_registry_redacts_secrets_from_nested_tool_output() -> None:
    secret = "deepseek-super-secret"
    registry = ToolRegistry(redactor=SecretRedactor([secret]))
    registry.register(NestedSecretTool(secret))

    result = await registry.execute("nested_secret", {})

    assert result.success is True
    assert result.output == {
        "stdout": "token=[REDACTED]",
        "nested": ["[REDACTED]", {"value": "prefix-[REDACTED]-suffix"}],
    }


async def test_registry_redacts_secrets_from_tool_errors() -> None:
    secret = "deepseek-super-secret"
    registry = ToolRegistry(redactor=SecretRedactor([secret]))
    registry.register(FailingSecretTool(secret))

    result = await registry.execute("failing_secret", {})

    assert result.success is False
    assert secret not in (result.error or "")
    assert "[REDACTED]" in (result.error or "")


async def test_registry_runs_cleanup_handlers_and_reports_errors() -> None:
    registry = ToolRegistry()
    cleaned: list[str] = []

    async def first_cleanup() -> None:
        cleaned.append("first")

    async def failing_cleanup() -> None:
        cleaned.append("failing")
        raise RuntimeError("cleanup failed")

    registry.register_cleanup(first_cleanup)
    registry.register_cleanup(failing_cleanup)

    errors = await registry.close()

    assert cleaned == ["failing", "first"]
    assert errors == ["RuntimeError: cleanup failed"]


async def test_registry_redacts_secrets_from_cleanup_errors() -> None:
    secret = "deepseek-super-secret"
    registry = ToolRegistry(redactor=SecretRedactor([secret]))

    async def failing_cleanup() -> None:
        raise RuntimeError(f"cleanup leaked {secret}")

    registry.register_cleanup(failing_cleanup)

    errors = await registry.close()

    assert errors == ["RuntimeError: cleanup leaked [REDACTED]"]


def test_registry_exposes_openai_compatible_schema() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    schema = registry.schemas()[0]

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["parameters"]["properties"]["text"]["type"] == "string"
