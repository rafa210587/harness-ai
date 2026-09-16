from pathlib import Path

from harness.tools import (
    BrowserClickTool,
    BrowserFillTool,
    BrowserNavigateTool,
    BrowserReadPageTool,
    BrowserScreenshotTool,
    BrowserWaitTool,
    ToolRegistry,
    WorkspacePaths,
)


class FakeBrowserController:
    def __init__(self) -> None:
        self.actions: list[tuple[str, object]] = []

    async def navigate(self, url: str) -> dict[str, str]:
        self.actions.append(("navigate", url))
        return {"url": url, "title": "Test"}

    async def read_page(self) -> dict[str, str]:
        return {"url": "https://example.com", "title": "Test", "text": "Hello"}

    async def click(self, selector: str) -> dict[str, str]:
        self.actions.append(("click", selector))
        return {"url": "https://example.com"}

    async def fill(self, selector: str, text: str) -> dict[str, str]:
        self.actions.append(("fill", (selector, text)))
        return {"selector": selector}

    async def wait_for(self, selector: str, timeout_ms: int = 10_000) -> dict[str, str]:
        self.actions.append(("wait", (selector, timeout_ms)))
        return {"selector": selector}

    async def screenshot(self, path: Path, *, full_page: bool = True) -> Path:
        self.actions.append(("screenshot", (path, full_page)))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-png")
        return path


async def test_browser_tools_execute_through_controller(tmp_path: Path) -> None:
    controller = FakeBrowserController()
    paths = WorkspacePaths(tmp_path)
    registry = ToolRegistry()
    registry.register(BrowserNavigateTool(controller))
    registry.register(BrowserReadPageTool(controller))
    registry.register(BrowserFillTool(controller))
    registry.register(BrowserWaitTool(controller))
    registry.register(BrowserScreenshotTool(controller, paths))

    navigated = await registry.execute("browser_navigate", {"url": "https://example.com"})
    read = await registry.execute("browser_read_page", {})
    filled = await registry.execute("browser_fill", {"selector": "#name", "text": "Rafa"})
    waited = await registry.execute("browser_wait", {"selector": "#result", "timeout_ms": 500})
    captured = await registry.execute(
        "browser_screenshot", {"path": "artifacts/page.png", "full_page": True}
    )

    assert navigated.success is True
    assert read.output["text"] == "Hello"
    assert filled.success is True
    assert waited.success is True
    assert captured.artifacts == ["artifacts/page.png"]
    assert (tmp_path / "artifacts/page.png").exists()


def test_browser_click_is_dangerous() -> None:
    controller = FakeBrowserController()
    tool = BrowserClickTool(controller)

    assert tool.risk.value == "dangerous"
