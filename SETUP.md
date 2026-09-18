# Setup

Windows is the primary local target. CI also validates the core on Linux and Windows.

## Active OpenCode migration bootstrap

The migration branch uses stable OpenCode `1.18.31` and official Playwright MCP `0.0.81`.

Current migration prerequisites:

```text
Node.js 20+
npm / npx
OpenCode 1.18.31
Python 3.12 + uv
Google Chrome
```

Install the pinned OpenCode version:

```powershell
npm install -g opencode-ai@1.18.31
opencode --version
```

Expected:

```text
1.18.31
```

Validate repository configuration:

```powershell
.\scripts\validate-opencode.ps1
```

The committed `opencode.jsonc` configures official Playwright MCP `@playwright/mcp@0.0.81` with the installed Google Chrome channel.

Provider authentication stays outside Git. For the DeepSeek parity baseline:

```powershell
opencode
```

Then use:

```text
/connect  -> DeepSeek
/models   -> choose the desired DeepSeek model
```

Do not remove custom runtime code until its replacement passes the gates in `OPENCODE_MIGRATION.md`.


## OpenCode migration local gates

After checking out `migration/opencode-core`:

```powershell
git pull
npm install -g opencode-ai@1.18.31
uv python install 3.12
```

Validate repository/config/MCP packages:

```powershell
.\scripts\validate-opencode.ps1
.\scripts\validate-opencode-mcp-candidates.ps1
```

Configure DeepSeek once through OpenCode:

```powershell
opencode auth login
opencode models deepseek --refresh
```

Choose the exact `deepseek/<model-id>` printed by the model list.

Run the provider + synthetic security + browser gates:

```powershell
.\scripts\validate-opencode-local.ps1 -Model "deepseek/<model-id>" -Security -Browser
```

The security gate creates only synthetic temporary secrets, checks direct read/search/shell/outside-root paths, and removes the fixtures afterward. It never uses your real API key as test data.

For the current migration Stage 2 (real DeepSeek + synthetic security + browser), use one command:

```powershell
.\scripts\validate-opencode-stage2.ps1
```

Stage 2 requires DeepSeek to be stored in OpenCode's credential store (`auth.json`); environment-only `DEEPSEEK_API_KEY` is not accepted for cutover. If needed, the script starts `opencode auth login --provider deepseek` interactively. During validation it removes `DEEPSEEK_API_KEY` from the child process environment, runs file/search/shell/environment exfiltration probes, and only writes fresh `deepseek`, `security`, and `browser` evidence markers after the corresponding gates pass.

For Unity, use only the disposable smoke project:

```powershell
.\scripts\prepare-unity-mcp.ps1 -ProjectPath "$env:HARNESS_UNITY_SMOKE_PROJECT"
```

Then open that project in Unity, wait for package resolution/compilation, start/configure MCP for Unity, and run:

```powershell
.\scripts\validate-opencode-unity.ps1 -Model "deepseek/<model-id>"
```

For Blender:

```powershell
.\scripts\prepare-blender-mcp.ps1
```

Then open Blender, enable **Interface: MCP for Blender**, start its MCP server from the Blender sidebar, and run:

```powershell
.\scripts\validate-opencode-blender.ps1 -Model "deepseek/<model-id>"
```

Or after both applications are prepared:

```powershell
.\scripts\validate-opencode-local.ps1 -Model "deepseek/<model-id>" -All
```

The local scripts enable Unity/Blender MCP only for the process through `OPENCODE_CONFIG_CONTENT`; they do not rewrite the committed project config.

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
Google Chrome installed locally (default browser runtime)
Blender
Unity Editor
```

The harness can still use Playwright-managed Chromium when explicitly configured, but local Windows validation defaults to the installed Google Chrome and therefore does not require a Playwright browser download.

The harness does not require Docker, Redis, PostgreSQL, Kubernetes, Node.js, LangGraph, or Temporal.

## 1. Clone and install

```powershell
git clone https://github.com/rafa210587/harness-ai.git
cd harness-ai

