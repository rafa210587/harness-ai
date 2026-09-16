# Repository Design

> Status: proposed repository layout for the first implementation of the Local AI Harness.
>
> Related: `ARCHITECTURE.md`, `SETUP.md`, `AGENTS.md`

## 1. Goal

Keep the repository small enough that one engineer and one coding agent can understand the whole runtime, while leaving clear extension points for new LLM providers, tools, applications, skills and hooks.

The MVP is a local Python application with:

- DeepSeek as the first LLM provider.
- One agent loop.
- A tool registry.
- Filesystem and shell tools.
- Browser automation through Playwright.
- Blender automation through CLI + Python.
- Unity automation through CLI + Editor scripts.
- SQLite persistence.
- Human approval gates for risky operations.
- Structured events and artifacts.

The repository must not start as a framework. Every abstraction needs a concrete use in the MVP.

---

## 2. Repository layout

```text
local-ai-harness/
├── README.md
├── ARCHITECTURE.md
├── REPOSITORY.md
├── SETUP.md
├── AGENTS.md
├── CLAUDE.md
├── CHANGELOG.md
│
├── pyproject.toml
├── uv.lock
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
├── src/
│   └── harness/
│       ├── __init__.py
│       ├── cli.py
│       │
│       ├── runtime/
│       │   ├── agent_loop.py
│       │   ├── context.py
│       │   ├── session.py
│       │   ├── approvals.py
│       │   └── limits.py
│       │
│       ├── llm/
│       │   ├── base.py
│       │   └── deepseek.py
│       │
│       ├── tools/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── filesystem.py
│       │   ├── shell.py
│       │   ├── screenshot.py
│       │   ├── browser.py
│       │   ├── blender.py
│       │   ├── unity.py
│       │   └── image.py
│       │
│       ├── browser/
│       │   └── playwright_controller.py
│       │
│       ├── blender/
│       │   ├── controller.py
│       │   └── scripts/
│       │
│       ├── unity/
│       │   ├── controller.py
│       │   └── editor_templates/
│       │
│       ├── images/
│       │   ├── base.py
│       │   ├── interactive_chatgpt.py
│       │   └── providers/
│       │
│       ├── hooks/
│       │   ├── base.py
│       │   ├── dispatcher.py
│       │   └── builtin/
│       │       ├── audit.py
│       │       ├── permissions.py
│       │       └── artifacts.py
│       │
│       ├── storage/
│       │   ├── database.py
│       │   ├── repositories.py
│       │   └── artifacts.py
│       │
│       └── observability/
│           ├── events.py
│           └── logger.py
│
├── skills/
│   ├── README.md
│   └── _examples/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── fixtures/
│
├── scripts/
│   ├── doctor.py
│   ├── bootstrap.py
│   └── sync_agent_config.py
│
├── .claude/
│   ├── settings.example.json
│   ├── hooks/
│   │   ├── guard_destructive.py
│   │   ├── post_python_edit.py
│   │   └── verify_on_stop.py
│   └── skills/
│       ├── architecture-change/
│       │   └── SKILL.md
│       ├── add-tool/
│       │   └── SKILL.md
│       ├── add-llm-provider/
│       │   └── SKILL.md
│       ├── browser-integration/
│       │   └── SKILL.md
│       ├── blender-integration/
│       │   └── SKILL.md
│       ├── unity-integration/
│       │   └── SKILL.md
│       ├── security-review/
│       │   └── SKILL.md
│       └── test-change/
│           └── SKILL.md
│
├── .cursor/
│   └── rules/
│       └── project.mdc
│
├── workspace/
│   └── .gitkeep
│
└── data/
    └── .gitkeep
```

`workspace/` and `data/` are local runtime directories and must not contain committed runtime state.

---

## 3. Source-of-truth rules

We will not maintain three different architecture descriptions for Codex, Claude Code and Cursor.

The hierarchy is:

```text
ARCHITECTURE.md
      │
      ├── technical architecture and ADRs
      │
REPOSITORY.md
      │
      ├── repository boundaries and development structure
      │
AGENTS.md
      │
      ├── short mandatory engineering instructions
      │
.claude/skills/*
      │
      └── procedural playbooks loaded only when relevant
```

`AGENTS.md` is the main cross-agent instruction document.

`CLAUDE.md` should be a very small compatibility file telling Claude Code to read and follow `AGENTS.md`.

Cursor can also read `AGENTS.md`; `.cursor/rules/` should only contain Cursor-specific scoping if we later need it.

Skills are not a replacement for architecture documentation. Skills are procedures.

---

## 4. Build-time skills

These skills exist to help coding agents build this repository consistently.

