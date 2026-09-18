---
name: create-blender-prop
description: Create or revise a game prop in Blender through the configured Blender MCP and validate the resulting artifact.
compatibility: opencode
---

# Create Blender Prop

Use this procedure when the task is to create or revise a game prop in Blender.

## Procedure

1. Choose repository/workspace-relative source, export and render artifact paths before editing.
2. Use Blender MCP capabilities rather than desktop mouse/keyboard automation.
3. Prefer deterministic Blender Python or structured Blender MCP operations that are inspectable and reproducible.
4. Keep source/output files inside the configured workspace unless the user explicitly chose another allowed project path.
5. Preserve the .blend source when the task requires an editable source artifact.
6. Export FBX or glTF only when the task or downstream Unity workflow requires it.
7. Produce a small validation render for geometry/material/framing checks.
8. If vision is available, inspect the render and correct obvious geometry, scale, material, lighting or framing defects before completion.
9. Report source/export/render paths that actually exist.

## Security constraints

- Keep Blender MCP safe mode enabled unless a measured task requires disabling it and the user explicitly approves the additional risk.
- Do not use Blender Python to launch OS processes, install software, access unrelated files or reach the network.
- Do not write outside the intended workspace/project roots.
- Preserve existing assets unless replacement is explicitly requested.

## Completion

The task is complete only when the requested asset exists and its required validation/export artifacts were verified.
