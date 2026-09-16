from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Protocol

from pydantic import BaseModel, Field, HttpUrl

from harness.tools.base import EmptyArguments, Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths


class BrowserController(Protocol):
    async def navigate(self, url: str) -> dict[str, str]: ...

    async def read_page(self) -> dict[str, str]: ...

    async def click(self, selector: str) -> dict[str, str]: ...

    async def fill(self, selector: str, text: str) -> dict[str, str]: ...

    async def wait_for(self, selector: str, timeout_ms: int = 10_000) -> dict[str, str]: ...

    async def screenshot(self, path: Path, *, full_page: bool = True) -> Path: ...


class NavigateArguments(BaseModel):
    url: HttpUrl


class SelectorArguments(BaseModel):
    selector: str = Field(min_length=1)


class FillArguments(SelectorArguments):
    text: str


class WaitArguments(SelectorArguments):
    timeout_ms: int = Field(default=10_000, ge=1, le=60_000)


class ScreenshotArguments(BaseModel):
    path: str = "artifacts/browser.png"
    full_page: bool = True


class BrowserNavigateTool(Tool):
    name: ClassVar[str] = "browser_navigate"
    description: ClassVar[str] = "Navigate Chromium to an HTTP or HTTPS URL."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = NavigateArguments

    def __init__(self, controller: BrowserController) -> None:
        self._controller = controller

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = NavigateArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(await self._controller.navigate(str(args.url)))


class BrowserReadPageTool(Tool):
    name: ClassVar[str] = "browser_read_page"
    description: ClassVar[str] = "Read the current page title, URL, and visible body text."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = EmptyArguments

    def __init__(self, controller: BrowserController) -> None:
        self._controller = controller

    async def execute(self, arguments: BaseModel) -> ToolResult:
        return ToolResult.ok(await self._controller.read_page())


class BrowserClickTool(Tool):
    name: ClassVar[str] = "browser_click"
    description: ClassVar[str] = "Click a DOM element selected by a Playwright locator string."
    risk: ClassVar[ToolRisk] = ToolRisk.DANGEROUS
    arguments_model: ClassVar[type[BaseModel]] = SelectorArguments

    def __init__(self, controller: BrowserController) -> None:
        self._controller = controller

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = SelectorArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(await self._controller.click(args.selector))


class BrowserFillTool(Tool):
    name: ClassVar[str] = "browser_fill"
    description: ClassVar[str] = "Fill a DOM input without submitting the form."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = FillArguments

    def __init__(self, controller: BrowserController) -> None:
        self._controller = controller

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = FillArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(await self._controller.fill(args.selector, args.text))


class BrowserWaitTool(Tool):
    name: ClassVar[str] = "browser_wait"
    description: ClassVar[str] = "Wait until a DOM selector becomes available."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = WaitArguments

    def __init__(self, controller: BrowserController) -> None:
        self._controller = controller

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = WaitArguments.model_validate(arguments.model_dump())
        return ToolResult.ok(await self._controller.wait_for(args.selector, args.timeout_ms))


class BrowserScreenshotTool(Tool):
    name: ClassVar[str] = "browser_screenshot"
    description: ClassVar[str] = "Capture the current browser page into the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = ScreenshotArguments

    def __init__(self, controller: BrowserController, paths: WorkspacePaths) -> None:
        self._controller = controller
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = ScreenshotArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        screenshot = await self._controller.screenshot(path, full_page=args.full_page)
        relative = self._paths.relative(screenshot)
        return ToolResult.ok({"path": relative}, artifacts=[relative])
