# Refine Feature

Use before writing a spec for medium or large changes.

## Goal

Turn an ambiguous request into an implementation-ready scope without inventing unnecessary architecture.

## Output

For large changes write `.work/<feature>/REFINEMENT.md`. For medium changes, the refined result may be folded directly into `SPEC.md`.

Use this shape:

```md
# Refinement

## Need
What must become possible?

## Existing constraints
Facts already fixed by repository architecture or current code.

## Scope
What this change will implement.

## Out of scope
What this change will intentionally not implement.

## Decisions resolved
Ambiguities that can be resolved from current repository context.

## Open blockers
Only unresolved questions that truly prevent a correct implementation.
```

## Rules

- Inspect current code and relevant architecture before refining.
- Resolve questions from existing context instead of asking them again.
- Do not create speculative future requirements.
- Separate requirements from implementation choices.
- Keep the refinement short enough to scan in under two minutes.
- If there are no real blockers, proceed to the spec instead of asking for confirmation.
