# SETUP.md

> Development environment setup for the Local AI Harness.
>
> Initial supported development target: Windows host, Python 3.12, `uv`, Git, Chromium via Playwright, Blender and Unity.

## 1. What will be installed

Required for the core harness:

```text
Git
uv
Python 3.12 (managed by uv)
project Python dependencies
Playwright
Chromium
DeepSeek API key
```

Required when working on the corresponding integrations:

```text
Blender
Unity Hub + Unity Editor
```

Optional:

```text
WSL
Claude Code
Cursor
Codex
```

The harness itself must not require Node.js, Docker, Kubernetes, Redis or PostgreSQL.

---

## 2. Why Python

Use Python 3.12 for the harness.

Reasons:

- Blender has first-class Python scripting.
- Playwright has an async Python API.
- subprocess/process control is straightforward.
- the AI ecosystem is mature.
- SQLite support is native and simple.
- the MVP needs orchestration more than raw runtime performance.

Pin the project to the Python 3.12 line initially so contributors do not debug unnecessary version differences.

`.python-version`:

```text
3.12
```

`pyproject.toml`:

```toml
[project]
requires-python = ">=3.12,<3.13"
```

We can widen this after CI verifies later Python versions.

---

## 3. Install Git

Install Git for Windows from:

```text
https://git-scm.com/download/win
```

Verify:

```powershell
git --version
```

Configure identity if necessary:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## 4. Install uv

`uv` is the project/package/Python environment manager.

Official Windows installation:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Open a new terminal if required.

Verify:

```powershell
uv --version
```

The repository should use `uv.lock` as the reproducible dependency lockfile.

Official reference:

```text
https://docs.astral.sh/uv/
https://docs.astral.sh/uv/getting-started/installation/
```

---

## 5. Install Python 3.12 with uv

```powershell
uv python install 3.12
```

Verify:

```powershell
uv python list
```

When the repository contains `.python-version`, `uv` will use the requested version for the project.

There is no need to create a virtual environment manually. `uv sync` creates/manages `.venv` for the project.

---

## 6. Clone and initialize the repository

```powershell
git clone <REPOSITORY_URL>
cd local-ai-harness
```

Install the locked project environment:

```powershell
uv sync
```

For every dependency group:

```powershell
uv sync --all-groups
```

Normally the `dev` dependency group is installed by default by `uv`.

Verify Python:

```powershell
uv run python --version
```

Expected:

```text
Python 3.12.x
```

---

## 7. Runtime Python dependencies

The MVP dependency set should remain small.

### `openai`

Purpose:

```text
DeepSeek API client for the MVP
```

DeepSeek currently exposes an OpenAI-compatible API and supports the Responses API/tool calling.

Install:

```powershell
uv add openai
```

### `pydantic`

Purpose:

```text
typed configuration
tool arguments
normalized responses
events
session models
```

Install:

```powershell
uv add pydantic
```

### `pydantic-settings`

Purpose:

```text
environment variable and application configuration loading
```

Install:

```powershell
uv add pydantic-settings
```

### `PyYAML`

Purpose:

```text
harness.yaml
models.yaml
permissions.yaml
```

Install:

```powershell
uv add pyyaml
```

### `typer`

Purpose:

```text
CLI commands
```

Install:

```powershell
uv add typer
```

### `rich`

Purpose:

```text
human-readable CLI output
status
tables
errors
tool events
```

Install:

```powershell
uv add rich
```

### `aiosqlite`

Purpose:

```text
async SQLite persistence
```

Install:

```powershell
uv add aiosqlite
```

### `playwright`

Purpose:

```text
browser automation
```

Install:

```powershell
uv add playwright
```

### `httpx`

Purpose:

```text
small direct HTTP integrations
future localhost Unity/Blender bridges
provider-independent HTTP work
```

Install:

```powershell
uv add httpx
```

### Optional: `Pillow`

Do not add it until screenshots/images require local inspection/manipulation.

```powershell
uv add pillow
```

---

## 8. Install all initial runtime dependencies at once

When bootstrapping the repository:

```powershell
uv add openai pydantic pydantic-settings pyyaml typer rich aiosqlite playwright httpx
```

Do not add Pillow yet unless the first image-processing code requires it.

---

## 9. Development dependencies

