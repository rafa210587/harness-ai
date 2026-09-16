---
name: unity-integration
description: Use for Unity CLI, Editor scripts, asset imports, scene operations, console capture, or future editor bridges.
---

# Unity Integration

Priority order:

```text
Unity CLI / Editor API
→ generated Editor scripts
→ persistent localhost bridge
→ GUI automation only as fallback
```

1. Keep Unity-specific mechanics inside `unity/`.
2. Expose stable model-facing capabilities through `tools/unity.py`.
3. Generated C# automation belongs under Editor-only paths and should not leak into normal game runtime code.
4. Treat Unity executable/project paths as configuration.
5. Capture Unity process/log output and return compiler/editor errors to the agent as structured tool failures.
6. Asset refresh/import operations must report concrete results rather than assuming success.
7. Mark tests requiring a real editor with `@pytest.mark.unity`; keep default tests independent of Unity installation.
8. Prefer deterministic Editor APIs over clicks/keystrokes.
9. Do not build a persistent plugin/bridge until command-line and Editor-script integration is demonstrably insufficient.
