from __future__ import annotations

import asyncio
from typing import ClassVar

from pydantic import BaseModel, Field

from harness.tools.base import Tool, ToolResult, ToolRisk
from harness.tools.filesystem import WorkspacePaths


class ShellArguments(BaseModel):
    command: str = Field(min_length=1)
    cwd: str = "."
    timeout_seconds: int = Field(default=60, ge=1, le=300)


class ShellRunTool(Tool):
    name: ClassVar[str] = "shell_run"
    description: ClassVar[str] = "Run a shell command inside the configured workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.DANGEROUS
    arguments_model: ClassVar[type[BaseModel]] = ShellArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = ShellArguments.model_validate(arguments.model_dump())
        cwd = self._paths.resolve(args.cwd)
        if not cwd.is_dir():
            return ToolResult.fail(f"Working directory not found: {args.cwd}")

        process = await asyncio.create_subprocess_shell(
            args.command,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=args.timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return ToolResult.fail(
                f"Command timed out after {args.timeout_seconds}s",
                retryable=False,
            )

        return ToolResult.ok(
            {
                "exit_code": process.returncode,
                "stdout": stdout_bytes.decode(errors="replace"),
                "stderr": stderr_bytes.decode(errors="replace"),
            }
        )
