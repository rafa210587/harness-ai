# Implement Feature

Use after the required specification workflow is complete.

## Inputs

Read, when present:

```text
.work/<feature>/REFINEMENT.md
.work/<feature>/SPEC.md
.work/<feature>/PLAN.md
.work/<feature>/TASKS.md
```

Also read the relevant code and tests before editing.

## Workflow

1. Implement the smallest vertical slice satisfying the next task.
2. Add or update tests with the behavior.
3. Mark completed items in `TASKS.md` when that file exists.
4. Run the smallest relevant checks after each coherent step.
5. Do not silently change requirements to fit the implementation.
6. If implementation exposes a real spec defect, update the spec explicitly before continuing.
7. When all tasks are complete, run the relevant verification suite.
8. Run `simplify-change` before final review for non-trivial changes.

## Rules

- Follow existing module boundaries.
- No speculative abstractions.
- No unrelated refactors bundled into the feature.
- New dependencies require a concrete need.
- Preserve useful errors instead of hiding failures.
- Do not claim acceptance criteria are met without verification evidence.
- Do not create additional documentation unless a lasting repository decision changed.
