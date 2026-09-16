from __future__ import annotations

from harness.hooks.base import BeforeToolEvent, HookAction, HookDecision, RuntimeHook


class HookDispatcher:
    def __init__(self, hooks: list[RuntimeHook] | None = None) -> None:
        self._hooks = hooks or []

    def register(self, hook: RuntimeHook) -> None:
        self._hooks.append(hook)

    async def before_tool(self, event: BeforeToolEvent) -> HookDecision:
        decisions: list[HookDecision] = []
        for hook in self._hooks:
            decision = await hook.before_tool(event)
            if decision is not None:
                decisions.append(decision)

        denied = next((item for item in decisions if item.action is HookAction.DENY), None)
        if denied is not None:
            return denied

        approval = next(
            (item for item in decisions if item.action is HookAction.REQUIRE_APPROVAL),
            None,
        )
        if approval is not None:
            return approval

        return HookDecision(HookAction.ALLOW)