Install:

```powershell
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy pre-commit
```

Roles:

| Package | Purpose |
|---|---|
| `pytest` | test runner |
| `pytest-asyncio` | async tests |
| `pytest-cov` | coverage |
| `ruff` | formatter + linter |
| `mypy` | static type checking |
| `pre-commit` | local Git checks |

We should not add Black, Flake8 or isort because Ruff replaces those roles for this project.

---

## 10. Playwright browser installation

Installing the Python package does not install browser binaries.

Install Chromium:

```powershell
uv run playwright install chromium
```

Verify with a future harness doctor command:

```powershell
uv run harness doctor browser
```

Until that command exists, a minimal manual test can launch Chromium from a small Playwright script.

Official reference:

```text
https://playwright.dev/python/docs/intro
```

Current Playwright documentation lists Windows 11+ among supported Windows environments.

---

## 11. DeepSeek configuration

Create a DeepSeek API key in the DeepSeek platform.

Do not put the key in committed configuration.

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

`.env.example`:

```dotenv
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash

HARNESS_DATA_DIR=./data
HARNESS_WORKSPACE=./workspace
```

The current official DeepSeek OpenAI-compatible base URL is:

```text
https://api.deepseek.com
```

The current Flash API model identifier is:

```text
deepseek-flash
```

It maps to the current DeepSeek V4.1 Flash service.

Official references:

```text
https://api-docs.deepseek.com/
https://api-docs.deepseek.com/guides/responses_api/
```

---

## 12. Minimal DeepSeek connectivity test

Once the provider exists, use the harness.

Before it exists, this temporary test validates credentials:

```python
import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)

response = client.responses.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
    input="Reply with exactly: OK",
)

print(response.output_text)
```

Run:

```powershell
uv run python scripts/test_deepseek.py
```

Delete the temporary script once `harness doctor` contains the same check.

---

## 13. Blender

Blender is not a Python package dependency of the harness.

Install Blender normally:

```text
https://www.blender.org/download/
```

The first integration uses Blender's executable in background mode.

Example:

```powershell
"C:\Program Files\Blender Foundation\Blender <version>\blender.exe" --background --python script.py
```

Configure:

```dotenv
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender <version>\blender.exe
```

Do not install Blender's internal Python packages into the harness `.venv`.

Blender Python scripts run inside Blender's own Python runtime.

Validation target:

```powershell
uv run harness doctor blender
```

Expected future check:

1. resolve executable;
2. run `blender --version`;
3. execute a tiny background script;
4. exit successfully.

---

## 14. Unity

Unity is also not a Python package dependency.

Install:

```text
Unity Hub
Unity Editor version used by the target project
```

The first integration should call the Unity executable and generate Editor scripts instead of automating the desktop UI.

Example configuration:

```dotenv
UNITY_PATH=C:\Program Files\Unity\Hub\Editor\<version>\Editor\Unity.exe
```

Validation target:

```powershell
uv run harness doctor unity
```

The doctor should initially validate only:

```text
executable exists
version can be read
configured project path is valid
```

Do not build a persistent Unity plugin before the CLI/editor-script path proves insufficient.

---

## 15. Environment file

Suggested `.env.example`:

```dotenv
# LLM
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash

# Runtime
HARNESS_DATA_DIR=./data
HARNESS_WORKSPACE=./workspace
HARNESS_LOG_LEVEL=INFO

# Browser
HARNESS_BROWSER_PROFILE=./data/browser-profile
HARNESS_BROWSER_HEADLESS=false

# Applications
BLENDER_PATH=
UNITY_PATH=
```

`.env` must be ignored by Git.

`.gitignore` must include:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

