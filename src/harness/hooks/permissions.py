from __future__ import annotations

from harness.hooks.base import BeforeToolEvent, HookAction, HookDecision, RuntimeHook
from harness.tools.base import ToolRisk


class PermissionHook(RuntimeHook):
    """Default conservative risk policy for tool execution."""

    async def before_tool(self, event: BeforeToolEvent) -> HookDecision:
        if event.risk is ToolRisk.DANGEROUS:
            return HookDecision(
                HookAction.REQUIRE_APPROVAL,
                f"Tool {event.tool_name} is classified as dangerous",
            )
        return HookDecision(HookAction.ALLOW)
