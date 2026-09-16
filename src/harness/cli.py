from __future__ import annotations

import asyncio
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from harness import __version__
from harness.config import load_settings
from harness.hooks import BeforeToolEvent
from harness.llm import LLMProviderError
from harness.runtime import AgentStatus, build_agent_loop, build_tool_registry

app = typer.Typer(
    name="harness",
    help="Local AI harness for tool-driven computer workflows.",
    no_args_is_help=True,
)
console = Console()


@app.command("version")
def version_command() -> None:
    """Print the harness version."""
    console.print(__version__)


@app.command("tools")
def tools_command() -> None:
    """List tools exposed by the default runtime."""
    settings = load_settings()
    registry = build_tool_registry(settings)

    table = Table(title="Harness tools")
    table.add_column("Name")
    table.add_column("Risk")
    table.add_column("Description")
    for tool in registry.tools():
        table.add_row(tool.name, tool.risk.value, tool.description)
    console.print(table)


@app.command("run")
def run_command(task: str) -> None:
    """Run one task with the configured DeepSeek provider."""
    settings = load_settings()

    async def approval_handler(event: BeforeToolEvent) -> bool:
        console.print(f"[yellow]Approval required:[/] {event.tool_name}")
        console.print(event.arguments)
        return typer.confirm("Allow this tool call?", default=False)

    async def run_agent() -> None:
        try:
            loop = build_agent_loop(settings, approval_handler=approval_handler)
            result = await loop.run(task)
        except LLMProviderError as exc:
            console.print(f"[red]Provider error:[/] {exc}")
            raise typer.Exit(code=1) from exc

        if result.status is AgentStatus.COMPLETED:
            console.print(result.content or "")
            return

        console.print(f"[red]{result.status.value}:[/] {result.reason or 'unknown reason'}")
        raise typer.Exit(code=1)

    asyncio.run(run_agent())


@app.command()
def doctor() -> None:
    """Run local environment checks without making a network request."""
    settings = load_settings()
    workspace = settings.harness_workspace
    data_dir = settings.harness_data_dir

    checks = [
        ("Python 3.12", sys.version_info[:2] == (3, 12), sys.version.split()[0]),
        ("Git available", shutil.which("git") is not None, shutil.which("git") or "not found"),
        ("uv available", shutil.which("uv") is not None, shutil.which("uv") or "not found"),
        (
            "Playwright package",
            importlib.util.find_spec("playwright") is not None,
            "installed" if importlib.util.find_spec("playwright") else "not installed",
        ),
        ("workspace exists", workspace.exists(), str(workspace.resolve())),
        (
            "workspace writable",
            workspace.exists() and os.access(workspace, os.W_OK),
            str(workspace.resolve()),
        ),
        ("data directory exists", data_dir.exists(), str(data_dir.resolve())),
        (
            "data directory writable",
            data_dir.exists() and os.access(data_dir, os.W_OK),
            str(data_dir.resolve()),
        ),
        (
            "DeepSeek API key",
            settings.deepseek_api_key is not None,
            "configured" if settings.deepseek_api_key else "not set",
        ),
        (
            "Blender executable",
            _configured_executable_exists(settings.blender_path),
            str(settings.blender_path or "not set"),
        ),
        (
            "Unity executable",
            _configured_executable_exists(settings.unity_path),
            str(settings.unity_path or "not set"),
        ),
    ]

    table = Table(title="Harness doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    for name, ok, detail in checks:
        table.add_row(name, "OK" if ok else "MISSING", str(detail))

    console.print(table)


def _configured_executable_exists(path: Path | None) -> bool:
    return path is not None and path.is_file()


if __name__ == "__main__":
    app()
