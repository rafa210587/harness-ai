from __future__ import annotations

from harness.blender import BlenderController
from harness.browser import PlaywrightController
from harness.config import Settings
from harness.hooks import HookDispatcher, PermissionHook
from harness.images import ImageProvider
from harness.llm import DeepSeekProvider
from harness.runtime.agent_loop import AgentLoop, ApprovalHandler
from harness.runtime.context import LLMContextCompactor
from harness.runtime.verification import LatestImageVisionVerifier, RunVerifier
from harness.skills import RuntimeSkillLoader
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
    ImageGenerateTool,
    ShellRunTool,
    SkillListTool,
    SkillLoadTool,
    ToolRegistry,
    UnityExecuteEditorScriptTool,
    UnityProjectInfoTool,
    VisionInspectTool,
    WorkspacePaths,
)
from harness.unity import UnityController
from harness.vision import VisionProvider


def build_tool_registry(
    settings: Settings,
    *,
    image_provider: ImageProvider | None = None,
    vision_provider: VisionProvider | None = None,
) -> ToolRegistry:
    settings.harness_workspace.mkdir(parents=True, exist_ok=True)
    paths = WorkspacePaths(settings.harness_workspace)
    browser = PlaywrightController(
        settings.harness_browser_profile,
        headless=settings.harness_browser_headless,
    )
    blender = BlenderController(settings.blender_path, paths)
    unity = UnityController(settings.unity_path, paths)
    skills = RuntimeSkillLoader(settings.harness_skills_dir)

    registry = ToolRegistry(default_timeout_seconds=settings.agent_max_tool_runtime_seconds)
    registry.register(FilesystemReadTool(paths))
    registry.register(FilesystemListTool(paths))
    registry.register(FilesystemWriteTool(paths))
    registry.register(FilesystemPatchTool(paths))
    registry.register(FilesystemSearchTool(paths))
    registry.register(FilesystemMkdirTool(paths))
    registry.register(FilesystemCopyTool(paths))
    registry.register(FilesystemMoveTool(paths))
    registry.register(ShellRunTool(paths))
    registry.register(SkillListTool(skills))
    registry.register(SkillLoadTool(skills))
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
    if image_provider is not None:
        registry.register(ImageGenerateTool(image_provider, paths))
    if vision_provider is not None:
        registry.register(VisionInspectTool(vision_provider, paths))
    return registry


def build_agent_loop(
    settings: Settings,
    *,
    approval_handler: ApprovalHandler | None = None,
    image_provider: ImageProvider | None = None,
    vision_provider: VisionProvider | None = None,
    verifier: RunVerifier | None = None,
) -> AgentLoop:
    settings.harness_data_dir.mkdir(parents=True, exist_ok=True)
    registry = build_tool_registry(
        settings,
        image_provider=image_provider,
        vision_provider=vision_provider,
    )
    hooks = HookDispatcher([PermissionHook(settings.permissions)])
    provider = DeepSeekProvider(settings)
    context_compactor = LLMContextCompactor(
        provider,
        keep_recent=settings.context_keep_recent,
    )
    store = SQLiteStore(settings.harness_data_dir / "harness.db")
    effective_verifier = verifier
    if effective_verifier is None and vision_provider is not None:
        effective_verifier = LatestImageVisionVerifier(
            vision_provider,
            settings.harness_workspace,
        )
    return AgentLoop(
        provider,
        registry,
        hooks,
        store=store,
        verifier=effective_verifier,
        context_compactor=context_compactor,
        max_context_messages=settings.context_max_messages,
        max_steps=settings.agent_max_steps,
        max_consecutive_errors=settings.agent_max_consecutive_errors,
        approval_handler=approval_handler,
    )
