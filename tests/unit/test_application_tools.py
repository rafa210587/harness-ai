from pathlib import Path

from harness.process import ProcessResult
from harness.tools import (
    BlenderExecutePythonTool,
    BlenderRenderTool,
    UnityProjectInfoTool,
    WorkspacePaths,
)


class FakeBlenderController:
    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute_python(
        self,
        script: str,
        *,
        blend_file: str | None = None,
    ) -> ProcessResult:
        return ProcessResult(exit_code=0, stdout=f"ran:{len(script)}", stderr="")

    async def render(
        self,
        *,
        blend_file: str,
        output_path: str,
        frame: int = 1,
    ) -> tuple[ProcessResult, Path]:
        output = self._paths.resolve(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"png")
        return ProcessResult(exit_code=0, stdout="rendered", stderr=""), output


async def test_blender_tools_return_artifacts(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    controller = FakeBlenderController(paths)
    (tmp_path / "scene.blend").write_bytes(b"blend")

    render = BlenderRenderTool(controller, paths)  # type: ignore[arg-type]
    result = await render.execute(
        render.validate_arguments(
            {"blend_file": "scene.blend", "output_path": "artifacts/render.png", "frame": 1}
        )
    )

    assert result.success is True
    assert result.artifacts == ["artifacts/render.png"]

    arbitrary = BlenderExecutePythonTool(controller, paths)  # type: ignore[arg-type]
    assert arbitrary.risk.value == "dangerous"


async def test_unity_project_info_reads_project_version(tmp_path: Path) -> None:
    project = tmp_path / "game"
    (project / "Assets").mkdir(parents=True)
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.0.1f1\n",
        encoding="utf-8",
    )

    tool = UnityProjectInfoTool(WorkspacePaths(tmp_path))
    result = await tool.execute(tool.validate_arguments({"project_path": "game"}))

    assert result.success is True
    assert "6000.0.1f1" in result.output["project_version"]
