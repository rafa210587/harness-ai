# harness-ai

A small local AI harness for tool-driven computer workflows.

The MVP uses DeepSeek as the first LLM provider and is designed to expose local capabilities as explicit tools: filesystem, shell, browser, Blender, Unity, images, screenshots and later optional desktop automation.

## Status

Repository bootstrap / MVP architecture.

The first implementation milestone is:

```text
User → DeepSeek → Agent Loop → Tool Registry → filesystem/shell → result → DeepSeek
```

Browser, Blender and Unity are added as subsequent vertical slices.

The complete build order, manual actions and phase exit criteria are in [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md).

## Development stack

- Python 3.12
- `uv` for environments/dependencies/lockfile
- Typer + Rich for CLI
- Pydantic for contracts/configuration
- SQLite / `aiosqlite` for persistence
- Playwright for browser automation
- Blender CLI + Python for the first Blender integration
- Unity CLI + Editor scripts for the first Unity integration

## Start

```powershell
git clone https://github.com/rafa210587/harness-ai.git
cd harness-ai

uv python install 3.12
uv sync
uv run playwright install chromium

Copy-Item .env.example .env
uv run harness doctor
```

The first local `uv sync` will create the lockfile if it is not present yet.

## Source of truth

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture, ADRs, MVP and execution model.
- [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) — complete implementation roadmap, ownership and exit criteria.
- [`REPOSITORY.md`](REPOSITORY.md) — repository structure and boundaries.
- [`SETUP.md`](SETUP.md) — complete machine/environment setup.
- [`AGENTS.md`](AGENTS.md) — cross-agent engineering rules and feature workflow.
- [`SKILLS_HOOKS.md`](SKILLS_HOOKS.md) — skills, development hooks and runtime hooks.
- [`CLAUDE.md`](CLAUDE.md) — Claude Code compatibility entrypoint.

## Coding-agent configuration

- `.claude/skills/` contains focused engineering playbooks.
- `.claude/hooks/` contains development guardrails.
- `.claude/settings.json` enables the repository Claude Code hooks.
- `.cursor/rules/project.mdc` points Cursor to the same source-of-truth rules.
- root `AGENTS.md` is the shared instruction source for Codex and other coding agents.

## Design constraint

Do not turn the MVP into a framework before a measured requirement exists. The core loop must remain explicit, and new capabilities should normally enter the system as tools.
