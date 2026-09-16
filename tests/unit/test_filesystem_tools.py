from pathlib import Path

from harness.tools import (
    FilesystemListTool,
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

    written = await registry.execute(
        "filesystem_write",
        {"path": "notes/example.txt", "content": "alpha\nbeta\n"},
    )
    assert written.success is True

    read = await registry.execute("filesystem_read", {"path": "notes/example.txt"})
    assert read.success is True
    assert read.output["content"] == "alpha\nbeta\n"

    listed = await registry.execute("filesystem_list", {"path": "notes"})
    assert listed.success is True
    assert listed.output == [{"path": "notes/example.txt", "type": "file"}]

    searched = await registry.execute(
        "filesystem_search",
        {"path": ".", "query": "beta", "glob": "*.txt"},
    )
    assert searched.success is True
    assert searched.output[0]["line"] == 2


def test_workspace_paths_reject_escape(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)

    try:
        paths.resolve("../outside.txt")
    except ValueError as exc:
        assert "escapes workspace" in str(exc)
    else:
        raise AssertionError("workspace escape should be rejected")
