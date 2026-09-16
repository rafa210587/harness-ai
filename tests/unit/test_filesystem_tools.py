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


def test_workspace_paths_protect_sensitive_files(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)

    for raw_path in (
        ".env",
        ".env.local",
        "nested/.env.production",
        "id_rsa",
        "nested/id_ed25519",
        "certs/client.pem",
        "certs/client.key",
        ".ssh/config",
        ".aws/credentials",
        "credentials.json",
        "secrets.json",
    ):
        with pytest.raises(ValueError, match="Sensitive workspace path is protected"):
            paths.resolve(raw_path)


@pytest.mark.parametrize("filename", [".env.example", ".env.sample", ".env.template"])
def test_workspace_paths_allow_safe_env_templates(tmp_path: Path, filename: str) -> None:
    paths = WorkspacePaths(tmp_path)

    assert paths.resolve(filename) == (tmp_path / filename).resolve()


async def test_filesystem_search_skips_sensitive_files(tmp_path: Path) -> None:
    secret = "super-secret-value"
    (tmp_path / ".env").write_text(f"DEEPSEEK_API_KEY={secret}\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("DEEPSEEK_API_KEY=example\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text(f"safe text {secret}\n", encoding="utf-8")

    registry = ToolRegistry()
    registry.register(FilesystemSearchTool(WorkspacePaths(tmp_path)))

    result = await registry.execute(
        "filesystem_search",
        {"path": ".", "query": secret, "glob": "*"},
    )

    assert result.success is True
    assert result.output == [{"path": "notes.txt", "line": 1, "text": f"safe text {secret}"}]


async def test_filesystem_read_blocks_env_but_allows_example(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=value\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("SECRET=example\n", encoding="utf-8")
    registry = ToolRegistry()
    registry.register(FilesystemReadTool(WorkspacePaths(tmp_path)))

    blocked = await registry.execute("filesystem_read", {"path": ".env"})
    allowed = await registry.execute("filesystem_read", {"path": ".env.example"})

    assert blocked.success is False
    assert "Sensitive workspace path is protected" in (blocked.error or "")
    assert allowed.success is True
    assert allowed.output["content"] == "SECRET=example\n"
