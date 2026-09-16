from __future__ import annotations

import shutil
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from harness.tools.base import Tool, ToolResult, ToolRisk

_SAFE_ENV_EXAMPLES = {".env.example", ".env.sample", ".env.template"}
_SENSITIVE_DIRECTORY_NAMES = {".git", ".ssh", ".aws", ".azure", ".gnupg"}
_SENSITIVE_FILE_NAMES = {
    "credentials",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
    "service-account.json",
}
_SENSITIVE_SUFFIXES = {".key", ".p12", ".pem", ".pfx"}


class WorkspacePaths:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, raw_path: str) -> Path:
        candidate = (self.root / raw_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes workspace: {raw_path}") from exc
        if self.is_sensitive(candidate):
            raise ValueError(f"Sensitive workspace path is protected: {raw_path}")
        return candidate

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def is_sensitive(self, path: Path) -> bool:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(self.root)
        except ValueError:
            return True

        lowered_parts = [part.lower() for part in relative.parts]
        if any(part in _SENSITIVE_DIRECTORY_NAMES for part in lowered_parts[:-1]):
            return True
        if not lowered_parts:
            return False

        name = lowered_parts[-1]
        if name in _SENSITIVE_DIRECTORY_NAMES:
            return True
        if name.startswith(".env") and name not in _SAFE_ENV_EXAMPLES:
            return True
        if name in _SENSITIVE_FILE_NAMES:
            return True
        return Path(name).suffix.lower() in _SENSITIVE_SUFFIXES


class PathArguments(BaseModel):
    path: str


class ListArguments(BaseModel):
    path: str = "."
    recursive: bool = False


class WriteArguments(BaseModel):
    path: str
    content: str
    overwrite: bool = True


class PatchArguments(BaseModel):
    path: str
    old: str = Field(min_length=1)
    new: str
    expected_replacements: int = Field(default=1, ge=1)


class TransferArguments(BaseModel):
    source: str
    destination: str
    overwrite: bool = False


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


class FilesystemPatchTool(Tool):
    name: ClassVar[str] = "filesystem_patch"
    description: ClassVar[str] = "Replace an exact text fragment in a UTF-8 workspace file."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = PatchArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = PatchArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        if not path.is_file():
            return ToolResult.fail(f"File not found: {args.path}")
        content = path.read_text(encoding="utf-8")
        matches = content.count(args.old)
        if matches != args.expected_replacements:
            error = (
                f"Expected {args.expected_replacements} replacements in {args.path}, "
                f"found {matches}"
            )
            return ToolResult.fail(error)
        updated = content.replace(args.old, args.new, args.expected_replacements)
        path.write_text(updated, encoding="utf-8")
        return ToolResult.ok(
            {"path": self._paths.relative(path), "replacements": args.expected_replacements}
        )


class FilesystemMkdirTool(Tool):
    name: ClassVar[str] = "filesystem_mkdir"
    description: ClassVar[str] = "Create a directory inside the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = PathArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = PathArguments.model_validate(arguments.model_dump())
        path = self._paths.resolve(args.path)
        path.mkdir(parents=True, exist_ok=True)
        return ToolResult.ok({"path": self._paths.relative(path)})


class FilesystemCopyTool(Tool):
    name: ClassVar[str] = "filesystem_copy"
    description: ClassVar[str] = "Copy a file or directory inside the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = TransferArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = TransferArguments.model_validate(arguments.model_dump())
        source = self._paths.resolve(args.source)
        destination = self._paths.resolve(args.destination)
        if not source.exists():
            return ToolResult.fail(f"Source not found: {args.source}")
        if destination.exists() and not args.overwrite:
            return ToolResult.fail(f"Destination already exists: {args.destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=args.overwrite)
        else:
            shutil.copy2(source, destination)
        return ToolResult.ok({"path": self._paths.relative(destination)})


class FilesystemMoveTool(Tool):
    name: ClassVar[str] = "filesystem_move"
    description: ClassVar[str] = "Move a file or directory inside the workspace."
    risk: ClassVar[ToolRisk] = ToolRisk.WRITE
    arguments_model: ClassVar[type[BaseModel]] = TransferArguments

    def __init__(self, paths: WorkspacePaths) -> None:
        self._paths = paths

    async def execute(self, arguments: BaseModel) -> ToolResult:
        args = TransferArguments.model_validate(arguments.model_dump())
        source = self._paths.resolve(args.source)
        destination = self._paths.resolve(args.destination)
        if not source.exists():
            return ToolResult.fail(f"Source not found: {args.source}")
        if destination.exists():
            if not args.overwrite:
                return ToolResult.fail(f"Destination already exists: {args.destination}")
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)
        moved = Path(shutil.move(str(source), str(destination)))
        return ToolResult.ok({"path": self._paths.relative(moved)})


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
            if not file_path.is_file() or self._paths.is_sensitive(file_path):
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
