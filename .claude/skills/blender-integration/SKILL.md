---
name: blender-integration
description: Use for Blender automation, Python scripts, CLI/background execution, rendering, exports, or future Blender bridges.
---

# Blender Integration

Priority order:

```text
Blender Python API
→ Blender CLI/background mode
→ persistent local bridge/addon
→ GUI automation only as fallback
```

1. Keep Blender-specific process/script logic inside `blender/`.
2. Expose stable model-facing capabilities through `tools/blender.py`.
3. Generated Python scripts must be inspectable and saved as artifacts/workspace files when useful.
4. Do not install Blender-internal Python dependencies into the harness virtual environment.
5. Treat Blender executable paths as configuration, never assumptions.
6. Capture stdout/stderr and process exit codes.
7. For renders/exports, return artifact metadata and concrete output paths.
8. Add pure unit tests around command/script construction and mark tests requiring Blender with `@pytest.mark.blender`.
9. Do not build a persistent addon/bridge until CLI/background mode is measurably limiting.
