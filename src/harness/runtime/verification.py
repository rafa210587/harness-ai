from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


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
