from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    description: str
    passed: bool | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class VisionProvider(Protocol):
    """Provider-neutral visual inspection contract."""

    async def inspect(
        self,
        image_path: Path,
        prompt: str,
    ) -> VisionResult: ...
