import sys
from pathlib import Path

from harness.tools import ShellRunTool, WorkspacePaths


async def test_shell_returns_output_on_success(tmp_path: Path) -> None:
    tool = ShellRunTool(WorkspacePaths(tmp_path))
    result = await tool.execute(
        tool.validate_arguments(
            {
                "command": f'"{sys.executable}" -c "print(123)"',
                "cwd": ".",
                "timeout_seconds": 10,
            }
        )
    )

    assert result.success is True
    assert result.output["exit_code"] == 0
    assert "123" in result.output["stdout"]


async def test_shell_nonzero_exit_is_failure(tmp_path: Path) -> None:
    tool = ShellRunTool(WorkspacePaths(tmp_path))
    result = await tool.execute(
        tool.validate_arguments(
            {
                "command": f'"{sys.executable}" -c "import sys; sys.exit(7)"',
                "cwd": ".",
                "timeout_seconds": 10,
            }
        )
    )

    assert result.success is False
    assert result.output["exit_code"] == 7
    assert "code 7" in (result.error or "")
