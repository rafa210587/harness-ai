from __future__ import annotations

import asyncio
from typing import Any

from harness.llm.base import LLMProvider, LLMProviderError, LLMResponse, Message


class RetryingLLMProvider(LLMProvider):
    """Apply timeout and bounded retries to provider calls without retrying tools."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        timeout_seconds: int = 120,
        max_attempts: int = 3,
        retry_base_seconds: float = 1.0,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if retry_base_seconds < 0:
            raise ValueError("retry_base_seconds cannot be negative")
        self._provider = provider
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._retry_base_seconds = retry_base_seconds

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        last_error: LLMProviderError | None = None

        for attempt in range(1, self._max_attempts + 1):
            try:
                return await asyncio.wait_for(
                    self._provider.complete(messages, tools=tools),
                    timeout=self._timeout_seconds,
                )
            except TimeoutError as exc:
                last_error = LLMProviderError(
                    f"LLM request timed out after {self._timeout_seconds}s",
                    retryable=True,
                )
                last_error.__cause__ = exc
            except LLMProviderError as exc:
                last_error = exc

            if not last_error.retryable or attempt >= self._max_attempts:
                raise last_error

            delay = self._retry_base_seconds * (2 ** (attempt - 1))
            if delay > 0:
                await asyncio.sleep(delay)

        raise RuntimeError("LLM retry loop exited unexpectedly")
