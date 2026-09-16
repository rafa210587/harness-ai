# AGENTS.md

## Project

This repository implements a small local AI harness.

Read these documents before making architectural changes:

1. `ARCHITECTURE.md`
2. `REPOSITORY.md`
3. `SETUP.md`

## Core constraints

- Use Python 3.12 for the harness.
- Use `uv` for Python/environment/dependency management.
- Keep the core runtime small and explicit.
- Do not introduce LangChain, LangGraph, Temporal, Redis, PostgreSQL, a vector database, Kubernetes or a multi-agent framework without a concrete requirement and an architecture decision.
- Prefer vertical slices that run end-to-end over speculative abstractions.
- DeepSeek is the first LLM provider, but provider-specific code must stay behind the provider interface.
- Tools are the main capability boundary.
- All LLM-visible tools must go through the Tool Registry.
- Blender/Unity/browser implementation details do not belong in the agent loop.
- Prefer APIs, CLI and application scripting over mouse/keyboard automation.
- Risky side effects must pass through the approval/permission layer.
- Never commit credentials, browser session secrets or `.env`.

## Before editing

Investigate the relevant code first. Do not infer implementation details from filenames alone.

For a non-trivial change:

1. identify the affected module boundary;
2. identify the smallest vertical behavior to change;
3. inspect relevant tests;
4. use the matching repository skill if one exists under `.claude/skills/`.

## Skills

Use these playbooks when applicable:

- `.claude/skills/architecture-change/SKILL.md`
- `.claude/skills/add-tool/SKILL.md`
- `.claude/skills/add-llm-provider/SKILL.md`
- `.claude/skills/browser-integration/SKILL.md`
- `.claude/skills/blender-integration/SKILL.md`
- `.claude/skills/unity-integration/SKILL.md`
- `.claude/skills/security-review/SKILL.md`
- `.claude/skills/test-change/SKILL.md`

Even when the current coding agent does not auto-discover these skill files, read the relevant file as normal repository context.

## Dependency rules

Runtime dependencies must have a concrete runtime purpose.

Before adding a dependency, check whether the standard library or an existing dependency already solves the requirement.

Use:

```powershell
uv add <package>
```

Development-only dependency:

```powershell
uv add --dev <package>
```

Never edit `uv.lock` manually.

## Python

Core contracts should be typed.

Prefer:

- small modules;
- explicit dataclasses/Pydantic models;
- async only when I/O concurrency benefits from it;
- dependency injection through constructors/functions rather than global mutable registries;
- domain-specific exceptions normalized at boundaries.

Avoid:

- broad `except Exception` without re-raising/normalization;
- implicit magic;
- mutable global session state;
- provider-specific types leaking into runtime;
- application-controller types leaking into tool schemas.

## Tools

When adding a tool, define:

```text
name
description
input schema
risk classification
timeout behavior
result contract
```

Every execution path returns a normalized `ToolResult`.

Tool failures are data for the agent. Preserve useful stderr/errors.

A tool must not silently perform a more dangerous action than its declared risk level.

## Runtime hooks

Runtime hooks are product behavior.

Development hooks under `.claude/hooks/` are not runtime hooks.

Do not couple them.

## Tests

For normal changes, run the smallest relevant test set first.

Before considering a substantial change complete:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -m "not blender and not unity and not browser_external"
```

Run Blender/Unity/external browser tests only when relevant and the environment supports them.

Do not change tests merely to make incorrect behavior pass.

## Documentation

Update `ARCHITECTURE.md` when an architectural decision changes.

Update `SETUP.md` when a machine/setup/dependency requirement changes.

Update `REPOSITORY.md` when repository ownership/boundaries/conventions change.

Do not duplicate the same detailed rule across all three files.

## Git

Do not:

```text
git reset --hard
git clean -fd
force push
delete unrelated user changes
```

unless the user explicitly requests that exact destructive operation.

Keep commits logically scoped.

## Completion report

When finishing implementation work, state:

- what changed;
- what was tested;
- what was not tested;
- any remaining limitation.

Do not claim a tool/application workflow works if it was not actually executed.