### 4.1 `architecture-change`

Use when a change affects module boundaries, execution flow, persistence, security model, provider model, tool contract or public interfaces.

The skill must force the agent to:

1. Read `ARCHITECTURE.md`.
2. Identify which ADR is affected.
3. Prefer the smallest compatible change.
4. Avoid introducing infrastructure without a concrete MVP requirement.
5. Update architecture documentation if a real architectural decision changed.
6. Run relevant tests.

### 4.2 `add-tool`

Use whenever a new harness tool is created.

The skill should require:

```text
Tool schema
→ validation
→ risk classification
→ implementation
→ deterministic ToolResult
→ unit tests
→ integration test where practical
→ registry registration
→ documentation
```

Every tool must declare:

```python
name
description
input model/schema
risk level
timeout behavior
execute()
```

A tool must never bypass the Tool Registry.

### 4.3 `add-llm-provider`

Use for DeepSeek alternatives or future providers.

Required contract:

```text
provider configuration
authentication
request translation
tool schema translation
response parsing
tool call parsing
stream handling
error normalization
provider-specific tests
```

Provider-specific behavior must remain inside `src/harness/llm/`.

### 4.4 `browser-integration`

Use when changing Playwright or browser behavior.

The skill should enforce:

- locators before screen coordinates;
- browser semantic operations before desktop automation;
- explicit separation between read actions and side-effect actions;
- persistent profiles only when configured;
- no credentials committed to repository;
- screenshots/traces available for failed integration tests.

### 4.5 `blender-integration`

Use for Blender changes.

Priority:

```text
Blender Python API
→ Blender CLI/background mode
→ persistent Blender bridge later
→ GUI automation only as fallback
```

Generated Blender scripts must remain inspectable.

### 4.6 `unity-integration`

Use for Unity changes.

Priority:

```text
Unity CLI
→ Editor scripts
→ local editor bridge later
→ GUI automation only as fallback
```

Generated C# Editor scripts must remain isolated from normal game/runtime code whenever possible.

### 4.7 `security-review`

Use for changes that affect:

- shell execution;
- filesystem writes/deletes;
- browser form submission;
- secret loading;
- external network calls;
- privilege escalation;
- approvals;
- plugin/MCP execution.

The skill must inspect trust boundaries and approval behavior, not only conventional code vulnerabilities.

### 4.8 `test-change`

Use before declaring a meaningful feature complete.

The skill should determine the smallest correct test set and run:

```text
unit tests
contract tests
integration tests
lint
type checking
```

It should not blindly run expensive external application tests when the change cannot affect them.

---

## 5. Product/runtime skills

Do not confuse the coding-agent skills above with skills used by our own harness.

The harness may eventually load reusable procedural skills from:

```text
skills/<skill-name>/SKILL.md
```

Examples:

```text
skills/
├── create-blender-prop/
├── import-asset-to-unity/
├── inspect-unity-scene/
├── browser-research/
└── generate-game-texture/
```

This loader is NOT required for the first vertical slice.

For MVP phase 1, DeepSeek receives tools directly.

A runtime skill loader should only be introduced when we have repeated procedures that are clearly better represented as reusable instructions than Python orchestration code.

---

## 6. Build-time hooks

Build-time hooks are automation around development. They are not part of the runtime hook system.

### 6.1 Git hooks

Use `pre-commit`.

Fast checks on commit:

```text
ruff format
ruff check
basic repository checks
secret/file-size checks if added later
```

Heavier checks belong on push or CI:

```text
pytest
mypy
coverage thresholds
```

Do not put Blender/Unity end-to-end tests in every commit hook.

### 6.2 Claude Code hooks

Initial useful hooks:

#### `PreToolUse`

`guard_destructive.py`

Purpose:

- reject destructive commands outside the repository;
- reject accidental access to secrets;
- reject `git reset --hard`, destructive checkout/clean operations, recursive delete and equivalent commands unless explicitly approved;
- reject writes outside allowed roots.

#### `PostToolUse`

`post_python_edit.py`

Purpose:

- when Python files change, run targeted Ruff checks;
- do not run the full test suite after every edit.

#### `Stop`

`verify_on_stop.py`

Purpose:

- optionally run a fast repository health check before the coding session is considered complete;
- report failures to the agent;
- avoid hiding errors.

These hooks are convenience/guardrails. Repository correctness must not depend exclusively on one coding assistant supporting them.

---

## 7. Runtime hooks

Runtime hooks are part of the product.

Use a small event-driven hook dispatcher.

Initial events:

