# Skills and Hooks Plan

> This document distinguishes three mechanisms that sound similar but solve different problems:
>
> 1. coding-agent skills;
> 2. development hooks;
> 3. Local AI Harness runtime hooks.

## 1. Coding-agent skills

A skill is a reusable procedural playbook.

Use a skill for repeatable engineering work that would otherwise require pasting the same checklist into a coding agent.

Project skills live under:

```text
.claude/skills/<skill-name>/SKILL.md
```

Claude Code can discover these directly. Other coding agents should be instructed by `AGENTS.md` to read the same files as repository context.

Do not place basic always-on project facts in skills. Those belong in `AGENTS.md`.

---

## 2. Initial skill set

### `architecture-change`

Use when changing:

```text
agent loop
tool contract
provider contract
session model
hooks
storage
approval model
module boundaries
```

Success criteria:

- architecture read first;
- impact identified;
- smallest viable change;
- ADR/doc updated when needed;
- no unnecessary framework introduced.

### `add-tool`

Use whenever a new LLM-visible capability is added.

Required workflow:

```text
define contract
→ define risk
→ implement
→ normalize result/errors
→ register
→ unit test
→ integration test if possible
→ document
```

### `add-llm-provider`

Use for new model providers.

Required workflow:

```text
configuration
→ auth
→ request mapping
→ tool mapping
→ response/tool-call normalization
→ error normalization
→ tests
```

### `browser-integration`

Rules:

```text
semantic locator > coordinates
browser API > desktop automation
read side effect classification is mandatory
persistent authenticated profile must be explicit
```

### `blender-integration`

Rules:

```text
Python API > CLI > local bridge > GUI automation
generated scripts are inspectable artifacts
```

### `unity-integration`

Rules:

```text
CLI/Editor API > local bridge > GUI automation
keep generated Editor-only code isolated
```

### `security-review`

Review:

```text
commands
paths
secrets
network destinations
browser side effects
privilege
approval bypasses
tool risk metadata
plugin/MCP boundaries
```

### `test-change`

Select the correct test scope instead of running everything blindly.

---

## 3. Future runtime skills

Our own harness may later support:

```text
skills/<name>/SKILL.md
```

Candidate runtime skills:

```text
create-blender-prop
import-asset-to-unity
inspect-unity-scene
browser-research
debug-unity-console
generate-texture
verify-game-object
```

Do not implement the skill loader in the first milestone.

The first milestone only needs:

```text
model
→ tools
→ observations
→ loop
```

---

## 4. Development hooks

Development hooks act around the coding workflow.

Recommended initial Claude Code hooks:

```text
PreToolUse  → guard dangerous commands/writes
PostToolUse → run targeted Python formatting/lint after edits
Stop        → run a small final verification
```

Recommended Git hooks:

```text
pre-commit → formatting + lint + file hygiene
pre-push   → test + type-check
```

These are safeguards, not architecture.

The repository must remain buildable when somebody uses a coding agent that does not support these hooks.

---

## 5. Runtime hooks

Runtime hooks belong to `src/harness/hooks/`.

Initial event lifecycle:

```text
SESSION_START

BEFORE_LLM_REQUEST
AFTER_LLM_RESPONSE
LLM_ERROR

BEFORE_TOOL
AFTER_TOOL
TOOL_ERROR

BEFORE_APPROVAL
AFTER_APPROVAL

ARTIFACT_CREATED

SESSION_END
```

Initial built-ins:

```text
PermissionHook
AuditHook
ArtifactHook
```

Potential later hooks:

```text
RedactionHook
CostHook
TelemetryHook
NotificationHook
PolicyHook
```

---

## 6. Tool execution lifecycle

Target:

```text
DeepSeek requests tool
        │
        ▼
Tool Registry resolves tool
        │
        ▼
BEFORE_TOOL hooks
        │
        ├─ deny ──────────────► ToolResult denied
        │
        ├─ require approval ──► approval flow
        │
        └─ allow
        │
        ▼
tool.execute()
        │
        ├─ success
        │    ▼
        │  AFTER_TOOL hooks
        │
        └─ failure
             ▼
           TOOL_ERROR hooks
        │
        ▼
normalized ToolResult
        │
        ▼
DeepSeek continues
```

The hook system should not call the LLM by itself in the MVP.

---

## 7. Hook contract

Example:

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class HookAction(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class HookDecision:
    action: HookAction
    reason: str | None = None


@dataclass(frozen=True)
class BeforeToolEvent:
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    risk: str
```

The dispatcher combines decisions conservatively:

```text
DENY wins
then REQUIRE_APPROVAL
then ALLOW
```

This keeps the security behavior deterministic.

---

## 8. Initial permission hook

Example policy:

```text
filesystem.read        auto
filesystem.list        auto
filesystem.write       auto inside workspace
filesystem.delete      approval

shell.run              auto for normal commands
shell elevated         approval
dangerous commands     deny or approval

browser.navigate       auto
browser.read           auto
browser.submit         approval
browser.purchase       deny

blender changes        auto within configured project
unity changes          auto within configured project

git commit             auto/configurable
git push               approval
```

Configuration belongs in:

```text
config/permissions.yaml
```

Policy belongs in code + configuration, not in an LLM prompt.

---

## 9. Why hooks instead of prompt rules for safety

Prompt instructions are probabilistic.

Permission checks must be deterministic.

The model may decide:

```text
"I should not delete this"
```

but the runtime must independently decide whether:

```text
filesystem.delete(...)
```

is permitted.

Therefore:

```text
prompt = behavior guidance
hook/policy = enforcement
```

---

## 10. Skills vs tools vs hooks

Use this test:

### Skill

"How should the agent perform this repeatable procedure?"

Example:

```text
How to create and validate a Blender game prop.
```

### Tool

"What concrete capability can the model invoke?"

Example:

```text
blender.execute_python
```

### Hook

"What deterministic behavior runs around a lifecycle event?"

Example:

```text
Require approval before filesystem.delete.
```

Do not implement procedural skills as hundreds of Python branches.

Do not implement security policy only as a skill.

Do not expose every internal hook as an LLM tool.
