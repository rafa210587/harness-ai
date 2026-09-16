from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import BaseModel


class ProcessResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


async def run_process(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 300,
) -> ProcessResult:
    """Run an executable without invoking a shell."""
    process = await asyncio.create_subprocess_exec(
        *arguments,
        cwd=str(cwd) if cwd is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        return ProcessResult(
            exit_code=process.returncode or -1,
            stdout="",
            stderr=f"Process timed out after {timeout_seconds}s",
            timed_out=True,
        )

    return ProcessResult(
        exit_code=process.returncode or 0,
        stdout=stdout_bytes.decode(errors="replace"),
        stderr=stderr_bytes.decode(errors="replace"),
    )
