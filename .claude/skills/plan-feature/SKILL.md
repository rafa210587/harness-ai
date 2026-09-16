# Plan Feature

Use after `SPEC.md` for medium/large changes when work needs to be decomposed.

## Outputs

For large changes create:

```text
.work/<feature>/PLAN.md
.work/<feature>/TASKS.md
```

For medium changes, create `TASKS.md`; create `PLAN.md` only when ordering or migration risk is not obvious.

## PLAN.md

Keep it implementation-oriented:

```md
# Plan

1. Change contract/configuration needed for the behavior.
2. Implement the smallest vertical slice.
3. Integrate it into the runtime.
4. Add/adjust tests.
5. Verify acceptance criteria.
```

Do not repeat requirements already in `SPEC.md`.

## TASKS.md

Tasks must be independently executable and verifiable:

```md
# Tasks

- [ ] T1 Concrete implementation task
- [ ] T2 Concrete test/integration task
- [ ] T3 Verification task
```

## Rules

- Each task should produce a concrete repository change or verification result.
- Order tasks by dependency.
- Prefer vertical slices over creating every abstraction first.
- Do not create tasks for documentation unless a permanent document actually changes.
- Do not create future-phase tasks outside the current spec.
- Keep task count small; split only when the implementation would otherwise be ambiguous.
