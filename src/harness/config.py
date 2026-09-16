from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration loaded from environment variables and `.env`."""

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


def load_settings() -> Settings:
    return Settings()