data/*
!data/.gitkeep

workspace/*
!workspace/.gitkeep

playwright-report/
test-results/
```

---

## 16. Initial `pyproject.toml`

Recommended starting point:

```toml
[project]
name = "local-ai-harness"
version = "0.1.0"
description = "Local AI harness for tool-driven computer workflows."
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
    "aiosqlite",
    "httpx",
    "openai",
    "playwright",
    "pydantic",
    "pydantic-settings",
    "pyyaml",
    "rich",
    "typer",
]

[project.scripts]
harness = "harness.cli:app"

[dependency-groups]
dev = [
    "mypy",
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "blender: requires a local Blender installation",
    "unity: requires a local Unity installation",
    "browser_external: uses external web resources",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",
    "F",
    "I",
    "UP",
    "B",
    "SIM",
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true
```

Let `uv` write exact resolved package versions into `uv.lock`.

Do not manually pin every package in `pyproject.toml` unless compatibility requires it.

---

## 17. Formatting and linting

Format:

```powershell
uv run ruff format .
```

Check formatting:

```powershell
uv run ruff format --check .
```

Lint:

```powershell
uv run ruff check .
```

Safe autofixes:

```powershell
uv run ruff check --fix .
```

Official reference:

```text
https://docs.astral.sh/ruff/
```

---

## 18. Type checking

```powershell
uv run mypy src
```

`mypy strict` can initially expose too many issues while scaffolding.

If necessary, enable strict mode incrementally by module, but new core contracts should be fully typed from day one.

---

## 19. Tests

Run fast default tests:

```powershell
uv run pytest
```

With coverage:

```powershell
uv run pytest --cov=src/harness --cov-report=term-missing
```

Skip application-dependent tests:

```powershell
uv run pytest -m "not blender and not unity and not browser_external"
```

Run Blender tests explicitly:

```powershell
uv run pytest -m blender
```

Run Unity tests explicitly:

```powershell
uv run pytest -m unity
```

---

## 20. Pre-commit

After `.pre-commit-config.yaml` is added:

```powershell
uv run pre-commit install
```

Run manually:

```powershell
uv run pre-commit run --all-files
```

The pre-commit path should remain fast.

Recommended checks:

```text
Ruff formatting
Ruff lint
basic YAML/TOML validation
trailing whitespace/end-of-file checks
```

Do not run Unity or Blender through pre-commit.

---

## 21. Suggested first `.pre-commit-config.yaml`

Use current revisions when the file is created rather than copying stale version numbers from documentation.

Conceptually:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: <current-version>
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: <current-version>
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

Commit the selected hook revisions.

---

## 22. Optional coding-agent tooling

These are development tools, not harness runtime dependencies.

### Claude Code

Project-specific reusable skills live under:

```text
.claude/skills/<skill-name>/SKILL.md
```

Hooks can intercept events such as tool execution and stopping.

### Cursor

Cursor project rules live under:

```text
.cursor/rules/
```

Cursor also supports a root `AGENTS.md`, which is enough for our initial cross-agent instructions.

### Codex

Use the root `AGENTS.md` as the repository-level instruction source.

Do not duplicate the full architecture into tool-specific rule files.

---

## 23. Bootstrap sequence for a fresh machine

After Git and `uv` are installed:

```powershell
git clone <REPOSITORY_URL>
cd local-ai-harness

uv python install 3.12
uv sync
uv run playwright install chromium

Copy-Item .env.example .env
```

Fill:

```text
DEEPSEEK_API_KEY
BLENDER_PATH
UNITY_PATH
```

Then:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run harness doctor
```

Once all checks pass, the machine is ready.

---

## 24. What `harness doctor` must eventually check

```text
[core]
✓ Python 3.12
✓ writable workspace
✓ writable data directory
✓ SQLite
✓ configuration parses

[deepseek]
✓ API key exists
✓ API reachable
✓ configured model responds

[browser]
✓ Playwright installed
✓ Chromium installed
✓ browser can launch

[blender]
✓ configured executable exists
✓ Blender launches in background mode

[unity]
✓ configured executable exists

[git]
✓ git executable available
```

The doctor command is one of the first bootstrap features we should build because it eliminates environment ambiguity.

---

## 25. CI later

Do not block the first commit on Blender or Unity being installed in CI.

Initial CI:

```text
uv sync --frozen
ruff format --check .
ruff check .
mypy src
pytest -m "not blender and not unity and not browser_external"
```

External-application integration testing can be added separately once those integrations exist.

---

## 26. Setup principles

1. One Python environment.
2. One lockfile.
3. No global project Python dependencies.
4. No Docker for the MVP.
5. No Node.js runtime dependency unless a concrete integration requires it.
6. Application integrations use installed desktop applications, not copied runtimes.
7. Secrets stay outside Git.
8. `harness doctor` becomes the canonical environment verification.
