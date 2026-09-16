from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


DANGEROUS_COMMANDS = (
    re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\s+-[^\s]*f[^\s]*d|\bgit\s+clean\s+-[^\s]*d[^\s]*f", re.IGNORECASE),
    re.compile(r"\brm\s+-[^\s]*r[^\s]*f|\brm\s+-[^\s]*f[^\s]*r", re.IGNORECASE),
    re.compile(r"\bRemove-Item\b[^\n]*\b-Recurse\b[^\n]*\b-Force\b", re.IGNORECASE),
)

SENSITIVE_NAMES = {".env", "settings.local.json"}


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def project_root(payload: dict[str, Any]) -> Path:
    raw = os.getenv("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    return Path(raw).resolve()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    root = project_root(payload)

    if tool_name in {"Bash", "PowerShell"}:
        command = str(tool_input.get("command", ""))
        if any(pattern.search(command) for pattern in DANGEROUS_COMMANDS):
            deny("Destructive shell/git command blocked by repository hook. Ask the user explicitly before running it.")
            return 0

    if tool_name in {"Write", "Edit"}:
        raw_path = tool_input.get("file_path") or tool_input.get("path")
        if not raw_path:
            return 0

        target = Path(str(raw_path))
        if not target.is_absolute():
            target = root / target
        target = target.resolve()

        if not is_within(target, root):
            deny(f"Write outside repository root blocked: {target}")
            return 0

        if target.name in SENSITIVE_NAMES or "browser-profile" in target.parts:
            deny(f"Write to sensitive local runtime file blocked: {target.name}")
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
