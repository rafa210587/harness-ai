from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_DEFAULT_MAX_SKILL_BYTES = 64 * 1024


class RuntimeSkill(BaseModel):
    name: str
    content: str
    path: Path


class RuntimeSkillLoader:
    """Load opt-in procedural Markdown skills from a bounded skills directory."""

    def __init__(self, root: Path, *, max_skill_bytes: int = _DEFAULT_MAX_SKILL_BYTES) -> None:
        if max_skill_bytes < 1:
            raise ValueError("max_skill_bytes must be at least 1")
        self.root = root.resolve()
        self._max_skill_bytes = max_skill_bytes

    def list(self) -> list[str]:
        if not self.root.is_dir():
            return []

        names: list[str] = []
        for entry in self.root.iterdir():
            if not entry.is_dir() or entry.name.startswith("_"):
                continue
            if not _SKILL_NAME.fullmatch(entry.name):
                continue
            try:
                self._resolve_skill_file(entry.name)
            except (FileNotFoundError, ValueError):
                continue
            names.append(entry.name)
        return sorted(names)

    def load(self, name: str) -> RuntimeSkill:
        skill_file = self._resolve_skill_file(name)
        return RuntimeSkill(
            name=name,
            content=skill_file.read_text(encoding="utf-8"),
            path=skill_file,
        )

    def _resolve_skill_file(self, name: str) -> Path:
        if not _SKILL_NAME.fullmatch(name):
            raise ValueError(f"Invalid skill name: {name}")

        skill_dir = (self.root / name).resolve()
        try:
            skill_dir.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Skill escapes configured root: {name}") from exc

        skill_file = (skill_dir / "SKILL.md").resolve()
        try:
            skill_file.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Skill file escapes configured root: {name}") from exc

        if not skill_file.is_file():
            raise FileNotFoundError(f"Runtime skill not found: {name}")
        if skill_file.stat().st_size > self._max_skill_bytes:
            raise ValueError(
                f"Runtime skill is too large: {name} exceeds {self._max_skill_bytes} bytes"
            )
        return skill_file
