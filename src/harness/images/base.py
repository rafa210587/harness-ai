from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class ImageGenerationResult(BaseModel):
    path: Path
    metadata: dict[str, object] = Field(default_factory=dict)


class ImageProvider(Protocol):
    """Provider-neutral image generation contract."""

    async def generate(
        self,
        prompt: str,
        output_path: Path,
        *,
        references: list[Path] | None = None,
    ) -> ImageGenerationResult: ...
