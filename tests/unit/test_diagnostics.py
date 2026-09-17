from pathlib import Path

from harness.config import Settings
from harness.diagnostics import run_online_checks
from harness.llm import LLMProvider, LLMResponse, Message
from harness.process import ProcessResult


class FakeProvider(LLMProvider):
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        return LLMResponse(content="OK")


class FakeBrowser:
    started = False
    closed = False

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True


async def test_online_diagnostics_can_pass_with_fakes(tmp_path: Path) -> None:
    blender = tmp_path / "blender.exe"
    unity = tmp_path / "Unity.exe"
    blender.write_text("", encoding="utf-8")
    unity.write_text("", encoding="utf-8")

    async def fake_process_runner(
        arguments: list[str],
        *,
        cwd: Path | None = None,
        timeout_seconds: int = 300,
    ) -> ProcessResult:
        del cwd, timeout_seconds
        return ProcessResult(exit_code=0, stdout=f"ok:{arguments[0]}", stderr="")

    settings = Settings(
        _env_file=None,
        deepseek_api_key="test-key",
        blender_path=blender,
        unity_path=unity,
    )
    results = await run_online_checks(
        settings,
        provider_factory=lambda _settings: FakeProvider(),
        browser_factory=lambda _profile: FakeBrowser(),
        process_runner=fake_process_runner,
    )

    assert [result.ok for result in results] == [True, True, True, True]
    assert [result.name for result in results] == [
        "DeepSeek API",
        "Browser launch",
        "Blender launch",
        "Unity launch",
    ]
    assert results[1].detail == "chrome launched successfully"


async def test_online_diagnostics_report_missing_configuration(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("BLENDER_PATH", raising=False)
    monkeypatch.delenv("UNITY_PATH", raising=False)
    settings = Settings(_env_file=None)
    results = await run_online_checks(settings, browser_factory=lambda _profile: FakeBrowser())

    assert results[0].ok is False
    assert results[0].detail == "API key not configured"
    assert results[1].ok is True
    assert results[2].detail == "not configured"
    assert results[3].detail == "not configured"
