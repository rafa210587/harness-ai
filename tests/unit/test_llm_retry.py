import asyncio
from typing import Any

import pytest

from harness.llm import LLMProvider, LLMProviderError, LLMResponse, Message, RetryingLLMProvider


class ScriptedProvider(LLMProvider):
    def __init__(self, outcomes: list[LLMResponse | Exception]) -> None:
        self._outcomes = outcomes
        self.calls = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        del messages, tools
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class SlowProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        del messages, tools
        self.calls += 1
        await asyncio.sleep(2)
        return LLMResponse(content="late")


async def test_retrying_provider_returns_first_success_without_retry() -> None:
    inner = ScriptedProvider([LLMResponse(content="ok")])
    provider = RetryingLLMProvider(inner, retry_base_seconds=0)

    response = await provider.complete([Message(role="user", content="hello")])

    assert response.content == "ok"
    assert inner.calls == 1


async def test_retrying_provider_retries_retryable_error() -> None:
    inner = ScriptedProvider(
        [
            LLMProviderError("temporary", retryable=True),
            LLMResponse(content="recovered"),
        ]
    )
    provider = RetryingLLMProvider(inner, max_attempts=3, retry_base_seconds=0)

    response = await provider.complete([Message(role="user", content="hello")])

    assert response.content == "recovered"
    assert inner.calls == 2


async def test_retrying_provider_does_not_retry_permanent_error() -> None:
    inner = ScriptedProvider([LLMProviderError("bad request", retryable=False)])
    provider = RetryingLLMProvider(inner, max_attempts=3, retry_base_seconds=0)

    with pytest.raises(LLMProviderError, match="bad request"):
        await provider.complete([Message(role="user", content="hello")])

    assert inner.calls == 1


async def test_retrying_provider_retries_timeout_and_then_fails() -> None:
    inner = SlowProvider()
    provider = RetryingLLMProvider(
        inner,
        timeout_seconds=1,
        max_attempts=2,
        retry_base_seconds=0,
    )

    with pytest.raises(LLMProviderError, match="timed out") as error:
        await provider.complete([Message(role="user", content="hello")])

    assert error.value.retryable is True
    assert inner.calls == 2
