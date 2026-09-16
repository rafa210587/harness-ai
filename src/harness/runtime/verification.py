from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from harness.vision import VisionProvider

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class VerificationRequest(BaseModel):
    session_id: str
    task: str
    proposed_content: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    attempt: int = 1


class VerificationResult(BaseModel):
    passed: bool
    feedback: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class RunVerifier(Protocol):
    """Verify a proposed terminal result before the agent run is accepted as complete."""

    async def verify(self, request: VerificationRequest) -> VerificationResult: ...


class LatestImageVisionVerifier:
    """Verify the most recent image artifact and skip non-visual runs."""

    def __init__(self, provider: VisionProvider, workspace: Path) -> None:
        self._provider = provider
        self._workspace = workspace.resolve()

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        artifact = self._latest_image_artifact(request.artifacts)
        if artifact is None:
            return VerificationResult(
                passed=True,
                metadata={"skipped": "no_image_artifact"},
            )

        image_path = self._resolve_artifact(artifact)
        if not image_path.is_file():
            return VerificationResult(
                passed=False,
                feedback=f"Visual artifact no longer exists: {artifact}",
                metadata={"artifact": artifact},
            )

        inspection = await self._provider.inspect(
            image_path,
            self._prompt(request),
        )
        passed = inspection.passed is True
        feedback = inspection.description
        if inspection.passed is None:
            feedback = (
                "Vision provider returned no pass/fail decision. "
                f"Assessment: {inspection.description}"
            )
        return VerificationResult(
            passed=passed,
            feedback=feedback,
            metadata={
                "artifact": artifact,
                **inspection.metadata,
            },
        )

    def _latest_image_artifact(self, artifacts: list[str]) -> str | None:
        for artifact in reversed(artifacts):
            if Path(artifact).suffix.lower() in _IMAGE_SUFFIXES:
                return artifact
        return None

    def _resolve_artifact(self, artifact: str) -> Path:
        path = (self._workspace / artifact).resolve()
        try:
            path.relative_to(self._workspace)
        except ValueError as exc:
            raise ValueError(f"Artifact escapes workspace: {artifact}") from exc
        return path

    @staticmethod
    def _prompt(request: VerificationRequest) -> str:
        proposed = request.proposed_content or ""
        return (
            "Verify whether this image satisfies the original task. "
            "Set passed=true only when the visual result is acceptable.\n\n"
            f"Original task:\n{request.task}\n\n"
            f"Proposed final response:\n{proposed}"
        )
