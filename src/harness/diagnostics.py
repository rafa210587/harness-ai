from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from pydantic import BaseModel

from harness.browser import PlaywrightController
from harness.config import Settings
from harness.llm import DeepSeekProvider, LLMProvider, Message
from harness.process import ProcessResult, run_process


class DiagnosticResult(BaseModel):
    name: str
    ok: bool
    detail: str


class BrowserProbe(Protocol):
    async def start(self) -> None: ...

    async def close(self) -> None: ...


ProviderFactory = Callable[[Settings], LLMProvider]
BrowserFactory = Callable[[Path], BrowserProbe]
ProcessRunner = Callable[..., Awaitable[ProcessResult]]


async def run_online_checks(
    settings: Settings,
    *,
    provider_factory: ProviderFactory = DeepSeekProvider,
    browser_factory: BrowserFactory | None = None,
    process_runner: ProcessRunner = run_process,
) -> list[DiagnosticResult]:
    """Run checks that contact providers or launch external applications."""
    effective_browser_factory = browser_factory or _default_browser_factory
    results = [await _check_deepseek(settings, provider_factory)]
    results.append(await _check_browser(effective_browser_factory))
    results.append(
        await _check_executable(
            "Blender launch",
            settings.blender_path,
            ["--version"],
            process_runner,
        )
    )
    results.append(
        await _check_executable(
            "Unity launch",
            settings.unity_path,
            ["-version"],
            process_runner,
        )
    )
    return results


async def _check_deepseek(
    settings: Settings,
    provider_factory: ProviderFactory,
) -> DiagnosticResult:
    if settings.deepseek_api_key is None:
        return DiagnosticResult(name="DeepSeek API", ok=False, detail="API key not configured")

    try:
        provider = provider_factory(settings)
        response = await provider.complete([Message(role="user", content="Reply with exactly OK")])
    except Exception as exc:  # diagnostics boundary
        return DiagnosticResult(
            name="DeepSeek API",
            ok=False,
            detail=f"{type(exc).__name__}: {exc}",
        )

    content = (response.content or "").strip()
    return DiagnosticResult(
        name="DeepSeek API",
        ok=bool(content),
        detail=content or "empty response",
    )


async def _check_browser(browser_factory: BrowserFactory) -> DiagnosticResult:
    browser: BrowserProbe | None = None
    try:
        with TemporaryDirectory(prefix="harness-doctor-") as directory:
            browser = browser_factory(Path(directory))
            await browser.start()
            await browser.close()
            browser = None
    except Exception as exc:  # diagnostics boundary
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass
        return DiagnosticResult(
            name="Chromium launch",
            ok=False,
            detail=f"{type(exc).__name__}: {exc}",
        )

    return DiagnosticResult(name="Chromium launch", ok=True, detail="launched successfully")


async def _check_executable(
    name: str,
    executable: Path | None,
    arguments: list[str],
    process_runner: ProcessRunner,
) -> DiagnosticResult:
    if executable is None:
        return DiagnosticResult(name=name, ok=False, detail="not configured")
    if not executable.is_file():
        return DiagnosticResult(name=name, ok=False, detail=f"not found: {executable}")

    try:
        result = await process_runner(
            [str(executable), *arguments],
            timeout_seconds=60,
        )
    except Exception as exc:  # diagnostics boundary
        return DiagnosticResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}")

    output = (result.stdout or result.stderr).strip()
    detail = output.splitlines()[0] if output else f"exit code {result.exit_code}"
    return DiagnosticResult(
        name=name,
        ok=not result.timed_out and result.exit_code == 0,
        detail=detail,
    )


def _default_browser_factory(profile_dir: Path) -> BrowserProbe:
    return PlaywrightController(profile_dir, headless=True)
