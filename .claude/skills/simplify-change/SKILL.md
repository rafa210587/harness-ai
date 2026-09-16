# Simplify Change

Use after a non-trivial implementation and before final review.

## Goal

Remove accidental complexity without changing required behavior.

## Inspect for

- abstractions with only one real use;
- factories/registries/wrappers that add no value;
- duplicate validation or error mapping;
- speculative extension points;
- unused configuration;
- unnecessary dependencies;
- dead code;
- repeated documentation;
- tests coupled to implementation details rather than behavior.

## Workflow

1. Compare the implementation to the current spec and acceptance criteria.
2. Identify code or documentation not required to satisfy them.
3. Simplify only when behavior is preserved.
4. Re-run affected tests/checks.
5. Do not remove deliberate architecture boundaries documented by the project.

## Rules

- Simpler code is preferred, not merely fewer lines.
- Do not collapse useful domain boundaries to reduce file count.
- Do not perform unrelated refactors.
- Do not add a new abstraction as part of a simplification unless it removes more complexity than it adds.
