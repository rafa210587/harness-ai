from pathlib import Path

import pytest

from harness.browser import PlaywrightController

pytestmark = pytest.mark.browser_runtime


async def test_chromium_launch_read_and_screenshot_without_network(tmp_path: Path) -> None:
    controller = PlaywrightController(tmp_path / "browser-profile", headless=True)
    screenshot = tmp_path / "browser-smoke.png"

    try:
        await controller.navigate(
            "data:text/html,<html><head><title>Harness Smoke</title></head>"
            "<body><main id='status'>browser-ok</main></body></html>"
        )
        page = await controller.read_page()
        captured = await controller.screenshot(screenshot)
    finally:
        await controller.close()

    assert page["title"] == "Harness Smoke"
    assert "browser-ok" in page["text"]
    assert captured == screenshot
    assert screenshot.is_file()
    assert screenshot.stat().st_size > 0
