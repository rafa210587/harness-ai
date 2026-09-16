from __future__ import annotations

import json
from typing import Any, cast

from openai import AsyncOpenAI

from harness.config import Settings
from harness.llm.base import (
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    LLMUsage,
    Message,
    ToolCall,
)


class DeepSeekProvider(LLMProvider):
    """DeepSeek implementation using its OpenAI-compatible Chat Completions API."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self._settings = settings
        if client is not None:
            self._client = client
            return

        if settings.deepseek_api_key is None:
            raise LLMProviderError("DEEPSEEK_API_KEY is not configured")

        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key.get_secret_value(),
            base_url=settings.deepseek_base_url,
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload_messages = [self._message_to_api(message) for message in messages]

        try:
            response = await self._client.chat.completions.create(
                model=self._settings.deepseek_model,
                messages=cast(Any, payload_messages),
                tools=cast(Any, tools) if tools else None,
                tool_choice="auto" if tools else None,
            )
        except Exception as exc:  # provider boundary
            raise LLMProviderError(f"DeepSeek request failed: {exc}") from exc

        if not response.choices:
            raise LLMProviderError("DeepSeek returned no choices")

        choice = response.choices[0]
        response_message = choice.message
        parsed_calls: list[ToolCall] = []

        for tool_call in response_message.tool_calls or []:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise LLMProviderError(
                    f"DeepSeek returned invalid JSON for tool {tool_call.function.name}: {exc}"
                ) from exc

            if not isinstance(arguments, dict):
                raise LLMProviderError(
                    f"DeepSeek returned non-object arguments for tool {tool_call.function.name}"
                )

            parsed_calls.append(
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            )

        return LLMResponse(
            content=response_message.content,
            tool_calls=parsed_calls,
            finish_reason=choice.finish_reason,
            usage=self._normalize_usage(getattr(response, "usage", None)),
        )

    @staticmethod
    def _normalize_usage(usage: Any | None) -> LLMUsage | None:
        if usage is None:
            return None
        return LLMUsage(
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
        )

    @staticmethod
    def _message_to_api(message: Message) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }

        if message.tool_call_id is not None:
            payload["tool_call_id"] = message.tool_call_id

        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
                for call in message.tool_calls
            ]

        return payload
