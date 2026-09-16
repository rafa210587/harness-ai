---
name: architecture-change
description: Use when changing module boundaries, runtime flow, persistence, security, provider/tool contracts, hooks, approvals, or other architectural decisions.
---

# Architecture Change

1. Read `ARCHITECTURE.md`, `REPOSITORY.md`, and the affected implementation/tests before editing.
2. State which current ADR/module boundary the change touches.
3. Prefer the smallest change compatible with the existing architecture.
4. Do not introduce LangChain, LangGraph, Temporal, Redis, PostgreSQL, vector databases, Kubernetes, multi-agent orchestration, or equivalent infrastructure unless the current design cannot satisfy a concrete requirement.
5. Keep provider-specific behavior behind `llm/`, tool contracts behind `tools/`, and application mechanics inside their adapters.
6. Preserve deterministic permission/approval enforcement outside prompts.
7. Add or update focused tests.
8. Update `ARCHITECTURE.md` only when the architectural decision itself changes; update `REPOSITORY.md` when repository boundaries/conventions change.
9. Run the smallest relevant verification set, then the normal fast suite before completion.

Do not create speculative abstractions for hypothetical future requirements.
