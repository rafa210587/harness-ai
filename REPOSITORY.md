# Repository Design

> Repository structure and engineering workflow. Architecture lives in `ARCHITECTURE.md`; setup lives in `SETUP.md`.

## 1. Goal

Keep the MVP understandable by one engineer and one coding agent.

Core stack:

```text
Python 3.12 + uv
DeepSeek provider
single agent loop
Tool Registry
SQLite
Playwright
Blender CLI/Python
Unity CLI/Editor scripts
```

Do not turn the repository into a framework before concrete requirements require it.

## 2. Layout

```text
harness-ai/
├── ARCHITECTURE.md
├── REPOSITORY.md
├── SETUP.md
├── AGENTS.md
├── CLAUDE.md
├── SKILLS_HOOKS.md
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── uv.lock                 # generated/resolved by uv
├── .python-version
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
│
├── config/
│   ├── harness.example.yaml
│   ├── models.example.yaml
│   └── permissions.example.yaml
│
├── src/harness/
│   ├── cli.py
│   ├── runtime/
│   ├── llm/
│   ├── tools/
│   ├── browser/
│   ├── blender/
│   ├── unity/
│   ├── images/
│   ├── hooks/
│   ├── storage/
│   └── observability/
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── fixtures/
│
├── .claude/
│   ├── settings.json
│   ├── hooks/
│   └── skills/
│
├── .cursor/rules/
├── skills/                 # future runtime skills for the harness itself
├── scripts/
├── workspace/              # local runtime state, ignored except .gitkeep
└── data/                   # local runtime state, ignored except .gitkeep
```

Temporary feature artifacts live in `.work/` and are fully ignored by Git.

## 3. Sources of truth

```text
ARCHITECTURE.md  lasting architecture and ADRs
REPOSITORY.md    repository boundaries and workflow
SETUP.md         environment/dependencies/setup
AGENTS.md        mandatory coding-agent instructions
SKILLS_HOOKS.md  skill/hook model and catalog
.claude/skills/  procedural playbooks
```

Do not duplicate the same detailed rule across files.

## 4. Feature workflow

Classify changes before implementation.

### Small

Examples: typo, local bug, simple config/message/timeout change.

```text
inspect -> change -> test
```

No planning artifacts.

### Medium

Examples: new tool, CLI command, contained provider/integration capability.

```text
refine -> SPEC -> TASKS -> implement -> simplify -> review
```

Temporary files:

```text
.work/<feature>/SPEC.md
.work/<feature>/TASKS.md
```

Create `PLAN.md` only when ordering/migration is non-obvious.

### Large

Examples: agent loop, persistent application bridge, storage/approval architecture, MCP integration.

```text
refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review
```

Temporary files:

```text
.work/<feature>/REFINEMENT.md
.work/<feature>/SPEC.md
.work/<feature>/PLAN.md
.work/<feature>/TASKS.md
```

Remove `.work/<feature>/` after completion unless explicitly requested otherwise.

Permanent docs change only when a lasting decision changes.

## 5. Skills

Workflow skills:

```text
feature-workflow
refine-feature
spec-feature
plan-feature
implement-feature
simplify-change
review-change
concise-docs
```

Technical skills:

```text
architecture-change
add-tool
add-llm-provider
browser-integration
blender-integration
unity-integration
security-review
test-change
```

Use skills as roles/processes first. Do not introduce multi-agent orchestration only to separate architect/implementer/reviewer roles; add real subagents later only if measured results justify the coordination cost.

## 6. Module ownership

### `runtime/`

Owns orchestration: session, context, agent loop, limits and approvals.

May depend on `llm`, `tools`, `hooks`, `storage`, `observability`.

Must not contain Playwright/Blender/Unity implementation details.

### `llm/`

Owns provider communication and normalization. Provider-specific types must not leak into runtime.

### `tools/`

Owns LLM-visible tool contracts and the Tool Registry. Application mechanics delegate to controllers.

### `browser/`, `blender/`, `unity/`, `images/`

Own application/provider-specific mechanics. They do not decide agent behavior.

### `hooks/`

Owns deterministic runtime interception/decisions. Do not turn hooks into hidden orchestration.

### `storage/`

Owns SQLite persistence and artifact metadata.

### `observability/`

Owns structured events/logging. Observability failures should not normally terminate sessions.

## 7. Dependency direction

Allowed:

```text
cli
 ↓
runtime
 ↓
llm / tools / hooks / storage / observability

tools
 ↓
browser / blender / unity / images
```

Avoid:

```text
browser -> runtime
unity -> agent_loop
storage -> tools
llm -> blender
```

## 8. Tool contract

Every LLM-visible tool declares:

```text
name
description
input schema
risk level
timeout behavior
execute()
```

Every execution path returns normalized `ToolResult` data. Tools never bypass the Tool Registry or permission layer.

## 9. Tests

```text
unit        fast isolated behavior
contract    provider/tool/hook interface guarantees
integration real local components such as SQLite/filesystem/Playwright local page
external    explicitly marked Blender/Unity/external-browser tests
```

External markers:

```text
@pytest.mark.blender
@pytest.mark.unity
@pytest.mark.browser_external
```

Do not run expensive external-application tests for unrelated changes.

## 10. Definition of done

A non-trivial change is done when:

1. Acceptance criteria are satisfied.
2. Relevant tests exist and pass.
3. Ruff formatting/lint pass.
4. Mypy passes for affected typed code.
5. Risk/approval behavior is explicit for new side effects.
6. Simplification pass is complete.
7. Review has no unresolved P0/P1 findings.
8. Permanent docs are updated only if a lasting decision changed.
9. Temporary `.work/` artifacts are removed.
10. The completion report states what was and was not verified.

## 11. Git

Initial branch convention:

```text
main
feature/<short-name>
fix/<short-name>
```

Prefer coherent vertical changes over large speculative scaffolds.

## 12. MVP milestones

```text
M0 bootstrap          CLI/config/logging/tests/pre-commit
M1 DeepSeek echo      provider + normalized response
M2 first tools        Tool Registry + filesystem + shell + permissions
M3 autonomous loop    model -> tool -> observation -> model
M4 browser            Playwright vertical slice
M5 Blender            create cube -> render -> artifact
M6 Unity              import artifact -> refresh -> inspect
```

Before adding LangGraph, Temporal, Redis, PostgreSQL, vector DB, MCP gateway or multi-agent orchestration, document the concrete problem that the current design cannot solve.
