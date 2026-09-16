from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class RuntimeSkill(BaseModel):
    name: str
    content: str
    path: Path


class RuntimeSkillLoader:
    """Load opt-in procedural Markdown skills from a bounded skills directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def list(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self.root.iterdir()
            if entry.is_dir()
            and not entry.name.startswith("_")
            and _SKILL_NAME.fullmatch(entry.name)
            and (entry / "SKILL.md").is_file()
        )

    def load(self, name: str) -> RuntimeSkill:
        if not _SKILL_NAME.fullmatch(name):
            raise ValueError(f"Invalid skill name: {name}")
        skill_dir = (self.root / name).resolve()
        try:
            skill_dir.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Skill escapes configured root: {name}") from exc

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            raise FileNotFoundError(f"Runtime skill not found: {name}")
        return RuntimeSkill(
            name=name,
            content=skill_file.read_text(encoding="utf-8"),
            path=skill_file,
        )
