---
name: import-asset-to-unity
description: Import, configure or place an existing artifact in the connected disposable/target Unity project through Unity MCP.
compatibility: opencode
---

# Import Asset To Unity

Use this procedure when an artifact must be imported, configured or placed in a Unity project.

## Procedure

1. Inspect the connected Unity project and confirm it is the intended target before mutating anything.
2. Confirm the source artifact exists at the expected workspace/project path.
3. Choose the destination under the project's Assets tree explicitly.
4. Use Unity MCP asset/editor capabilities rather than desktop coordinate automation.
5. Use script/code editing only when the Unity Editor API or structured Unity MCP operations cannot express the required change.
6. Keep generated editor-side code narrowly scoped to the task.
7. Refresh/import assets and inspect compile/console errors before claiming success.
8. When visual correctness matters, capture the resulting scene/game view and verify it.
9. Report project-relative paths and scene/object changes that actually occurred.

## Security constraints

- Do not modify packages, ProjectSettings, build settings or unrelated scenes unless explicitly required.
- Do not delete existing assets as cleanup without explicit approval.
- Operate only on the intended project; first migration tests must use the disposable smoke project.
- Prefer reversible bounded changes.

## Completion

The task is complete when Unity recognizes the expected asset/change and the relevant compile, artifact or visual verification succeeded.
