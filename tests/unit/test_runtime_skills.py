from pathlib import Path

import pytest

from harness.skills import RuntimeSkillLoader
from harness.tools import SkillListTool, SkillLoadTool, ToolRegistry


def _create_skill(root: Path, name: str, content: str) -> None:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(content, encoding="utf-8")


async def test_runtime_skill_tools_list_and_load_valid_skills(tmp_path: Path) -> None:
    _create_skill(tmp_path, "create-prop", "# Create Prop\nUse Blender tools.")
    _create_skill(tmp_path, "inspect-scene", "# Inspect Scene\nUse Unity tools.")
    _create_skill(tmp_path, "_examples", "# Ignore me")
    (tmp_path / "not-a-skill").mkdir()

    loader = RuntimeSkillLoader(tmp_path)
    registry = ToolRegistry()
    registry.register(SkillListTool(loader))
    registry.register(SkillLoadTool(loader))

    listed = await registry.execute("skill_list", {})
    loaded = await registry.execute("skill_load", {"name": "create-prop"})

    assert listed.success is True
    assert listed.output == {"skills": ["create-prop", "inspect-scene"]}
    assert loaded.success is True
    assert "Use Blender tools" in loaded.output["content"]


async def test_runtime_skill_tool_rejects_unknown_or_invalid_names(tmp_path: Path) -> None:
    loader = RuntimeSkillLoader(tmp_path)
    tool = SkillLoadTool(loader)

    unknown = await tool.execute(tool.validate_arguments({"name": "missing-skill"}))
    invalid = await tool.execute(tool.validate_arguments({"name": "../escape"}))

    assert unknown.success is False
    assert invalid.success is False


def test_runtime_skill_loader_blocks_direct_path_escape(tmp_path: Path) -> None:
    loader = RuntimeSkillLoader(tmp_path)

    with pytest.raises(ValueError, match="Invalid skill name"):
        loader.load("../outside")


def test_runtime_skill_loader_blocks_symlinked_skill_file_escape(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    skill_dir = root / "linked-skill"
    skill_dir.mkdir()
    link = skill_dir / "SKILL.md"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available in this environment")

    loader = RuntimeSkillLoader(root)

    with pytest.raises(ValueError, match="Skill file escapes configured root"):
        loader.load("linked-skill")
    assert "linked-skill" not in loader.list()


def test_runtime_skill_loader_rejects_oversized_skill(tmp_path: Path) -> None:
    _create_skill(tmp_path, "large-skill", "x" * 33)
    loader = RuntimeSkillLoader(tmp_path, max_skill_bytes=32)

    with pytest.raises(ValueError, match="too large"):
        loader.load("large-skill")
    assert "large-skill" not in loader.list()
