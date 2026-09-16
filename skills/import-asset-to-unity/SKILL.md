# Import Asset To Unity

Use this procedure when an artifact must be imported, configured, or placed in a Unity project.

## Procedure

1. Run `unity_project_info` first and confirm the target path is the intended Unity project.
2. Confirm the source artifact exists inside the configured workspace.
3. Choose the destination under the project's `Assets/` tree explicitly; do not guess a production path when the request is ambiguous.
4. Use filesystem tools for simple file placement inside the workspace.
5. Use `unity_execute_editor_script` only for Editor API work that filesystem operations cannot perform, such as `AssetDatabase.Refresh`, importer configuration, prefab creation, component changes, or scene edits.
6. Keep generated Editor C# narrowly scoped to the requested task.
7. Declare expected output files through `expected_artifacts` when the Editor script creates assets or reports.
8. Inspect Unity output and errors before claiming completion.
9. If a screenshot/vision capability is available, capture and verify the resulting scene or asset when visual correctness matters.
10. Report the Unity project-relative paths that were created or changed.

## Constraints

- Do not alter ProjectSettings, packages, build settings, or unrelated scenes unless explicitly required.
- Do not delete existing assets as cleanup without explicit approval.
- Do not use desktop coordinate automation when the Editor API can perform the action.
- Treat `unity_execute_editor_script` as a dangerous operation that requires the runtime permission path.

## Completion

The task is complete when Unity successfully recognizes the expected asset/change and the relevant artifact or visual verification succeeded.
