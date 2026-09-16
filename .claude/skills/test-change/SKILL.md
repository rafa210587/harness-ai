---
name: test-change
description: Use before declaring a meaningful code change complete to choose and run the correct verification scope.
---

# Test Change

1. Identify the behavior that changed and the smallest tests that prove it.
2. Run focused unit/contract tests first.
3. Run integration tests when the changed boundary actually depends on SQLite, subprocesses, Playwright, or another local component.
4. Do not run Blender/Unity/external-browser suites unless relevant and the environment supports them.
5. Before completing a substantial change, run:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -m "not blender and not unity and not browser_external"
```

6. Do not weaken assertions, delete tests, or change expected behavior merely to obtain green output.
7. If a required test cannot be executed, state exactly what was not tested and why.
8. Never claim an external application workflow works unless it was actually exercised.
