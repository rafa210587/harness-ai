from __future__ import annotations

from harness.config import Settings
from harness.hooks import HookDispatcher, PermissionHook
from harness.llm import DeepSeekProvider
from harness.runtime.agent_loop import AgentLoop, ApprovalHandler
from harness.tools import (
    FilesystemListTool,
    FilesystemReadTool,
    FilesystemSearchTool,
    FilesystemWriteTool,
    ShellRunTool,
    ToolRegistry,
    WorkspacePaths,
)


def build_tool_registry(settings: Settings) -> ToolRegistry:
    settings.harness_workspace.mkdir(parents=True, exist_ok=True)
    paths = WorkspacePaths(settings.harness_workspace)
    registry = ToolRegistry()
    registry.register(FilesystemReadTool(paths))
    registry.register(FilesystemListTool(paths))
    registry.register(FilesystemWriteTool(paths))
    registry.register(FilesystemSearchTool(paths))
    registry.register(ShellRunTool(paths))
    return registry


def build_agent_loop(
    settings: Settings,
    *,
    approval_handler: ApprovalHandler | None = None,
) -> AgentLoop:
    settings.harness_data_dir.mkdir(parents=True, exist_ok=True)
    registry = build_tool_registry(settings)
    hooks = HookDispatcher([PermissionHook()])
    provider = DeepSeekProvider(settings)
    return AgentLoop(
        provider,
        registry,
        hooks,
        max_steps=settings.agent_max_steps,
        max_consecutive_errors=settings.agent_max_consecutive_errors,
        approval_handler=approval_handler,
    )
