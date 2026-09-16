# Feature Workflow

Use this skill to choose the minimum process required for a change.

## Classify first

### Small
Examples: typo, localized bug, timeout/config/message adjustment, trivial test fix.

Workflow:

```text
inspect -> change -> test -> done
```

Do not create SPEC/PLAN/TASKS.

### Medium
Examples: new tool, CLI command, provider capability, contained integration behavior.

Workflow:

```text
refine -> SPEC -> TASKS -> implement -> simplify -> review -> done
```

Create temporary artifacts under `.work/<feature>/`:

```text
SPEC.md
TASKS.md
```

Create `PLAN.md` only when sequencing or migration risk is non-obvious.

### Large
Examples: agent loop, new bridge, persistence model change, approval architecture, MCP integration.

Workflow:

```text
refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review -> fix findings -> done
```

Temporary artifacts:

```text
.work/<feature>/REFINEMENT.md
.work/<feature>/SPEC.md
.work/<feature>/PLAN.md
.work/<feature>/TASKS.md
```

## Rules

- Use the smallest workflow that removes ambiguity.
- `.work/` is temporary and ignored by Git.
- Do not duplicate permanent architecture in `.work/`.
- Only update `ARCHITECTURE.md`, `REPOSITORY.md` or `SETUP.md` when a lasting decision changed.
- Delete temporary work artifacts when the feature is complete unless the user explicitly asks to keep them.
- Do not introduce separate subagents solely to implement this workflow; skills are the default mechanism until independent agents show measurable value.
