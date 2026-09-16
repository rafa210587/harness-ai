# Review Change

Use after implementation and simplification of a non-trivial change.

## Role

Act as an independent reviewer. Do not modify code while reviewing.

## Review against

1. `SPEC.md` acceptance criteria when present.
2. Repository architecture and module boundaries.
3. Correctness and failure behavior.
4. Security and permission boundaries.
5. Test quality and missing coverage.
6. Unnecessary complexity or dependency growth.
7. Documentation drift or duplication.

## Findings

Report only actionable findings:

```text
P0 - blocking correctness/security/data-loss issue
P1 - important defect or requirement mismatch
P2 - worthwhile improvement that is not blocking
```

Each finding must contain:

```text
severity
file/location
problem
evidence/impact
required correction
```

## Rules

- Do not praise or summarize unchanged code.
- Do not invent style findings without repository support.
- Do not rewrite code during the review pass.
- Prefer evidence from code/tests over hypothetical concerns.
- If there are no findings, say so explicitly.
- After findings are produced, implementation work may resume to address them, followed by targeted re-review.
