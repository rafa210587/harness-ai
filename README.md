# harness-ai

A small local AI harness for tool-driven computer workflows.

The MVP uses DeepSeek as the first LLM provider and exposes local capabilities as explicit tools: filesystem, shell, browser, Blender, Unity, images, screenshots and optional runtime skills. Desktop coordinate automation remains a later fallback, not the primary integration model.

## Status

The core harness is implemented and covered by automated tests. Current capabilities include:

```text
DeepSeek provider
→ provider-neutral timeout/retry
→ Agent Loop
→ Tool Registry
→ filesystem/shell/browser/Blender/Unity tools
→ deterministic permissions/approvals
→ SQLite persistence/artifacts/events
→ verification/self-correction
→ context compaction
→ runtime skills
→ evals/metrics
```

Real DeepSeek, Chromium, Blender and Unity validation on the target Windows machine remains a separate acceptance gate.

- [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) defines the durable build order and exit criteria.
- [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) records what is implemented, what CI proves, and what still needs local validation.

## Development stack

- Python 3.12
- `uv` for environments/dependencies/lockfile
- Typer + Rich for CLI
- Pydantic for contracts/configuration
- SQLite / `aiosqlite` for persistence
- Playwright for browser automation
- Blender CLI + Python for Blender integration
- Unity CLI + Editor scripts for Unity integration

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

After configuring credentials/application paths:

```powershell
uv run harness doctor --online
uv run harness eval evals/smoke.yaml --json-out data/smoke-report.json
```

## Source of truth

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture, ADRs, MVP and execution model.
- [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) — complete implementation roadmap, ownership and exit criteria.
- [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) — evidence-based current status.
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
