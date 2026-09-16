# Spec Feature

Use for medium and large changes after refinement.

## Goal

Define observable behavior and acceptance criteria before implementation.

## Output

Write `.work/<feature>/SPEC.md` using only the sections that add implementation value:

```md
# Feature

## Goal
One concrete outcome.

## Requirements
- R1
- R2

## Non-goals
- Explicit exclusions.

## Behavior
Inputs, outputs, important flows and failure behavior.

## Constraints
Architecture, compatibility, security or performance constraints that matter.

## Acceptance criteria
- [ ] Verifiable outcome 1
- [ ] Verifiable outcome 2
```

## Rules

- Describe required behavior before implementation details.
- Acceptance criteria must be testable or directly inspectable.
- Do not restate `ARCHITECTURE.md` or `REPOSITORY.md`.
- Do not add background/history unless it changes the solution.
- Do not invent requirements for hypothetical future users.
- Prefer one page or less for normal medium changes.
- If sequencing is obvious, skip a separate `PLAN.md` and go directly to `TASKS.md`.
