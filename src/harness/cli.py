from __future__ import annotations

import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from harness import __version__

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


@app.command()
def doctor() -> None:
    """Run bootstrap-level environment checks."""
    workspace = Path(os.getenv("HARNESS_WORKSPACE", "./workspace"))
    data_dir = Path(os.getenv("HARNESS_DATA_DIR", "./data"))

    checks = [
        ("Python 3.12", sys.version_info[:2] == (3, 12), sys.version.split()[0]),
        ("workspace exists", workspace.exists(), str(workspace.resolve())),
        ("data directory exists", data_dir.exists(), str(data_dir.resolve())),
        ("DeepSeek API key configured", bool(os.getenv("DEEPSEEK_API_KEY")), "environment"),
        ("Blender path configured", bool(os.getenv("BLENDER_PATH")), os.getenv("BLENDER_PATH", "not set")),
        ("Unity path configured", bool(os.getenv("UNITY_PATH")), os.getenv("UNITY_PATH", "not set")),
    ]

    table = Table(title="Harness doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    for name, ok, detail in checks:
        table.add_row(name, "OK" if ok else "MISSING", str(detail))

    console.print(table)


if __name__ == "__main__":
    app()
