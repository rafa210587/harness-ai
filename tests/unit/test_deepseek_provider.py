from types import SimpleNamespace

import pytest

from harness.config import Settings
from harness.llm import DeepSeekProvider, LLMProviderError, Message


class FakeCompletions:
    def __init__(self, response) -> None:
        self.response = response
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


class FakeClient:
    def __init__(self, response) -> None:
        self.completions = FakeCompletions(response)
        self.chat = SimpleNamespace(completions=self.completions)


def make_response(*, content=None, tool_calls=None, finish_reason="stop"):
    message = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


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
