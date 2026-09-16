from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class ToolRisk(StrEnum):
    READ = "read"
    WRITE = "write"
    DANGEROUS = "dangerous"


class EmptyArguments(BaseModel):
    pass


class ToolResult(BaseModel):
    success: bool
    output: Any = None
    error: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    retryable: bool = False

    @classmethod
    def ok(cls, output: Any = None, *, artifacts: list[str] | None = None) -> ToolResult:
        return cls(success=True, output=output, artifacts=artifacts or [])

    @classmethod
    def fail(cls, error: str, *, retryable: bool = False) -> ToolResult:
        return cls(success=False, error=error, retryable=retryable)


class Tool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    risk: ClassVar[ToolRisk]
    arguments_model: ClassVar[type[BaseModel]] = EmptyArguments

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.arguments_model.model_json_schema(),
            },
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> BaseModel:
        return self.arguments_model.model_validate(arguments)

    @abstractmethod
    async def execute(self, arguments: BaseModel) -> ToolResult:
        """Execute already validated arguments and return a normalized result."""
