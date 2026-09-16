from typing import Any

from harness.llm import LLMProvider, LLMResponse, Message
from harness.runtime import AgentLoop, AgentStatus, VerificationRequest, VerificationResult
from harness.tools import ToolRegistry


class ScriptedProvider(LLMProvider):
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = responses
        self.calls: list[list[Message]] = []

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        self.calls.append([message.model_copy(deep=True) for message in messages])
        return self._responses.pop(0)


class ScriptedVerifier:
    def __init__(self, results: list[VerificationResult]) -> None:
        self._results = results
        self.requests: list[VerificationRequest] = []

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        self.requests.append(request)
        return self._results.pop(0)


async def test_verification_feedback_forces_agent_to_continue() -> None:
    provider = ScriptedProvider(
        [
            LLMResponse(content="first answer", finish_reason="stop"),
            LLMResponse(content="corrected answer", finish_reason="stop"),
        ]
    )
    verifier = ScriptedVerifier(
        [
            VerificationResult(passed=False, feedback="result is incomplete"),
            VerificationResult(passed=True),
        ]
    )

    result = await AgentLoop(provider, ToolRegistry(), verifier=verifier).run("do the task")

    assert result.status is AgentStatus.COMPLETED
    assert result.content == "corrected answer"
    assert [request.attempt for request in verifier.requests] == [1, 2]
    assert any(
        message.role == "system" and "result is incomplete" in (message.content or "")
        for message in provider.calls[1]
    )


async def test_verification_stops_after_retry_limit() -> None:
    provider = ScriptedProvider(
        [
            LLMResponse(content="bad 1", finish_reason="stop"),
            LLMResponse(content="bad 2", finish_reason="stop"),
        ]
    )
    verifier = ScriptedVerifier(
        [
            VerificationResult(passed=False, feedback="still wrong"),
            VerificationResult(passed=False, feedback="still wrong"),
        ]
    )

    result = await AgentLoop(
        provider,
        ToolRegistry(),
        verifier=verifier,
        max_verification_retries=1,
    ).run("do the task")

    assert result.status is AgentStatus.FAILED
    assert result.reason is not None
    assert "Verification failed" in result.reason
