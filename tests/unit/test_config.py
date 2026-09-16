from pathlib import Path

from harness.config import Settings


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    settings = Settings(_env_file=None)

    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_model == "deepseek-flash"
    assert settings.harness_workspace == Path("workspace")
    assert settings.agent_max_steps == 50


def test_settings_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_MODEL", "custom-model")
    monkeypatch.setenv("AGENT_MAX_STEPS", "12")

    settings = Settings(_env_file=None)

    assert settings.deepseek_model == "custom-model"
    assert settings.agent_max_steps == 12
