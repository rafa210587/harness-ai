from __future__ import annotations

from harness.blender import BlenderController
from harness.browser import PlaywrightController
from harness.config import Settings
from harness.hooks import HookDispatcher, PermissionHook
from harness.llm import DeepSeekProvider
from harness.runtime.agent_loop import AgentLoop, ApprovalHandler
from harness.storage import SQLiteStore
from harness.tools import (
    BlenderExecutePythonTool,
    BlenderRenderTool,
    BrowserClickTool,
    BrowserFillTool,
    BrowserNavigateTool,
    BrowserReadPageTool,
    BrowserScreenshotTool,
    BrowserWaitTool,
    FilesystemCopyTool,
    FilesystemListTool,
    FilesystemMkdirTool,
    FilesystemMoveTool,
    FilesystemPatchTool,
    FilesystemReadTool,
    FilesystemSearchTool,
    FilesystemWriteTool,
    ShellRunTool,
    ToolRegistry,
    UnityExecuteEditorScriptTool,
    UnityProjectInfoTool,
    WorkspacePaths,
)
from harness.unity import UnityController


def build_tool_registry(settings: Settings) -> ToolRegistry:
    settings.harness_workspace.mkdir(parents=True, exist_ok=True)
    paths = WorkspacePaths(settings.harness_workspace)
    browser = PlaywrightController(
        settings.harness_browser_profile,
        headless=settings.harness_browser_headless,
    )
    blender = BlenderController(settings.blender_path, paths)
    unity = UnityController(settings.unity_path, paths)

    registry = ToolRegistry()
    registry.register(FilesystemReadTool(paths))
    registry.register(FilesystemListTool(paths))
    registry.register(FilesystemWriteTool(paths))
    registry.register(FilesystemPatchTool(paths))
    registry.register(FilesystemSearchTool(paths))
    registry.register(FilesystemMkdirTool(paths))
    registry.register(FilesystemCopyTool(paths))
    registry.register(FilesystemMoveTool(paths))
    registry.register(ShellRunTool(paths))
    registry.register(BrowserNavigateTool(browser))
    registry.register(BrowserReadPageTool(browser))
    registry.register(BrowserClickTool(browser))
    registry.register(BrowserFillTool(browser))
    registry.register(BrowserWaitTool(browser))
    registry.register(BrowserScreenshotTool(browser, paths))
    registry.register(BlenderExecutePythonTool(blender, paths))
    registry.register(BlenderRenderTool(blender, paths))
    registry.register(UnityProjectInfoTool(paths))
    registry.register(UnityExecuteEditorScriptTool(unity, paths))
    return registry


def build_agent_loop(
    settings: Settings,
    *,
    approval_handler: ApprovalHandler | None = None,
) -> AgentLoop:
    settings.harness_data_dir.mkdir(parents=True, exist_ok=True)
    registry = build_tool_registry(settings)
    hooks = HookDispatcher([PermissionHook(settings.permissions)])
    provider = DeepSeekProvider(settings)
    store = SQLiteStore(settings.harness_data_dir / "harness.db")
    return AgentLoop(
        provider,
        registry,
        hooks,
        store=store,
        max_steps=settings.agent_max_steps,
        max_consecutive_errors=settings.agent_max_consecutive_errors,
        approval_handler=approval_handler,
    )
