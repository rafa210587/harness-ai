from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from harness.config import Settings
from harness.images import ImageGenerationResult
from harness.runtime import build_tool_registry
from harness.tools import Tool, ToolResult, ToolRisk
from harness.vision import VisionResult


class FakeImageProvider:
    async def generate(
        self,
        prompt: str,
        output_path: Path,
        *,
        references: list[Path] | None = None,
    ) -> ImageGenerationResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"image")
        return ImageGenerationResult(
            path=output_path,
            metadata={"prompt": prompt, "references": len(references or [])},
        )


class FakeVisionProvider:
    async def inspect(self, image_path: Path, prompt: str) -> VisionResult:
        return VisionResult(
            description=f"{image_path.name}: {prompt}",
            passed=True,
        )


class SecretEchoArguments(BaseModel):
    text: str


class SecretEchoTool(Tool):
    name: ClassVar[str] = "secret_echo"
    description: ClassVar[str] = "Echo text for redaction tests."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = SecretEchoArguments

    async def execute(self, arguments: BaseModel) -> ToolResult:
        parsed = SecretEchoArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(parsed.text)


def _settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(
        harness_workspace=tmp_path / "workspace",
        harness_data_dir=tmp_path / "data",
        harness_browser_profile=tmp_path / "browser-profile",
        **overrides,
    )


async def test_factory_registers_image_and_vision_only_when_provided(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    default_registry = build_tool_registry(settings)
    assert "image_generate" not in default_registry
    assert "vision_inspect" not in default_registry

    registry = build_tool_registry(
        settings,
        image_provider=FakeImageProvider(),
        vision_provider=FakeVisionProvider(),
    )
    assert "image_generate" in registry
    assert "vision_inspect" in registry

    generated = await registry.execute(
        "image_generate",
        {"prompt": "test", "output_path": "artifacts/test.png"},
    )
    assert generated.success is True
    assert generated.artifacts == ["artifacts/test.png"]

    inspected = await registry.execute(
        "vision_inspect",
        {"image_path": "artifacts/test.png", "prompt": "is valid?"},
    )
    assert inspected.success is True
    assert inspected.output["passed"] is True


async def test_factory_redacts_configured_deepseek_key_from_tool_results(tmp_path: Path) -> None:
    secret = "deepseek-live-secret"
    settings = _settings(tmp_path, deepseek_api_key=secret)
    registry = build_tool_registry(settings)
    registry.register(SecretEchoTool())

    result = await registry.execute("secret_echo", {"text": f"token={secret}"})

    assert result.success is True
    assert result.output == "token=[REDACTED]"