uv python install 3.12
uv sync --all-groups
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
HARNESS_BROWSER_CHANNEL=chrome

BLENDER_PATH=
UNITY_PATH=

# Optional override. If omitted, validate-local.ps1 creates data/unity-smoke-project.
HARNESS_UNITY_SMOKE_PROJECT=
```

`.env` is local-only and must never be committed.

`HARNESS_BROWSER_CHANNEL=chrome` tells Playwright to launch the Google Chrome installed on the machine. The harness always uses its own profile directory; do not point `HARNESS_BROWSER_PROFILE` at your personal Chrome profile.

To opt back into Playwright-managed Chromium instead:

```dotenv
HARNESS_BROWSER_CHANNEL=playwright
```

and install its browser binary once:

```powershell
uv run playwright install chromium
```

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

The browser runtime smoke uses the installed Google Chrome by default and does not require internet access:

```powershell
uv run pytest -m browser_runtime
```

Expected result is one passing browser-runtime test that launches Chrome headlessly, reads a local `data:` page, and writes a screenshot.

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

Set only the Unity executable for the normal local acceptance flow:

```dotenv
UNITY_PATH=C:\path\to\Unity.exe
```

Then run:

```powershell
.\scripts\validate-local.ps1 -Unity
```

If `HARNESS_UNITY_SMOKE_PROJECT` is not configured, the script creates a disposable project at:

```text
data/unity-smoke-project
```

The directory is reused on later runs. If that path already exists but is not a valid Unity project, validation stops instead of deleting or overwriting it.

You can still override the smoke project explicitly:

```dotenv
HARNESS_UNITY_SMOKE_PROJECT=C:\path\to\disposable-unity-project
```

The project must be disposable: the smoke test is allowed to generate Editor code in it. Do not point the override at an important working project.

To run only the Unity pytest directly, `HARNESS_UNITY_SMOKE_PROJECT` must already point to a valid project:

```powershell
uv run pytest -m unity
```

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

The script deliberately keeps `.env` out of the deterministic core test process, then loads it only for requested capability gates that need real local credentials or application paths. It runs `uv sync`, quality checks, core tests, `uv build`, doctor, and the requested real integration gates. For `-Unity`, it also creates/reuses the dedicated disposable smoke project when no override is configured.

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

Blender -> Unity Level 6A acceptance (real DeepSeek + real applications):

```powershell
.\scripts\validate-level6a.ps1
```

This creates/reuses `workspace/unity-level6`, runs `evals/blender-unity-smoke.yaml`, and verifies the generated `.blend`, `.fbx`, imported Unity FBX, and saved Unity scene. The command writes its eval report to `data/blender-unity-smoke-report.json`. Blender and Unity scripting are explicitly auto-allowed by `config/permissions.yaml`; `shell_run`, `browser_click`, and the global `dangerous` default remain approval-gated.

Dangerous tools still require runtime approval unless the permission policy explicitly says otherwise.

Full local acceptance package:

```powershell
.\scripts\validate-full-local.ps1
```

This is the longest supported local gate. It runs the deterministic/core suite, real DeepSeek smoke scenarios, installed-Chrome runtime smoke, real Blender, real Unity, Level 6A Blender -> Unity, and an additional reliability suite covering bounded error recovery, mutation of an existing Blender artifact, idempotent Unity scene editing, runtime skills, artifact inspection, and forced real context compaction. It writes the consolidated report to `data/full-local-acceptance-report.json`.

A green full-local report proves the currently implemented Level 5 gates plus Level 6A and reliability/recovery behavior. It does **not** prove Level 6B visual correctness because no concrete real `VisionProvider` is wired into the default runtime yet.

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
local Google Chrome runtime behavior
local Blender installation behavior
local Unity installation/project behavior
visual quality of generated assets
complete Blender -> vision -> Unity workflows
```

Track current evidence in `IMPLEMENTATION_STATUS.md` and durable phase criteria in `EXECUTION_PLAN.md`.
