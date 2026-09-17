from pathlib import Path

from harness.config import PermissionAction, Settings, load_settings


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    settings = Settings(_env_file=None)

    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_model == "deepseek-flash"
    assert settings.harness_workspace == Path("workspace")
    assert settings.agent_max_steps == 50
    assert settings.agent_llm_timeout_seconds == 120
    assert settings.agent_llm_max_attempts == 3
    assert settings.agent_llm_retry_base_seconds == 1.0


def test_settings_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_MODEL", "custom-model")
    monkeypatch.setenv("AGENT_MAX_STEPS", "12")
    monkeypatch.setenv("AGENT_LLM_MAX_ATTEMPTS", "4")

    settings = Settings(_env_file=None)

    assert settings.deepseek_model == "custom-model"
    assert settings.agent_max_steps == 12
    assert settings.agent_llm_max_attempts == 4


def test_load_settings_precedence_and_permissions(tmp_path: Path, monkeypatch) -> None:
    for name in (
        "HARNESS_WORKSPACE",
        "HARNESS_BROWSER_HEADLESS",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL",
        "AGENT_LLM_TIMEOUT_SECONDS",
        "AGENT_LLM_MAX_ATTEMPTS",
        "AGENT_LLM_RETRY_BASE_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "harness.yaml").write_text(
        """
workspace:
  root: ./yaml-workspace
agent:
  max_steps: 7
  llm_timeout_seconds: 45
  llm_max_attempts: 2
  llm_retry_base_seconds: 0.5
browser:
  headless: true
""".strip(),
        encoding="utf-8",
    )
    (config_dir / "models.yaml").write_text(
        """
providers:
  deepseek:
    base_url: https://yaml.example
    model: yaml-model
""".strip(),
        encoding="utf-8",
    )
    (config_dir / "permissions.yaml").write_text(
        """
read: auto
write: approval
dangerous: deny
tools:
  shell_run: approval
""".strip(),
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_MODEL=dotenv-model\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_MAX_STEPS", "13")

    settings = load_settings(config_dir=config_dir, env_file=env_file)

    assert settings.harness_workspace == Path("yaml-workspace")
    assert settings.harness_browser_headless is True
    assert settings.deepseek_base_url == "https://yaml.example"
    assert settings.deepseek_model == "dotenv-model"
    assert settings.agent_max_steps == 13
    assert settings.agent_llm_timeout_seconds == 45
    assert settings.agent_llm_max_attempts == 2
    assert settings.agent_llm_retry_base_seconds == 0.5
    assert settings.permissions.write is PermissionAction.APPROVAL
    assert settings.permissions.dangerous is PermissionAction.DENY
    assert settings.permissions.action_for("shell_run", "dangerous") is PermissionAction.APPROVAL
