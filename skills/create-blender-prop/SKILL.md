# Create Blender Prop

Use this procedure when the task is to create or revise a game prop in Blender.

## Procedure

1. Identify the requested asset and choose workspace-relative output paths before editing.
2. Prefer `blender_execute_python`; do not use desktop mouse/keyboard automation.
3. Keep generated Blender Python inspectable and deterministic.
4. Keep all source/output files inside the configured workspace.
5. Save a `.blend` source artifact before considering the asset complete.
6. Export FBX or glTF only when the task or downstream Unity workflow requires it.
7. Declare expected output files through `expected_artifacts` so the harness tracks them.
8. Use `blender_render` to create a small validation render.
9. If vision is available, inspect the render and correct material, framing, geometry, scale, or obvious visual defects before finishing.
10. Report the final source, export, and render artifact paths.

## Constraints

- Do not execute operating-system commands from Blender Python; use harness tools for OS work.
- Do not write outside the workspace.
- Do not add unrelated scene content or dependencies.
- Prefer simple geometry/material changes over unnecessary procedural complexity.
- Preserve existing assets unless the task explicitly asks to replace them.

## Completion

The task is complete only when the requested asset exists as a tracked artifact and the validation render or downstream check succeeded.
