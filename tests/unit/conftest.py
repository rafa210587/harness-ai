from collections.abc import Iterator

import pytest


_HARNESS_ENVIRONMENT_KEYS = (
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "HARNESS_DATA_DIR",
    "HARNESS_WORKSPACE",
    "HARNESS_SKILLS_DIR",
    "HARNESS_LOG_LEVEL",
    "HARNESS_BROWSER_PROFILE",
    "HARNESS_BROWSER_HEADLESS",
    "BLENDER_PATH",
    "UNITY_PATH",
    "AGENT_MAX_STEPS",
    "AGENT_MAX_CONSECUTIVE_ERRORS",
    "AGENT_MAX_TOOL_RUNTIME_SECONDS",
    "AGENT_LLM_TIMEOUT_SECONDS",
    "AGENT_LLM_MAX_ATTEMPTS",
    "AGENT_LLM_RETRY_BASE_SECONDS",
    "CONTEXT_MAX_MESSAGES",
    "CONTEXT_KEEP_RECENT",
)


@pytest.fixture(autouse=True)
def isolate_unit_tests_from_harness_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep unit tests deterministic when a developer has a real local .env loaded."""
    for name in _HARNESS_ENVIRONMENT_KEYS:
        monkeypatch.delenv(name, raising=False)
    yield
