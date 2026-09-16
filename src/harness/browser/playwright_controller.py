from __future__ import annotations

from pathlib import Path

from playwright.async_api import BrowserContext, Page, Playwright, Route, async_playwright

from harness.browser.security import ensure_public_http_url_resolved, is_blocked_http_url


class PlaywrightController:
    """Own one persistent Chromium context and expose semantic browser operations."""

    def __init__(self, profile_dir: Path, *, headless: bool = False) -> None:
        self._profile_dir = profile_dir
        self._headless = headless
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        if self._page is not None:
            return
        self._profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._profile_dir),
            headless=self._headless,
        )
        await self._context.route("**/*", self._guard_request)
        self._page = (
            self._context.pages[0] if self._context.pages else await self._context.new_page()
        )

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
        if self._playwright is not None:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None

    async def navigate(self, url: str) -> dict[str, str]:
        page = await self._require_page()
        await page.goto(url, wait_until="domcontentloaded")
        return {"url": page.url, "title": await page.title()}

    async def read_page(self) -> dict[str, str]:
        page = await self._require_page()
        return {
            "url": page.url,
            "title": await page.title(),
            "text": await page.locator("body").inner_text(),
        }

    async def click(self, selector: str) -> dict[str, str]:
        page = await self._require_page()
        await page.locator(selector).click()
        return {"url": page.url}

    async def fill(self, selector: str, text: str) -> dict[str, str]:
        page = await self._require_page()
        await page.locator(selector).fill(text)
        return {"selector": selector}

    async def wait_for(self, selector: str, timeout_ms: int = 10_000) -> dict[str, str]:
        page = await self._require_page()
        await page.locator(selector).wait_for(timeout=timeout_ms)
        return {"selector": selector}

    async def screenshot(self, path: Path, *, full_page: bool = True) -> Path:
        page = await self._require_page()
        path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(path), full_page=full_page)
        return path

    async def _require_page(self) -> Page:
        await self.start()
        if self._page is None:
            raise RuntimeError("Browser page was not created")
        return self._page

    async def _guard_request(self, route: Route) -> None:
        url = route.request.url
        if is_blocked_http_url(url):
            await route.abort("blockedbyclient")
            return

        if url.lower().startswith(("http://", "https://")):
            try:
                await ensure_public_http_url_resolved(url)
            except (OSError, ValueError):
                await route.abort("blockedbyclient")
                return

        await route.continue_()
