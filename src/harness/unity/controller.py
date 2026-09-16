from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from uuid import uuid4

from harness.runtime.process import ProcessResult, run_process
from harness.tools.filesystem import WorkspacePaths

ProcessRunner = Callable[..., Awaitable[ProcessResult]]


class UnityController:
    """Control Unity through batch-mode Editor execution."""

    def __init__(
        self,
        executable: Path | None,
        paths: WorkspacePaths,
        *,
        process_runner: ProcessRunner = run_process,
        timeout_seconds: int = 300,
    ) -> None:
        self._executable = executable
        self._paths = paths
        self._process_runner = process_runner
        self._timeout_seconds = timeout_seconds

    async def run_method(self, project_path: str, execute_method: str) -> ProcessResult:
        executable = self._require_executable()
        project = self._require_project(project_path)
        arguments = [
            str(executable),
            "-batchmode",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            execute_method,
            "-logFile",
            "-",
        ]
        return await self._process_runner(
            arguments,
            cwd=project,
            timeout_seconds=self._timeout_seconds,
        )

    async def execute_editor_script(self, project_path: str, method_body: str) -> ProcessResult:
        project = self._require_project(project_path)
        class_name = f"HarnessGeneratedTask_{uuid4().hex}"
        source = "\n".join(
            [
                "using UnityEditor;",
                "using UnityEngine;",
                "",
                f"public static class {class_name}",
                "{",
                "    public static void Run()",
                "    {",
                _indent(method_body, 8),
                "    }",
                "}",
                "",
            ]
        )
        generated_dir = project / "Assets" / "Editor" / "HarnessGenerated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        script_path = generated_dir / f"{class_name}.cs"
        script_path.write_text(source, encoding="utf-8")
        return await self.run_method(project_path, f"{class_name}.Run")

    def _require_project(self, project_path: str) -> Path:
        project = self._paths.resolve(project_path)
        if not project.is_dir():
            raise RuntimeError(f"Unity project directory not found: {project_path}")
        if not (project / "Assets").is_dir() or not (project / "ProjectSettings").is_dir():
            raise RuntimeError(f"Not a Unity project: {project_path}")
        return project

    def _require_executable(self) -> Path:
        if self._executable is None:
            raise RuntimeError("UNITY_PATH is not configured")
        if not self._executable.is_file():
            raise RuntimeError(f"Unity executable not found: {self._executable}")
        return self._executable


def _indent(source: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in source.splitlines())
