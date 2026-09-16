from pathlib import Path

from harness.runtime import LatestImageVisionVerifier, VerificationRequest
from harness.vision import VisionResult


class FakeVisionProvider:
    def __init__(self, result: VisionResult) -> None:
        self._result = result
        self.calls: list[tuple[Path, str]] = []

    async def inspect(self, image_path: Path, prompt: str) -> VisionResult:
        self.calls.append((image_path, prompt))
        return self._result


async def test_visual_verifier_skips_runs_without_image_artifacts(tmp_path: Path) -> None:
    provider = FakeVisionProvider(VisionResult(description="unused", passed=False))
    verifier = LatestImageVisionVerifier(provider, tmp_path)

    result = await verifier.verify(
        VerificationRequest(
            session_id="s1",
            task="write a file",
            artifacts=["output.txt"],
        )
    )

    assert result.passed is True
    assert result.metadata == {"skipped": "no_image_artifact"}
    assert provider.calls == []


async def test_visual_verifier_uses_latest_image_and_propagates_decision(tmp_path: Path) -> None:
    older = tmp_path / "older.png"
    latest = tmp_path / "latest.png"
    older.write_bytes(b"old")
    latest.write_bytes(b"new")
    provider = FakeVisionProvider(
        VisionResult(
            description="the object is missing the requested texture",
            passed=False,
            metadata={"score": 0.4},
        )
    )
    verifier = LatestImageVisionVerifier(provider, tmp_path)

    result = await verifier.verify(
        VerificationRequest(
            session_id="s1",
            task="create a textured crate",
            proposed_content="done",
            artifacts=["older.png", "notes.txt", "latest.png"],
        )
    )

    assert result.passed is False
    assert "missing" in result.feedback
    assert result.metadata["artifact"] == "latest.png"
    assert result.metadata["score"] == 0.4
    assert provider.calls[0][0] == latest.resolve()
    assert "create a textured crate" in provider.calls[0][1]
