# Concise Documentation

Use whenever creating or updating project documentation.

## Goal

Keep documentation minimal, durable and implementation-relevant.

## Rules

- Prefer bullets, tables and short sections over narrative prose.
- Do not repeat context already defined in another source-of-truth document.
- Do not create a document unless it will remain useful after the current task is complete.
- Temporary reasoning, plans and task lists belong under `.work/`, not permanent docs.
- One decision should have one authoritative location.
- Do not add Overview, Background, Summary or Conclusion sections unless they add unique information.
- Examples must remove ambiguity; otherwise omit them.
- Document behavior, contracts, constraints and decisions, not the story of how work was performed.
- Remove stale text when a decision changes instead of appending contradictory history.
- Prefer links/references to duplication.

## Permanent document ownership

```text
ARCHITECTURE.md  architecture and lasting technical decisions
REPOSITORY.md    repository structure, boundaries and engineering workflow
SETUP.md         environment, dependencies and machine setup
AGENTS.md        short mandatory instructions for coding agents
SKILLS_HOOKS.md  skill/hook model and catalog
```

Before adding text, ask: `Will an engineer need this after the feature is finished?`

If not, keep it in `.work/` or do not write it.
