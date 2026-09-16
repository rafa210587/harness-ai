from pathlib import Path

import pytest

from harness.tools import (
    FilesystemCopyTool,
    FilesystemListTool,
    FilesystemMkdirTool,
    FilesystemMoveTool,
    FilesystemPatchTool,
    FilesystemReadTool,
    FilesystemSearchTool,
    FilesystemWriteTool,
    ToolRegistry,
    WorkspacePaths,
)


async def test_filesystem_tools_round_trip(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    registry = ToolRegistry()
    registry.register(FilesystemWriteTool(paths))
    registry.register(FilesystemReadTool(paths))
    registry.register(FilesystemListTool(paths))
    registry.register(FilesystemSearchTool(paths))
    registry.register(FilesystemPatchTool(paths))
    registry.register(FilesystemMkdirTool(paths))
    registry.register(FilesystemCopyTool(paths))
    registry.register(FilesystemMoveTool(paths))

    written = await registry.execute(
        "filesystem_write",
        {"path": "notes/example.txt", "content": "alpha\nbeta\n"},
    )
    assert written.success is True

    patched = await registry.execute(
        "filesystem_patch",
        {"path": "notes/example.txt", "old": "beta", "new": "gamma"},
    )
    assert patched.success is True

    read = await registry.execute("filesystem_read", {"path": "notes/example.txt"})
    assert read.success is True
    assert read.output["content"] == "alpha\ngamma\n"

    created = await registry.execute("filesystem_mkdir", {"path": "copies"})
    assert created.success is True

    copied = await registry.execute(
        "filesystem_copy",
        {"source": "notes/example.txt", "destination": "copies/example.txt"},
    )
    assert copied.success is True

    moved = await registry.execute(
        "filesystem_move",
        {"source": "copies/example.txt", "destination": "copies/moved.txt"},
    )
    assert moved.success is True
    assert (tmp_path / "copies/moved.txt").is_file()

    listed = await registry.execute("filesystem_list", {"path": "notes"})
    assert listed.success is True
    assert listed.output == [{"path": "notes/example.txt", "type": "file"}]

    searched = await registry.execute(
        "filesystem_search",
        {"path": ".", "query": "gamma", "glob": "*.txt"},
    )
    assert searched.success is True
    assert len(searched.output) == 2


async def test_patch_rejects_ambiguous_replacement(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    path = tmp_path / "repeat.txt"
    path.write_text("x x", encoding="utf-8")
    tool = FilesystemPatchTool(paths)

    result = await tool.execute(
        tool.validate_arguments({"path": "repeat.txt", "old": "x", "new": "y"})
    )

    assert result.success is False
    assert "found 2" in (result.error or "")
    assert path.read_text(encoding="utf-8") == "x x"


def test_workspace_paths_reject_escape(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)

    with pytest.raises(ValueError, match="escapes workspace"):
        paths.resolve("../outside.txt")


def test_workspace_paths_reject_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    link = workspace / "external"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available in this environment")

    paths = WorkspacePaths(workspace)

    with pytest.raises(ValueError, match="escapes workspace"):
        paths.resolve("external/secret.txt")
