from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from harness.tools.base import ToolRisk


class HookAction(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class HookDecision:
    action: HookAction
    reason: str | None = None


@dataclass(frozen=True)
class BeforeToolEvent:
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    risk: ToolRisk


class RuntimeHook:
    async def before_tool(self, event: BeforeToolEvent) -> HookDecision | None:
        return None
