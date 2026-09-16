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
from harness.evals import EvalRunner, load_eval_scenarios
from harness.hooks import BeforeToolEvent
from harness.llm import LLMProviderError
from harness.runtime import AgentRunResult, AgentStatus, build_agent_loop, build_tool_registry
from harness.storage import SQLiteStore

app = typer.Typer(
    name="harness",
    help="Local AI harness for tool-driven computer workflows.",
    no_args_is_help=True,
)
session_app = typer.Typer(help="Inspect persisted harness sessions.")
app.add_typer(session_app, name="session")
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


@app.command("sessions")
def sessions_command(limit: int = typer.Option(20, min=1, max=200)) -> None:
    """List persisted sessions, newest first."""
    settings = load_settings()

    async def load() -> None:
        store = SQLiteStore(settings.harness_data_dir / "harness.db")
        await store.initialize()
        sessions = await store.list_sessions(limit=limit)

        table = Table(title="Harness sessions")
        table.add_column("ID")
        table.add_column("Status")
        table.add_column("Task")
        table.add_column("Updated")
        for session in sessions:
            table.add_row(session.id, session.status, session.task, session.updated_at)
        console.print(table)

    asyncio.run(load())


@session_app.command("show")
def session_show_command(session_id: str) -> None:
    """Show one persisted session."""
    settings = load_settings()

    async def load() -> None:
        store = SQLiteStore(settings.harness_data_dir / "harness.db")
        await store.initialize()
        session = await store.get_session(session_id)
        if session is None:
            console.print(f"[red]Session not found:[/] {session_id}")
            raise typer.Exit(code=1)

        table = Table(title=f"Session {session.id}")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("status", session.status)
        table.add_row("task", session.task)
        table.add_row("reason", session.reason or "")
        table.add_row("created", session.created_at)
        table.add_row("updated", session.updated_at)
        console.print(table)

    asyncio.run(load())


@session_app.command("events")
def session_events_command(session_id: str) -> None:
    """Show structured events for one session."""
    settings = load_settings()

    async def load() -> None:
        store = SQLiteStore(settings.harness_data_dir / "harness.db")
        await store.initialize()
        session = await store.get_session(session_id)
        if session is None:
            console.print(f"[red]Session not found:[/] {session_id}")
            raise typer.Exit(code=1)

        events = await store.list_events(session_id)
        table = Table(title=f"Events {session_id}")
        table.add_column("#")
        table.add_column("Type")
        table.add_column("Payload")
        table.add_column("Created")
        for event in events:
            table.add_row(str(event.id), event.event_type, str(event.payload), event.created_at)
        console.print(table)

    asyncio.run(load())


@app.command("run")
def run_command(task: str) -> None:
    """Run one task with the configured DeepSeek provider."""
    settings = load_settings()

    async def run_agent() -> None:
        try:
            loop = build_agent_loop(settings, approval_handler=_interactive_approval)
            result = await loop.run(task)
        except LLMProviderError as exc:
            console.print(f"[red]Provider error:[/] {exc}")
            raise typer.Exit(code=1) from exc

        _render_run_result(result)

    asyncio.run(run_agent())


@app.command("resume")
def resume_command(session_id: str) -> None:
    """Resume a blocked persisted session from its pending approval."""
    settings = load_settings()

    async def resume_agent() -> None:
        try:
            loop = build_agent_loop(settings, approval_handler=_interactive_approval)
            result = await loop.resume(session_id)
        except (ValueError, RuntimeError, LLMProviderError) as exc:
            console.print(f"[red]Resume failed:[/] {exc}")
            raise typer.Exit(code=1) from exc

        _render_run_result(result)

    asyncio.run(resume_agent())


@app.command("eval")
def eval_command(
    scenarios_file: Path,
    json_out: Path | None = typer.Option(None, "--json-out"),
) -> None:
    """Run a YAML eval suite with the configured harness."""
    settings = load_settings()

    async def run_evals() -> None:
        try:
            scenarios = load_eval_scenarios(scenarios_file)
            store = SQLiteStore(settings.harness_data_dir / "harness.db")
            await store.initialize()
            runner = EvalRunner(
                lambda _scenario: build_agent_loop(settings),
                store=store,
            )
            report = await runner.run(scenarios)
        except (ValueError, FileNotFoundError, LLMProviderError) as exc:
            console.print(f"[red]Eval failed:[/] {exc}")
            raise typer.Exit(code=1) from exc

        table = Table(title="Harness eval")
        table.add_column("Scenario")
        table.add_column("Result")
        table.add_column("Status")
        table.add_column("Steps")
        table.add_column("Tool errors")
        table.add_column("Verification failures")
        for case in report.cases:
            table.add_row(
                case.name,
                "PASS" if case.passed else "FAIL",
                case.status.value,
                str(case.steps),
                str(case.tool_errors),
                str(case.verification_failures),
            )
        console.print(table)
        console.print(
            f"Passed {report.passed}/{report.total} "
            f"({report.success_rate:.1%}); average steps: {report.average_steps:.2f}"
        )

        if json_out is not None:
            json_out.parent.mkdir(parents=True, exist_ok=True)
            json_out.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        if report.passed != report.total:
            raise typer.Exit(code=1)

    asyncio.run(run_evals())


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


async def _interactive_approval(event: BeforeToolEvent) -> bool:
    console.print(f"[yellow]Approval required:[/] {event.tool_name}")
    console.print(event.arguments)
    return typer.confirm("Allow this tool call?", default=False)


def _render_run_result(result: AgentRunResult) -> None:
    if result.status is AgentStatus.COMPLETED:
        console.print(result.content or "")
        return

    console.print(f"[red]{result.status.value}:[/] {result.reason or 'unknown reason'}")
    raise typer.Exit(code=1)


def _configured_executable_exists(path: Path | None) -> bool:
    return path is not None and path.is_file()


if __name__ == "__main__":
    app()
