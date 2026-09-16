import json
import os
from pathlib import Path

import pytest

from harness.blender import BlenderController
from harness.tools import WorkspacePaths

pytestmark = pytest.mark.blender


def _blender_executable() -> Path:
    raw = os.environ.get("BLENDER_PATH")
    if not raw:
        pytest.skip("BLENDER_PATH is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"Blender executable not found: {path}")
    return path


async def test_blender_background_python_and_render(tmp_path: Path) -> None:
    executable = _blender_executable()
    paths = WorkspacePaths(tmp_path)
    controller = BlenderController(executable, paths, timeout_seconds=180)
    blend_file = tmp_path / "smoke.blend"

    script = "\n".join(
        [
            "import bpy",
            "bpy.context.scene.render.resolution_x = 64",
            "bpy.context.scene.render.resolution_y = 64",
            "bpy.context.scene.render.resolution_percentage = 100",
            f"bpy.ops.wm.save_as_mainfile(filepath={json.dumps(str(blend_file))})",
        ]
    )
    create_result = await controller.execute_python(script)

    assert create_result.timed_out is False
    assert create_result.exit_code == 0, create_result.stderr
    assert blend_file.is_file()

    render_result, output = await controller.render(
        blend_file="smoke.blend",
        output_path="artifacts/smoke.png",
        frame=1,
    )

    assert render_result.timed_out is False
    assert render_result.exit_code == 0, render_result.stderr
    assert output.is_file()
    assert output.stat().st_size > 0
