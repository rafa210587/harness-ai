from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from uuid import uuid4

from harness.runtime.process import ProcessResult, run_process
from harness.tools.filesystem import WorkspacePaths

ProcessRunner = Callable[..., Awaitable[ProcessResult]]


class BlenderController:
    """Control Blender through background CLI execution and inspectable Python scripts."""

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

    async def execute_python(
        self,
        script: str,
        *,
        blend_file: str | None = None,
    ) -> ProcessResult:
        executable = self._require_executable()
        script_path = self._write_script(script)
        arguments = [str(executable)]
        if blend_file is not None:
            arguments.append(str(self._paths.resolve(blend_file)))
        arguments.extend(["--background", "--python", str(script_path)])
        return await self._process_runner(
            arguments,
            cwd=self._paths.root,
            timeout_seconds=self._timeout_seconds,
        )

    async def render(
        self,
        *,
        blend_file: str,
        output_path: str,
        frame: int = 1,
    ) -> tuple[ProcessResult, Path]:
        output = self._paths.resolve(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        script = "\n".join(
            [
                "import bpy",
                f"bpy.context.scene.frame_set({frame})",
                "bpy.context.scene.render.image_settings.file_format = 'PNG'",
                f"bpy.context.scene.render.filepath = {json.dumps(str(output))}",
                "bpy.ops.render.render(write_still=True)",
            ]
        )
        result = await self.execute_python(script, blend_file=blend_file)
        return result, output

    def _write_script(self, script: str) -> Path:
        script_dir = self._paths.resolve(".harness/blender/scripts")
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / f"{uuid4().hex}.py"
        script_path.write_text(script, encoding="utf-8")
        return script_path

    def _require_executable(self) -> Path:
        if self._executable is None:
            raise RuntimeError("BLENDER_PATH is not configured")
        if not self._executable.is_file():
            raise RuntimeError(f"Blender executable not found: {self._executable}")
        return self._executable
