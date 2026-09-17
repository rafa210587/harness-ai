# Setup

Windows is the primary local target. CI also validates the core on Linux and Windows.

## Requirements

Required:

```text
Git
uv
Python 3.12 (managed by uv)
DeepSeek API key for real-agent runs
```

Capability-specific:

```text
Chromium via Playwright
Blender
Unity Editor
```

The harness does not require Docker, Redis, PostgreSQL, Kubernetes, Node.js, LangGraph, or Temporal.

## 1. Clone and install

```powershell
git clone https://github.com/rafa210587/harness-ai.git
cd harness-ai

uv python install 3.12
uv sync --all-groups
uv run playwright install chromium
```

`uv.lock` is committed. Do not edit it manually.

If `uv` is not installed:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. Configure local environment

```powershell
Copy-Item .env.example .env
```

Fill the values you intend to validate:

```dotenv
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash

HARNESS_DATA_DIR=./data
HARNESS_WORKSPACE=./workspace
HARNESS_BROWSER_PROFILE=./data/browser-profile
HARNESS_BROWSER_HEADLESS=false

BLENDER_PATH=
UNITY_PATH=

# Use a disposable Unity project for integration tests.
HARNESS_UNITY_SMOKE_PROJECT=
```

`.env` is local-only and must never be committed.

The runtime blocks direct filesystem access to common secret files such as `.env`, private keys, credential files, and credential directories. Known configured secrets are also redacted from ToolResults before they reach the model or persistence.

## 3. Basic validation

```powershell
uv run harness version
uv run harness doctor
```

Quality and packaging gate:

```powershell
uv run ruff format --check src tests .claude/hooks
uv run ruff check src tests .claude/hooks
uv run mypy src
uv run pytest -m "not blender and not unity and not browser_runtime and not browser_external"
uv build
```

## 4. Online DeepSeek validation

Requires `DEEPSEEK_API_KEY`:

```powershell
uv run harness doctor --online
uv run harness eval evals/smoke.yaml --json-out data/smoke-report.json
```

The smoke suite requires actual tool use, including filesystem operations and loading a runtime skill. It is not satisfied by a text-only answer.

## 5. Browser validation

Chromium runtime smoke does not require internet access:

```powershell
uv run pytest -m browser_runtime
```

Tests that use real external websites remain separately marked:

```powershell
uv run pytest -m browser_external
```

Run those only when the test explicitly requires external web access.

## 6. Blender validation

Set:

```dotenv
BLENDER_PATH=C:\path\to\blender.exe
```

Then:

```powershell
uv run pytest -m blender
```

The Blender smoke test launches Blender in background mode and validates real generated artifacts rather than only mocking the process runner.

## 7. Unity validation

Set:

```dotenv
UNITY_PATH=C:\path\to\Unity.exe
HARNESS_UNITY_SMOKE_PROJECT=C:\path\to\disposable-unity-project
```

The project must be disposable: the harness smoke test is allowed to generate Editor code in it.

Then:

```powershell
uv run pytest -m unity
```

Do not point `HARNESS_UNITY_SMOKE_PROJECT` at an important working project for the first validation.

## 8. One-command Windows acceptance

Core only:

```powershell
.\scripts\validate-local.ps1
```

Core + DeepSeek:

```powershell
.\scripts\validate-local.ps1 -Online
```

Core + selected application gates:

```powershell
.\scripts\validate-local.ps1 -Browser -Blender
```

Everything configured:

```powershell
.\scripts\validate-local.ps1 -All
```

The script deliberately keeps `.env` out of the deterministic core test process, then loads it only for requested capability gates that need real local credentials or application paths. It runs `uv sync`, quality checks, core tests, `uv build`, doctor, and the requested real integration gates.

## 9. Useful CLI commands

```powershell
uv run harness tools
uv run harness run "<task>"
uv run harness sessions
uv run harness session show <session-id>
uv run harness session events <session-id>
uv run harness session artifacts <session-id>
uv run harness resume <session-id>
uv run harness eval evals/smoke.yaml
```

Dangerous tools still require runtime approval unless the permission policy explicitly says otherwise.

## 10. Development checks

Before considering a substantial repository change complete:

```powershell
uv run ruff format --check src tests .claude/hooks
uv run ruff check src tests .claude/hooks
uv run mypy src
uv run pytest -m "not blender and not unity and not browser_runtime and not browser_external"
uv build
```

GitHub Actions runs the quality suite and distribution build on Linux and the core acceptance plus distribution build on Windows. Application-specific Blender, Unity, browser-runtime, and external-web gates are intentionally opt-in.

## 11. What remains a real-machine gate

CI does not prove:

```text
real DeepSeek account access/billing
local authenticated browser profiles
local Blender installation behavior
local Unity installation/project behavior
visual quality of generated assets
complete Blender -> vision -> Unity workflows
```

Track current evidence in `IMPLEMENTATION_STATUS.md` and durable phase criteria in `EXECUTION_PLAN.md`.
