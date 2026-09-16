# AGENTS.md

## Project

This repository implements a small local AI harness.

Read these documents before architectural changes:

1. `ARCHITECTURE.md`
2. `REPOSITORY.md`
3. `SETUP.md`

## Core constraints

- Use Python 3.12 and `uv`.
- Keep the core runtime small and explicit.
- Do not introduce LangChain, LangGraph, Temporal, Redis, PostgreSQL, a vector database, Kubernetes or a multi-agent framework without a concrete requirement and architecture decision.
- Prefer vertical slices over speculative abstractions.
- DeepSeek is the first LLM provider; provider-specific code stays behind the provider interface.
- All LLM-visible capabilities go through the Tool Registry.
- Blender/Unity/browser implementation details do not belong in the agent loop.
- Prefer APIs, CLI and application scripting over mouse/keyboard automation.
- Risky side effects must pass through approval/permission enforcement.
- Never commit credentials, browser session secrets or `.env`.

## Change workflow

Use `.claude/skills/feature-workflow/SKILL.md` to classify every non-trivial change.

```text
small  -> inspect -> change -> test
medium -> refine -> SPEC -> TASKS -> implement -> simplify -> review
large  -> refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review
```

Rules:

- Small changes do not get planning documents.
- Medium/large work artifacts live under `.work/<feature>/` and are not committed.
- Specs define behavior and acceptance criteria before implementation.
- Plans/tasks must not restate the spec.
- Review is a separate pass and must not modify code while producing findings.
- Temporary work artifacts are removed when the feature is complete.
- Permanent docs change only when a lasting repository decision changed.
- Do not create separate subagents just to implement this workflow; skills are the default until independent agents show measurable value.

## Before editing

Investigate relevant code first. Do not infer implementation details from filenames alone.

For a non-trivial change:

1. classify it with `feature-workflow`;
2. inspect the affected module and tests;
3. create only the temporary artifacts required by the classification;
4. use the matching technical skill when applicable.

## Skills

Workflow:

- `.claude/skills/feature-workflow/SKILL.md`
- `.claude/skills/refine-feature/SKILL.md`
- `.claude/skills/spec-feature/SKILL.md`
- `.claude/skills/plan-feature/SKILL.md`
- `.claude/skills/implement-feature/SKILL.md`
- `.claude/skills/simplify-change/SKILL.md`
- `.claude/skills/review-change/SKILL.md`
- `.claude/skills/concise-docs/SKILL.md`

Technical:

- `.claude/skills/architecture-change/SKILL.md`
- `.claude/skills/add-tool/SKILL.md`
- `.claude/skills/add-llm-provider/SKILL.md`
- `.claude/skills/browser-integration/SKILL.md`
- `.claude/skills/blender-integration/SKILL.md`
- `.claude/skills/unity-integration/SKILL.md`
- `.claude/skills/security-review/SKILL.md`
- `.claude/skills/test-change/SKILL.md`

If the current coding agent does not auto-discover these files, read the relevant skill as normal repository context.

## Dependency rules

Runtime dependencies need a concrete runtime purpose. Check the standard library and existing dependencies first.

```powershell
uv add <package>
uv add --dev <package>
```

Never edit `uv.lock` manually.

## Python

Prefer:

- typed core contracts;
- small modules;
- explicit dataclasses/Pydantic models;
- async only when I/O concurrency benefits from it;
- constructor/function dependency injection;
- domain-specific errors normalized at boundaries.

Avoid:

- broad `except Exception` without useful normalization/re-raise;
- mutable global session state;
- provider-specific types leaking into runtime;
- application-controller types leaking into tool schemas;
- abstractions with no current use.

## Tools

Every tool defines:

```text
name
description
input schema
risk classification
timeout behavior
result contract
```

Every execution path returns a normalized `ToolResult`. Preserve useful stderr/errors. A tool must not perform behavior more dangerous than its declared risk level.

## Runtime hooks

Runtime hooks are product behavior. Development hooks under `.claude/hooks/` are not runtime hooks. Do not couple them.

## Tests

Run the smallest relevant test set first.

Before a substantial change is complete:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -m "not blender and not unity and not browser_external"
```

Run Blender/Unity/external browser tests only when relevant and supported by the environment. Do not change tests merely to make incorrect behavior pass.

## Documentation

Follow `.claude/skills/concise-docs/SKILL.md`.

- `ARCHITECTURE.md`: lasting architecture/ADRs.
- `REPOSITORY.md`: repository boundaries/workflow.
- `SETUP.md`: environment/dependency setup.
- `SKILLS_HOOKS.md`: skill/hook model.
- `.work/`: temporary refinement/spec/plan/task artifacts.

Do not duplicate the same rule across permanent documents.

## Git

Do not run destructive operations such as `git reset --hard`, `git clean -fd`, force push or deleting unrelated user changes unless explicitly requested.

Keep commits logically scoped.

## Completion report

State:

- what changed;
- what was tested;
- what was not tested;
- remaining limitations/findings.

Do not claim a workflow works if it was not actually executed.
