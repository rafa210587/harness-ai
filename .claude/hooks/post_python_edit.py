from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def emit_context(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message[:4000],
                }
            }
        )
    )


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    tool_input = payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path") or tool_input.get("path")
    if not raw_path:
        return 0

    path = Path(str(raw_path))
    if path.suffix.lower() != ".py" or not path.exists():
        return 0

    root = Path(os.getenv("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).resolve()

    format_result = subprocess.run(
        ["uv", "run", "ruff", "format", str(path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    check_result = subprocess.run(
        ["uv", "run", "ruff", "check", str(path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    messages: list[str] = []
    if format_result.returncode != 0:
        messages.append("Ruff formatter failed:\n" + (format_result.stderr or format_result.stdout))
    if check_result.returncode != 0:
        messages.append("Ruff lint failed:\n" + (check_result.stdout or check_result.stderr))

    if messages:
        emit_context("\n\n".join(messages))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
