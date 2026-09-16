from __future__ import annotations

from harness.config import PermissionAction, PermissionSettings
from harness.hooks.base import BeforeToolEvent, HookAction, HookDecision, RuntimeHook


class PermissionHook(RuntimeHook):
    """Deterministic permission policy for tool execution."""

    def __init__(self, settings: PermissionSettings | None = None) -> None:
        self._settings = settings or PermissionSettings()

    async def before_tool(self, event: BeforeToolEvent) -> HookDecision:
        action = self._settings.action_for(event.tool_name, event.risk.value)
        if action is PermissionAction.DENY:
            return HookDecision(
                HookAction.DENY,
                f"Tool {event.tool_name} is denied by runtime policy",
            )
        if action is PermissionAction.APPROVAL:
            return HookDecision(
                HookAction.REQUIRE_APPROVAL,
                f"Tool {event.tool_name} requires approval by runtime policy",
            )
        return HookDecision(HookAction.ALLOW)
