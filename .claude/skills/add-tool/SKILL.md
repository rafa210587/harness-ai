---
name: add-tool
description: Use whenever adding or materially changing an LLM-visible harness tool.
---

# Add Tool

Follow this order:

1. Read the existing tool base contract and registry.
2. Define the tool's single concrete capability and stable name.
3. Define typed input arguments/schema.
4. Classify risk: `read`, `write`, or `dangerous`.
5. Define timeout and cancellation behavior.
6. Implement the capability without bypassing the Tool Registry.
7. Normalize every outcome into `ToolResult`; preserve useful stderr/error detail.
8. Ensure the tool cannot perform a more dangerous side effect than its declared risk level.
9. Add unit tests for schema, success, failure, and important validation paths.
10. Add an integration test where the dependency can be exercised cheaply and deterministically.
11. Register the tool explicitly.
12. Update docs/config only when user-facing behavior or architecture changed.

Prefer one narrow tool over a large ambiguous `execute_anything` capability. Application-specific mechanics belong in controllers/adapters, not the agent loop.
