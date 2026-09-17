from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PermissionAction(StrEnum):
    AUTO = "auto"
    APPROVAL = "approval"
    DENY = "deny"


class BrowserChannel(StrEnum):
    CHROME = "chrome"
    PLAYWRIGHT = "playwright"

    @property
    def playwright_channel(self) -> str | None:
        """Translate harness channel selection to Playwright's launch option."""
        if self is BrowserChannel.PLAYWRIGHT:
            return None
        return self.value


class PermissionSettings(BaseModel):
    """Deterministic runtime permission policy."""

    read: PermissionAction = PermissionAction.AUTO
    write: PermissionAction = PermissionAction.AUTO
    dangerous: PermissionAction = PermissionAction.APPROVAL
    tools: dict[str, PermissionAction] = Field(default_factory=dict)

    def action_for(self, tool_name: str, risk: str) -> PermissionAction:
        override = self.tools.get(tool_name)
        if override is not None:
            return override
        return {
            "read": self.read,
            "write": self.write,
            "dangerous": self.dangerous,
        }.get(risk, PermissionAction.DENY)


class Settings(BaseSettings):
    """Typed runtime configuration loaded from YAML, `.env`, and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    harness_data_dir: Path = Path("./data")
    harness_workspace: Path = Path("./workspace")
    harness_skills_dir: Path = Path("./skills")
    harness_log_level: str = "INFO"

    harness_browser_profile: Path = Path("./data/browser-profile")
    harness_browser_headless: bool = False
    harness_browser_channel: BrowserChannel = BrowserChannel.CHROME

    blender_path: Path | None = None
    unity_path: Path | None = None

    agent_max_steps: int = Field(default=50, ge=1)
    agent_max_consecutive_errors: int = Field(default=5, ge=1)
    agent_max_tool_runtime_seconds: int = Field(default=300, ge=1)
    agent_llm_timeout_seconds: int = Field(default=120, ge=1)
    agent_llm_max_attempts: int = Field(default=3, ge=1, le=10)
    agent_llm_retry_base_seconds: float = Field(default=1.0, ge=0.0, le=60.0)

    context_max_messages: int = Field(default=40, ge=8)
    context_keep_recent: int = Field(default=16, ge=4)

    permissions: PermissionSettings = Field(default_factory=PermissionSettings)


_ENV_TO_FIELD = {
    "DEEPSEEK_API_KEY": "deepseek_api_key",
    "DEEPSEEK_BASE_URL": "deepseek_base_url",
    "DEEPSEEK_MODEL": "deepseek_model",
    "HARNESS_DATA_DIR": "harness_data_dir",
    "HARNESS_WORKSPACE": "harness_workspace",
    "HARNESS_SKILLS_DIR": "harness_skills_dir",
    "HARNESS_LOG_LEVEL": "harness_log_level",
    "HARNESS_BROWSER_PROFILE": "harness_browser_profile",
    "HARNESS_BROWSER_HEADLESS": "harness_browser_headless",
    "HARNESS_BROWSER_CHANNEL": "harness_browser_channel",
    "BLENDER_PATH": "blender_path",
    "UNITY_PATH": "unity_path",
    "AGENT_MAX_STEPS": "agent_max_steps",
    "AGENT_MAX_CONSECUTIVE_ERRORS": "agent_max_consecutive_errors",
    "AGENT_MAX_TOOL_RUNTIME_SECONDS": "agent_max_tool_runtime_seconds",
    "AGENT_LLM_TIMEOUT_SECONDS": "agent_llm_timeout_seconds",
    "AGENT_LLM_MAX_ATTEMPTS": "agent_llm_max_attempts",
    "AGENT_LLM_RETRY_BASE_SECONDS": "agent_llm_retry_base_seconds",
    "CONTEXT_MAX_MESSAGES": "context_max_messages",
    "CONTEXT_KEEP_RECENT": "context_keep_recent",
}


def load_settings(
    *,
    config_dir: Path = Path("config"),
    env_file: Path = Path(".env"),
) -> Settings:
    """Load defaults < YAML < .env < process environment."""
    values: dict[str, Any] = {}
    values.update(_harness_values(_load_yaml(config_dir / "harness.yaml")))
    values.update(_model_values(_load_yaml(config_dir / "models.yaml")))

    permissions_yaml = _load_yaml(config_dir / "permissions.yaml")
    if permissions_yaml:
        values["permissions"] = PermissionSettings.model_validate(permissions_yaml)

    file_environment = {
        key: value for key, value in dotenv_values(env_file).items() if value not in (None, "")
    }
    environment = {**file_environment, **os.environ}
    for env_name, field_name in _ENV_TO_FIELD.items():
        value = environment.get(env_name)
        if value not in (None, ""):
            values[field_name] = value

    settings = Settings(**values)
    if settings.context_keep_recent >= settings.context_max_messages:
        raise ValueError("context_keep_recent must be smaller than context_max_messages")
    return settings


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return raw


def _harness_values(config: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    workspace = config.get("workspace") or {}
    data = config.get("data") or {}
    skills = config.get("skills") or {}
    browser = config.get("browser") or {}
    agent = config.get("agent") or {}
    context = config.get("context") or {}

    _copy_if_present(values, "harness_workspace", workspace, "root")
    _copy_if_present(values, "harness_data_dir", data, "root")
    _copy_if_present(values, "harness_skills_dir", skills, "root")
    _copy_if_present(values, "harness_browser_profile", browser, "profile_path")
    _copy_if_present(values, "harness_browser_headless", browser, "headless")
    _copy_if_present(values, "harness_browser_channel", browser, "channel")
    _copy_if_present(values, "agent_max_steps", agent, "max_steps")
    _copy_if_present(values, "agent_max_consecutive_errors", agent, "max_consecutive_errors")
    _copy_if_present(values, "agent_max_tool_runtime_seconds", agent, "max_tool_runtime_seconds")
    _copy_if_present(values, "agent_llm_timeout_seconds", agent, "llm_timeout_seconds")
    _copy_if_present(values, "agent_llm_max_attempts", agent, "llm_max_attempts")
    _copy_if_present(values, "agent_llm_retry_base_seconds", agent, "llm_retry_base_seconds")
    _copy_if_present(values, "context_max_messages", context, "max_messages")
    _copy_if_present(values, "context_keep_recent", context, "keep_recent")
    return values


def _model_values(config: dict[str, Any]) -> dict[str, Any]:
    providers = config.get("providers") or {}
    deepseek = providers.get("deepseek") or {}
    values: dict[str, Any] = {}
    _copy_if_present(values, "deepseek_base_url", deepseek, "base_url")
    _copy_if_present(values, "deepseek_model", deepseek, "model")
    return values


def _copy_if_present(
    target: dict[str, Any],
    target_key: str,
    source: dict[str, Any],
    source_key: str,
) -> None:
    value = source.get(source_key)
    if value not in (None, ""):
        target[target_key] = value
