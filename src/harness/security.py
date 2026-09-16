from __future__ import annotations

from typing import Any

_REDACTED = "[REDACTED]"


class SecretRedactor:
    """Redact configured secret values from runtime data before it reaches the agent or storage."""

    def __init__(self, secrets: list[str] | tuple[str, ...]) -> None:
        self._secrets = tuple(
            secret for secret in secrets if secret and len(secret) >= 4
        )

    def redact_text(self, value: str) -> str:
        redacted = value
        for secret in self._secrets:
            redacted = redacted.replace(secret, _REDACTED)
        return redacted

    def redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.redact(item) for item in value)
        if isinstance(value, dict):
            return {key: self.redact(item) for key, item in value.items()}
        return value