```text
SESSION_START
SESSION_END

BEFORE_LLM_REQUEST
AFTER_LLM_RESPONSE
LLM_ERROR

BEFORE_TOOL
AFTER_TOOL
TOOL_ERROR

BEFORE_APPROVAL
AFTER_APPROVAL

ARTIFACT_CREATED
CONTEXT_COMPACTED
```

Do not allow arbitrary plugin code to mutate everything in the first version.

A hook receives an immutable event object and returns an optional decision/result.

Example:

```python
@dataclass(frozen=True)
class BeforeToolEvent:
    session_id: str
    tool_name: str
    arguments: dict[str, object]
    risk: ToolRisk
```

A permission hook may return:

```python
HookDecision(
    action="allow" | "deny" | "require_approval",
    reason="..."
)
```

The default runtime hooks are:

```text
permissions
audit
artifact tracking
```

Future hooks may add:

```text
telemetry
redaction
cost accounting
policy
notifications
```

---

## 8. Module boundaries

### `runtime/`

Owns orchestration.

It can depend on:

```text
llm
tools
hooks
storage
observability
```

It must not contain Blender, Unity or Playwright implementation details.

### `llm/`

Owns communication with model providers.

It must return normalized harness objects.

No tool implementation belongs here.

### `tools/`

Owns the public tool contracts exposed to the LLM.

Application-specific mechanics may delegate to controllers.

### `browser/`, `blender/`, `unity/`

Own application integration details.

They do not decide agent behavior.

### `hooks/`

Owns deterministic interception/event behavior.

Hooks should not become another hidden orchestration framework.

### `storage/`

Owns SQLite persistence and artifact metadata.

No LLM logic.

### `observability/`

Owns structured events/logging.

Observability failures should not normally crash the agent session.

---

## 9. Dependency direction

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
browser → runtime
unity → agent_loop
storage → tools
llm → blender
```

The application adapters must remain callable without knowing the agent loop.

---

## 10. Tests

### Unit

Fast and isolated.

Examples:

```text
tool schema validation
permission decisions
context building
DeepSeek response parser
artifact metadata
SQLite repositories
```

### Contract

Verify interfaces independently of real applications.

Examples:

```text
all tools return ToolResult
all providers return normalized LLMResponse
all hooks return valid HookDecision
```

### Integration

Use real local components when practical.

Examples:

```text
SQLite
filesystem sandbox
subprocess
Playwright + local test page
```

### External application integration

Explicitly marked tests:

```text
@pytest.mark.blender
@pytest.mark.unity
@pytest.mark.browser_external
```

These are not part of the default fast suite.

---

## 11. Branch and commit policy

For the first stage:

```text
main
feature/<short-name>
fix/<short-name>
```

A feature should be small enough to review as one coherent vertical change.

Prefer vertical slices:

```text
DeepSeek request → parsed response
```

then:

```text
tool call → filesystem tool → result
```

then:

```text
DeepSeek → tool registry → filesystem
```

instead of creating 40 empty interfaces before the first task runs.

---

## 12. Definition of done for a code change

A normal change is complete when:

1. The implementation works.
2. Relevant tests exist.
3. `ruff check` passes.
4. `ruff format --check` passes.
5. `mypy` passes for affected typed modules once type checking is enabled.
6. No secret is committed.
7. Architecture docs are updated if a decision changed.
8. New dangerous behavior has an explicit approval/risk decision.
9. The coding agent reports what it actually verified.

---

## 13. First repository milestones

### M0 — bootstrap

Deliver:

```text
pyproject.toml
uv.lock
CLI entrypoint
configuration loader
structured logging
tests running
pre-commit
AGENTS.md
```

### M1 — DeepSeek echo

Deliver:

```text
DeepSeek provider
simple request
stream/non-stream decision
normalized response
provider tests
```

### M2 — first real tool

Deliver:

```text
Tool base
Tool Registry
filesystem.list
filesystem.read
shell.run
permission hook
```

Target:

```bash
harness run "List this project's Python files."
```

### M3 — autonomous tool loop

Target:

```text
DeepSeek
→ requests tool
→ harness validates
→ tool executes
→ result returns to DeepSeek
→ DeepSeek finishes task
```

This is the first true harness milestone.

### M4 — browser

Playwright vertical slice.

### M5 — Blender

Create cube → render → artifact.

### M6 — Unity

Import artifact → refresh → inspect result.

---

## 14. Principle for future growth

Add a framework only when a measured problem requires it.

Before introducing LangGraph, Temporal, Redis, PostgreSQL, a vector database, an MCP gateway or a multi-agent scheduler, document:

```text
What exact problem exists?
Why cannot the current loop solve it?
What failure/metric proves the need?
What is the smallest dependency that solves it?
```

This constraint is intentional.
