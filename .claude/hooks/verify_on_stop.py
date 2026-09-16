from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if payload.get("stop_hook_active"):
        return 0

    root = Path(os.getenv("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).resolve()

    status = run(["git", "status", "--porcelain"], root)
    if status.returncode != 0 or not status.stdout.strip():
        return 0

    checks = [
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "ruff", "check", "."],
    ]

    failures: list[str] = []
    for command in checks:
        result = run(command, root)
        if result.returncode != 0:
            output = (result.stdout + "\n" + result.stderr).strip()
            failures.append(f"$ {' '.join(command)}\n{output}")

    if failures:
        reason = (
            "Repository verification failed. Fix these checks before finishing:\n\n"
            + "\n\n".join(failures)
        )
        print(json.dumps({"decision": "block", "reason": reason[:8000]}))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
