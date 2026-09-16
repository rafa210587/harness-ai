from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from harness.images import ImageProvider
from harness.tools.base import Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths


class ImageGenerateArguments(BaseModel):
    prompt: str = Field(min_length=1)
    output_path: str = "artifacts/generated-image.png"
    references: list[str] = Field(default_factory=list)


class ImageGenerateTool(Tool):
    name: ClassVar[str] = "image_generate"
    description: ClassVar[str] = "Generate an image through the configured image provider."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = ImageGenerateArguments

    def __init__(self, provider: ImageProvider, paths: WorkspacePaths) -> None:
        self._provider = provider
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = ImageGenerateArguments.model_validate(arguments.model_dump())
        output = self._paths.resolve(args.output_path)
        references = [self._require_reference(path) for path in args.references]
        result = await self._provider.generate(
            args.prompt,
            output,
            references=references,
        )
        path = result.path.resolve()
        self._paths.relative(path)
        if not path.is_file():
            return ToolResult.fail(f"Image provider did not create output: {args.output_path}")
        relative = self._paths.relative(path)
        return ToolResult.ok(
            {"path": relative, "metadata": result.metadata},
            artifacts=[relative],
        )

    def _require_reference(self, raw_path: str) -> Path:
        path = self._paths.resolve(raw_path)
        if not path.is_file():
            raise ValueError(f"Image reference not found: {raw_path}")
        return path
