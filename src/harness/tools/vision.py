from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from harness.tools.base import Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths
from harness.vision import VisionProvider


class VisionInspectArguments(BaseModel):
    image_path: str
    prompt: str = Field(min_length=1)


class VisionInspectTool(Tool):
    name: ClassVar[str] = "vision_inspect"
    description: ClassVar[str] = "Inspect an image artifact with the configured vision provider."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = VisionInspectArguments

    def __init__(self, provider: VisionProvider, paths: WorkspacePaths) -> None:
        self._provider = provider
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = VisionInspectArguments.model_validate(arguments.model_dump())
        image = self._paths.resolve(args.image_path)
        if not image.is_file():
            return ToolResult.fail(f"Image not found: {args.image_path}")
        result = await self._provider.inspect(image, args.prompt)
        return ToolResult.ok(result.model_dump(mode="json"))
