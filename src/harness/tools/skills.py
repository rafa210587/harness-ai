from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from harness.skills import RuntimeSkillLoader
from harness.tools.base import EmptyArguments, Tool, ToolResult, ToolRisk


class SkillLoadArguments(BaseModel):
    name: str = Field(min_length=1)


class SkillListTool(Tool):
    name: ClassVar[str] = "skill_list"
    description: ClassVar[str] = "List reusable runtime procedures available to the harness."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = EmptyArguments

    def __init__(self, loader: RuntimeSkillLoader) -> None:
        self._loader = loader

    async def execute(self, arguments: BaseModel) -> ToolResult:
        return ToolResult.ok({"skills": self._loader.list()})


class SkillLoadTool(Tool):
    name: ClassVar[str] = "skill_load"
    description: ClassVar[str] = (
        "Load one reusable runtime procedure by name when it is relevant to the current task."
    )
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = SkillLoadArguments

    def __init__(self, loader: RuntimeSkillLoader) -> None:
        self._loader = loader

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = SkillLoadArguments.model_validate(arguments.model_dump())
        try:
            skill = self._loader.load(args.name)
        except (FileNotFoundError, ValueError) as exc:
            return ToolResult.fail(str(exc))
        return ToolResult.ok(
            {
                "name": skill.name,
                "content": skill.content,
            }
        )
