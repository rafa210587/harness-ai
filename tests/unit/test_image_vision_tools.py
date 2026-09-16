from pathlib import Path

from harness.images import ImageGenerationResult
from harness.tools import ImageGenerateTool, VisionInspectTool, WorkspacePaths
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
        output_path.write_bytes(b"png")
        return ImageGenerationResult(
            path=output_path,
            metadata={"prompt": prompt, "references": len(references or [])},
        )


class FakeVisionProvider:
    async def inspect(self, image_path: Path, prompt: str) -> VisionResult:
        return VisionResult(
            description=f"inspected:{image_path.name}:{prompt}",
            passed=True,
        )


async def test_image_generate_returns_artifact(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"reference")
    tool = ImageGenerateTool(FakeImageProvider(), paths)

    result = await tool.execute(
        tool.validate_arguments(
            {
                "prompt": "wooden crate",
                "output_path": "artifacts/crate.png",
                "references": ["reference.png"],
            }
        )
    )

    assert result.success is True
    assert result.artifacts == ["artifacts/crate.png"]
    assert result.output["metadata"]["references"] == 1


async def test_vision_inspect_reads_workspace_image(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    image = tmp_path / "render.png"
    image.write_bytes(b"png")
    tool = VisionInspectTool(FakeVisionProvider(), paths)

    result = await tool.execute(
        tool.validate_arguments({"image_path": "render.png", "prompt": "Is the crate visible?"})
    )

    assert result.success is True
    assert result.output["passed"] is True
    assert "render.png" in result.output["description"]
