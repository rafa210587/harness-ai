from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from harness.blender import BlenderController
from harness.tools.base import Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths


class ExecutePythonArguments(BaseModel):
    script: str = Field(min_length=1)
    blend_file: str | None = None
    expected_artifacts: list[str] = Field(default_factory=list)


class RenderArguments(BaseModel):
    blend_file: str
    output_path: str = "artifacts/blender-render.png"
    frame: int = Field(default=1, ge=0)


class BlenderExecutePythonTool(Tool):
    name: ClassVar[str] = "blender_execute_python"
    description: ClassVar[str] = "Execute an inspectable Python script in Blender background mode."
    risk: ClassVar[ToolRisk] = ToolRisk.DANGEROUS
    arguments_model: ClassVar[type[BaseModel]] = ExecutePythonArguments

    def __init__(self, controller: BlenderController, paths: WorkspacePaths) -> None:
        self._controller = controller
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = ExecutePythonArguments.model_validate(arguments.model_dump())
        result = await self._controller.execute_python(args.script, blend_file=args.blend_file)
        artifacts = [
            self._paths.relative(path)
            for raw in args.expected_artifacts
            if (path := self._paths.resolve(raw)).is_file()
        ]
        if result.timed_out:
            return ToolResult.fail(result.stderr)
        if result.exit_code != 0:
            return ToolResult.fail(result.stderr or f"Blender exited with {result.exit_code}")
        return ToolResult.ok(
            {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr},
            artifacts=artifacts,
        )


class BlenderRenderTool(Tool):
    name: ClassVar[str] = "blender_render"
    description: ClassVar[str] = "Render one frame from a .blend file to a PNG inside the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = RenderArguments

    def __init__(self, controller: BlenderController, paths: WorkspacePaths) -> None:
        self._controller = controller
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = RenderArguments.model_validate(arguments.model_dump())
        result, output = await self._controller.render(
            blend_file=args.blend_file,
            output_path=args.output_path,
            frame=args.frame,
        )
        if result.timed_out:
            return ToolResult.fail(result.stderr)
        if result.exit_code != 0:
            return ToolResult.fail(result.stderr or f"Blender exited with {result.exit_code}")
        if not output.is_file():
            return ToolResult.fail(f"Blender reported success but render was not created: {args.output_path}")
        relative = self._paths.relative(output)
        return ToolResult.ok(
            {"path": relative, "stdout": result.stdout, "stderr": result.stderr},
            artifacts=[relative],
        )
