from types import SimpleNamespace

import pytest

from harness.config import Settings
from harness.llm import DeepSeekProvider, LLMProviderError, Message


class RateLimitError(RuntimeError):
    pass


class BadRequestError(RuntimeError):
    pass


class FakeCompletions:
    def __init__(self, response) -> None:
        self.response = response
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeClient:
    def __init__(self, response) -> None:
        self.completions = FakeCompletions(response)
        self.chat = SimpleNamespace(completions=self.completions)


def make_response(*, content=None, tool_calls=None, finish_reason="stop", usage=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=usage)


def make_tool_call(arguments: str):
    return SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="filesystem_list", arguments=arguments),
    )


async def test_provider_normalizes_text_response() -> None:
    client = FakeClient(make_response(content="done"))
    provider = DeepSeekProvider(Settings(_env_file=None), client=client)

    response = await provider.complete([Message(role="user", content="hello")])

    assert response.content == "done"
    assert response.tool_calls == []
    assert client.completions.kwargs["model"] == "deepseek-flash"


async def test_provider_normalizes_token_usage() -> None:
    usage = SimpleNamespace(prompt_tokens=120, completion_tokens=30, total_tokens=150)
    client = FakeClient(make_response(content="done", usage=usage))
    provider = DeepSeekProvider(Settings(_env_file=None), client=client)

    response = await provider.complete([Message(role="user", content="hello")])

    assert response.usage is not None
    assert response.usage.input_tokens == 120
    assert response.usage.output_tokens == 30
    assert response.usage.total_tokens == 150


async def test_provider_normalizes_tool_call() -> None:
    client = FakeClient(
        make_response(
            tool_calls=[make_tool_call('{"path": "."}')],
            finish_reason="tool_calls",
        )
    )
    provider = DeepSeekProvider(Settings(_env_file=None), client=client)

    response = await provider.complete(
        [Message(role="user", content="list files")],
        tools=[{"type": "function", "function": {"name": "filesystem_list"}}],
    )

    assert response.tool_calls[0].name == "filesystem_list"
    assert response.tool_calls[0].arguments == {"path": "."}
    assert client.completions.kwargs["tool_choice"] == "auto"


async def test_provider_rejects_invalid_tool_json() -> None:
    client = FakeClient(make_response(tool_calls=[make_tool_call("not-json")]))
    provider = DeepSeekProvider(Settings(_env_file=None), client=client)

    with pytest.raises(LLMProviderError, match="invalid JSON"):
        await provider.complete([Message(role="user", content="list files")])


async def test_provider_marks_transient_transport_failure_retryable() -> None:
    provider = DeepSeekProvider(
        Settings(_env_file=None),
        client=FakeClient(RateLimitError("slow down")),
    )

    with pytest.raises(LLMProviderError) as error:
        await provider.complete([Message(role="user", content="hello")])

    assert error.value.retryable is True


async def test_provider_keeps_permanent_failure_non_retryable() -> None:
    provider = DeepSeekProvider(
        Settings(_env_file=None),
        client=FakeClient(BadRequestError("invalid request")),
    )

    with pytest.raises(LLMProviderError) as error:
        await provider.complete([Message(role="user", content="hello")])

    assert error.value.retryable is False
