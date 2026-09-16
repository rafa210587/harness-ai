from harness.hooks import BeforeToolEvent, HookAction, HookDispatcher, PermissionHook
from harness.tools import ToolRisk


async def test_permission_hook_allows_read() -> None:
    dispatcher = HookDispatcher([PermissionHook()])

    decision = await dispatcher.before_tool(
        BeforeToolEvent(
            session_id="s1",
            tool_name="filesystem_read",
            arguments={"path": "x.txt"},
            risk=ToolRisk.READ,
        )
    )

    assert decision.action is HookAction.ALLOW


async def test_permission_hook_requires_approval_for_dangerous_tool() -> None:
    dispatcher = HookDispatcher([PermissionHook()])

    decision = await dispatcher.before_tool(
        BeforeToolEvent(
            session_id="s1",
            tool_name="shell_run",
            arguments={"command": "echo hi"},
            risk=ToolRisk.DANGEROUS,
        )
    )

    assert decision.action is HookAction.REQUIRE_APPROVAL
