import os
from pathlib import Path

import pytest

from harness.tools import WorkspacePaths
from harness.unity import UnityController

pytestmark = pytest.mark.unity


def _unity_executable() -> Path:
    raw = os.environ.get("UNITY_PATH")
    if not raw:
        pytest.skip("UNITY_PATH is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"Unity executable not found: {path}")
    return path


def _unity_smoke_project() -> Path:
    raw = os.environ.get("HARNESS_UNITY_SMOKE_PROJECT")
    if not raw:
        pytest.skip("HARNESS_UNITY_SMOKE_PROJECT is not configured")
    path = Path(raw).resolve()
    if not (path / "Assets").is_dir() or not (path / "ProjectSettings").is_dir():
        pytest.skip(f"Not a Unity smoke project: {path}")
    return path


async def test_unity_batchmode_executes_generated_editor_script() -> None:
    executable = _unity_executable()
    project = _unity_smoke_project()
    paths = WorkspacePaths(project.parent)
    controller = UnityController(executable, paths, timeout_seconds=300)
    marker = project / "HarnessSmoke.txt"
    if marker.exists():
        marker.unlink()

    result = await controller.execute_editor_script(
        project.name,
        'System.IO.File.WriteAllText("HarnessSmoke.txt", "ok");',
    )

    assert result.timed_out is False
    assert result.exit_code == 0, result.stderr or result.stdout
    assert marker.read_text(encoding="utf-8") == "ok"

    marker.unlink(missing_ok=True)
