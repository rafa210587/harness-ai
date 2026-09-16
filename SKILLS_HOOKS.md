# Skills and Hooks

This repository uses three different mechanisms:

```text
skills            repeatable engineering procedures
development hooks safeguards around coding-agent/Git activity
runtime hooks     deterministic product behavior around harness events
```

Do not mix them.

## 1. Coding-agent workflow skills

Project skills live under `.claude/skills/<name>/SKILL.md`.

The default feature flow is:

```text
small  -> inspect -> change -> test
medium -> refine -> SPEC -> TASKS -> implement -> simplify -> review
large  -> refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review
```

Workflow skills:

| Skill | Purpose |
|---|---|
| `feature-workflow` | Classify change and choose minimum process. |
| `refine-feature` | Turn an ambiguous request into bounded scope. |
| `spec-feature` | Define behavior, constraints and acceptance criteria. |
| `plan-feature` | Produce concise PLAN/TASKS when needed. |
| `implement-feature` | Execute the approved spec/tasks. |
| `simplify-change` | Remove accidental complexity without changing behavior. |
| `review-change` | Independent findings-only review pass. |
| `concise-docs` | Prevent redundant or temporary permanent documentation. |

Temporary artifacts belong under `.work/<feature>/` and are ignored by Git.

Typical large feature:

```text
.work/<feature>/
├── REFINEMENT.md
├── SPEC.md
├── PLAN.md
└── TASKS.md
```

Medium features normally need only `SPEC.md` and `TASKS.md`. Small changes need none.

## 2. Technical skills

Technical skills constrain implementation in specific areas:

| Skill | Scope |
|---|---|
| `architecture-change` | Module boundaries, contracts and architecture decisions. |
| `add-tool` | New LLM-visible Tool contract/registration/tests. |
| `add-llm-provider` | Provider auth, mapping, tool calls, normalization. |
| `browser-integration` | Playwright/browser safety and semantics. |
| `blender-integration` | Blender Python/CLI integration. |
| `unity-integration` | Unity CLI/Editor integration. |
| `security-review` | Trust boundaries, side effects, secrets and approvals. |
| `test-change` | Select and execute the correct verification scope. |

Workflow and technical skills can be combined. Example:

```text
feature-workflow
-> spec-feature
-> plan-feature
-> add-tool
-> implement-feature
-> security-review
-> simplify-change
-> review-change
```

## 3. Why skills before multiple agents

The project does not create separate Architect/Implementer/Reviewer agents yet.

Reasons:

- less duplicated context;
- fewer handoff errors;
- lower orchestration complexity;
- easier evaluation of whether specialization actually helps.

Skills define the roles now. Independent subagents can be introduced later if measured results justify them.

The review pass is logically independent even when executed by the same coding system: while reviewing, it must not modify code.

## 4. Development hooks

Development hooks are safeguards for repository work.

Current Claude Code hooks:

```text
PreToolUse  -> .claude/hooks/guard_destructive.py
PostToolUse -> .claude/hooks/post_python_edit.py
Stop        -> .claude/hooks/verify_on_stop.py
```

Git/pre-commit handles fast formatting/lint/file-hygiene checks.

These hooks are convenience and enforcement around development. Repository correctness must not depend on a specific coding assistant supporting them.

## 5. Runtime hooks

Runtime hooks belong to `src/harness/hooks/` and are part of the product.

Initial lifecycle:

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

A permission hook can return:

```text
allow
deny
require_approval
```

Decision precedence:

```text
deny > require_approval > allow
```

Security policy belongs in deterministic runtime code/configuration, not only in prompts.

## 6. Skills vs tools vs hooks

```text
Skill: how should a repeatable procedure be performed?
Tool:  what concrete capability can the model invoke?
Hook:  what deterministic behavior runs around an event?
```

Example:

```text
Skill -> create and validate a Blender prop
Tool  -> blender.execute_python
Hook  -> require approval before filesystem.delete
```

Runtime procedural skills under `skills/` are a future harness capability and are not part of the first MVP milestone.
