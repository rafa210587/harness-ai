from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PermissionAction(StrEnum):
    AUTO = "auto"
    APPROVAL = "approval"
    DENY = "deny"


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
    harness_log_level: str = "INFO"

    harness_browser_profile: Path = Path("./data/browser-profile")
    harness_browser_headless: bool = False

    blender_path: Path | None = None
    unity_path: Path | None = None

    agent_max_steps: int = 50
    agent_max_consecutive_errors: int = 5
    agent_max_tool_runtime_seconds: int = 300

    permissions: PermissionSettings = Field(default_factory=PermissionSettings)


_ENV_TO_FIELD = {
    "DEEPSEEK_API_KEY": "deepseek_api_key",
    "DEEPSEEK_BASE_URL": "deepseek_base_url",
    "DEEPSEEK_MODEL": "deepseek_model",
    "HARNESS_DATA_DIR": "harness_data_dir",
    "HARNESS_WORKSPACE": "harness_workspace",
    "HARNESS_LOG_LEVEL": "harness_log_level",
    "HARNESS_BROWSER_PROFILE": "harness_browser_profile",
    "HARNESS_BROWSER_HEADLESS": "harness_browser_headless",
    "BLENDER_PATH": "blender_path",
    "UNITY_PATH": "unity_path",
    "AGENT_MAX_STEPS": "agent_max_steps",
    "AGENT_MAX_CONSECUTIVE_ERRORS": "agent_max_consecutive_errors",
    "AGENT_MAX_TOOL_RUNTIME_SECONDS": "agent_max_tool_runtime_seconds",
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

    return Settings(**values)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return raw


def _harness_values(config: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    workspace = config.get("workspace") or {}
    data = config.get("data") or {}
    browser = config.get("browser") or {}
    agent = config.get("agent") or {}

    _copy_if_present(values, "harness_workspace", workspace, "root")
    _copy_if_present(values, "harness_data_dir", data, "root")
    _copy_if_present(values, "harness_browser_profile", browser, "profile_path")
    _copy_if_present(values, "harness_browser_headless", browser, "headless")
    _copy_if_present(values, "agent_max_steps", agent, "max_steps")
    _copy_if_present(values, "agent_max_consecutive_errors", agent, "max_consecutive_errors")
    _copy_if_present(values, "agent_max_tool_runtime_seconds", agent, "max_tool_runtime_seconds")
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
