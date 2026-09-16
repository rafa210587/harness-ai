from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from harness.tools.base import Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths
from harness.unity import UnityController


class UnityProjectArguments(BaseModel):
    project_path: str = "."


class UnityExecuteArguments(UnityProjectArguments):
    method_body: str = Field(min_length=1)
    expected_artifacts: list[str] = Field(default_factory=list)


class UnityProjectInfoTool(Tool):
    name: ClassVar[str] = "unity_project_info"
    description: ClassVar[str] = "Inspect basic Unity project metadata inside the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = UnityProjectArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = UnityProjectArguments.model_validate(arguments.model_dump())
        project = self._paths.resolve(args.project_path)
        assets = project / "Assets"
        settings = project / "ProjectSettings"
        if not project.is_dir() or not assets.is_dir() or not settings.is_dir():
            return ToolResult.fail(f"Not a Unity project: {args.project_path}")

        version_file = settings / "ProjectVersion.txt"
        version = version_file.read_text(encoding="utf-8") if version_file.is_file() else ""
        return ToolResult.ok(
            {
                "project_path": self._paths.relative(project),
                "project_version": version.strip(),
                "assets_exists": True,
            }
        )


class UnityExecuteEditorScriptTool(Tool):
    name: ClassVar[str] = "unity_execute_editor_script"
    description: ClassVar[str] = (
        "Execute inspectable generated C# inside the Unity Editor in batch mode."
    )
    risk: ClassVar[ToolRisk] = ToolRisk.DANGEROUS
    arguments_model: ClassVar[type[BaseModel]] = UnityExecuteArguments

    def __init__(self, controller: UnityController, paths: WorkspacePaths) -> None:
        self._controller = controller
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = UnityExecuteArguments.model_validate(arguments.model_dump())
        result = await self._controller.execute_editor_script(args.project_path, args.method_body)
        artifacts = [
            self._paths.relative(path)
            for raw in args.expected_artifacts
            if (path := self._paths.resolve(raw)).is_file()
        ]
        if result.timed_out:
            return ToolResult.fail(result.stderr)
        if result.exit_code != 0:
            return ToolResult.fail(result.stderr or f"Unity exited with {result.exit_code}")
        return ToolResult.ok(
            {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr},
            artifacts=artifacts,
        )
