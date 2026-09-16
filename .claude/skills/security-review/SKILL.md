---
name: security-review
description: Use for shell, filesystem writes/deletes, secrets, network calls, browser side effects, privilege, approvals, plugins, or MCP changes.
---

# Security Review

Inspect the concrete trust boundary introduced or changed.

Review:

- command execution and argument construction;
- filesystem roots, traversal, writes, moves, and deletes;
- secrets/config loading and accidental logging;
- external network destinations;
- authenticated browser profiles and side effects;
- privilege/elevation paths;
- approval bypasses;
- tool risk metadata;
- hooks/policy behavior;
- future plugin/MCP execution boundaries.

Rules:

1. Security enforcement belongs in deterministic runtime policy/hooks, not only prompts or skills.
2. Dangerous actions must be denied or require explicit approval according to configuration.
3. Never log credentials, tokens, cookies, or `.env` contents.
4. Validate paths and commands before execution; preserve useful failure detail without leaking secrets.
5. Prefer allowlisted roots/capabilities to unrestricted machine access.
6. Add tests for the abuse/failure path, not only the happy path.
7. Report any residual risk explicitly.
