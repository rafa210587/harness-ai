from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from harness.tools.base import Tool, ToolResult, ToolRisk


class WorkspacePaths:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, raw_path: str) -> Path:
        candidate = (self.root / raw_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes workspace: {raw_path}") from exc
        return candidate

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()


class PathArguments(BaseModel):
    path: str


class ListArguments(BaseModel):
    path: str = "."
    recursive: bool = False


class WriteArguments(BaseModel):
    path: str
    content: str
    overwrite: bool = True


class SearchArguments(BaseModel):
    query: str
    path: str = "."
    glob: str = "*"
    max_results: int = Field(default=50, ge=1, le=500)


class FilesystemReadTool(Tool):
    name: ClassVar[str] = "filesystem_read"
    description: ClassVar[str] = "Read a UTF-8 text file inside the configured workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = PathArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = PathArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        if not path.is_file():
            return ToolResult.fail(f"File not found: {args.path}")
        return ToolResult.ok(
            {"path": self._paths.relative(path), "content": path.read_text(encoding="utf-8")}
        )


class FilesystemListTool(Tool):
    name: ClassVar[str] = "filesystem_list"
    description: ClassVar[str] = "List files and directories inside the configured workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = ListArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = ListArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        if not path.is_dir():
            return ToolResult.fail(f"Directory not found: {args.path}")

        iterator = path.rglob("*") if args.recursive else path.iterdir()
        entries = [
            {
                "path": self._paths.relative(entry),
                "type": "directory" if entry.is_dir() else "file",
            }
            for entry in sorted(iterator)
        ]
        return ToolResult.ok(entries)


class FilesystemWriteTool(Tool):
    name: ClassVar[str] = "filesystem_write"
    description: ClassVar[str] = "Write a UTF-8 text file inside the configured workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = WriteArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = WriteArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        if path.exists() and not args.overwrite:
            return ToolResult.fail(f"File already exists: {args.path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.content, encoding="utf-8")
        return ToolResult.ok(
            {"path": self._paths.relative(path), "bytes": len(args.content.encode("utf-8"))}
        )


class FilesystemSearchTool(Tool):
    name: ClassVar[str] = "filesystem_search"
    description: ClassVar[str] = (
        "Search UTF-8 text files for a literal string inside the workspace."
    )
    risk: ClassVar[ToolRisk] = ToolRisk.READ
    arguments_model: ClassVar[type[BaseModel]] = SearchArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = SearchArguments.model_validate(arguments.model_dump())
        root = self._paths.resolve(args.path)
        if not root.is_dir():
            return ToolResult.fail(f"Directory not found: {args.path}")

        results: list[dict[str, object]] = []
        for file_path in root.rglob(args.glob):
            if not file_path.is_file():
                continue
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for line_number, line in enumerate(lines, start=1):
                if args.query in line:
                    results.append(
                        {
                            "path": self._paths.relative(file_path),
                            "line": line_number,
                            "text": line,
                        }
                    )
                    if len(results) >= args.max_results:
                        return ToolResult.ok(results)
        return ToolResult.ok(results)
