# Implementation Status

> Factual snapshot of what exists in code, what CI has proved, and what still requires Rafael's local Windows machine.
>
> `EXECUTION_PLAN.md` remains the durable roadmap. This file tracks current evidence so roadmap intent is not confused with completed validation.

## Status meanings

- **Implemented** — code and automated tests exist.
- **CI validated** — automated GitHub Actions checks have exercised the implementation without external credentials/apps.
- **Local gate pending** — requires the real Windows host, credentials, login, Blender, Unity, Chromium, or visual acceptance.
- **Not started** — intentionally not implemented yet.

## Current phase status

| Phase | Capability | Code | Automated evidence | Local / real-world gate |
|---|---|---|---|---|
| 0 | Repository + engineering workflow | Implemented | Linux + Windows CI active and green | None |
| 1 | Local development environment | Repo side implemented | `uv sync`, package install, CLI entrypoint and distribution build pass on Windows CI | Clone/sync on Rafael's Windows machine; local `.env`; local apps |
| 2 | Typed config + doctor | Implemented | Unit tests; offline + online diagnostic code tested with fakes | `harness doctor --online` on Rafael's Windows machine |
| 3 | LLM contract + DeepSeek | Implemented | Provider mapping/tool-call/usage/error + bounded retry tests | Real DeepSeek key + live request |
| 4 | Tool registry + filesystem + shell | Implemented | Linux + Windows core tests; global timeout; workspace/symlink boundaries; sensitive-path and secret-redaction tests | Real local smoke tasks |
| 5 | Agent loop | Implemented | Fake-provider end-to-end tests, limits, cancellation, stable runtime system instruction | Real DeepSeek → tool → result → DeepSeek run |
| 6 | Sessions + persistence + artifacts | Implemented | SQLite integration tests, resume, schema guard, indexes, foreign keys | Process restart/resume on Rafael's machine |
| 7 | Permissions + approvals + runtime hooks | Implemented | Deterministic permission/approval + tool-risk invariant tests | Manual approval UX validation |
| 8 | Observability | Implemented | Persisted events, timing, token usage, CLI inspection; known secrets redacted at tool boundary | Inspect one real success and failure run |
| 9 | Browser / Playwright | Implemented | Controller/tool tests; real-runtime smoke test exists but is excluded from fast CI | `pytest -m browser_runtime` after Playwright Chromium install |
| 10 | Interactive ChatGPT browser workflow | Not started | — | Requires authenticated browser profile and explicitly interactive/human-controlled flow |
| 11 | Screenshot + vision abstraction | Implemented / partial | Screenshot artifacts, `VisionProvider`, `vision_inspect`, visual verifier tests | Choose/inject a real vision provider |
| 12 | Blender | Implemented / partial | CLI/controller/tool tests with fakes; real Blender smoke test exists | `pytest -m blender` with real `BLENDER_PATH` |
| 13 | Unity | Implemented / partial | CLI/controller/editor-script tests with fakes; real Unity smoke test exists | `pytest -m unity` with real `UNITY_PATH` + disposable smoke project |
| 14 | Generic image providers | Abstraction implemented | `ImageProvider` + `image_generate` tool tests | Add at least one concrete provider if autonomous image generation is in v1 scope |
| 15 | Verification / self-correction | Implemented | Generic verifier + visual verifier retry tests | Real image/vision correction loop |
| 16 | Context management | Implemented | Compaction tests incl. tool-call boundary safety | Evaluate long real sessions |
| 17 | Runtime skills | Implemented | Bounded loader tests; real Blender/Unity/browser skills; smoke eval requires `skill_list` + `skill_load` | Run real DeepSeek smoke eval |
| 18 | Desktop/computer-control fallback | Not started | — | Decide only after CLI/API/browser gaps are proven |
| 19 | Reliability / evals | Implemented / partial | YAML eval runner, required tools, token/step/error metrics, smoke suite | Run `evals/smoke.yaml` against real DeepSeek |
| 20 | Packaging + bootstrap | Repo side implemented | `uv build` and core acceptance pass on Linux and Windows GitHub runners; local acceptance script includes the distribution build | Clean-clone / real-host acceptance on Rafael's Windows machine |
| 21 | v1 end-to-end acceptance | Not started | Core prerequisites are implemented through CI Level 4 | Level 5 real host/app gates, then Level 6 cross-application workflows |

## Core already implemented

```text
typed YAML/.env configuration
DeepSeek provider abstraction
provider-neutral LLM timeout/retry
normalized token usage
stable agent system instruction against prompt injection from tool/web/file content
Tool + ToolResult + ToolRegistry
global tool timeout
known-secret redaction before tool results reach model/storage
sensitive filesystem path protection
filesystem tools
shell tool
runtime permission hooks
human approvals + persisted resume
single-agent tool loop
SQLite sessions/messages/tool calls/events/approvals/artifacts
SQLite schema version guard + indexes + foreign key enforcement
structured observability
Playwright browser tools
Blender CLI/Python tools
Unity CLI/Editor-script tools
ImageProvider abstraction
VisionProvider abstraction
verification/self-correction loop
visual artifact verifier
context compaction
runtime skill loader
runtime skills: create-blender-prop, import-asset-to-unity, browser-research
YAML eval runner
smoke eval suite requiring real tool + skill use
resource cleanup + cancelled session state
Linux quality CI + Windows core/package CI
explicit real-runtime smoke tests for Chromium, Blender and Unity
Windows local acceptance PowerShell script with distribution build gate
```

## Evidence levels

```text
Level 1: unit/contract behavior
Level 2: integration with deterministic local components/fakes
Level 3: GitHub CI on Linux
Level 4: GitHub CI on Windows
Level 5: real DeepSeek / Chromium / Blender / Unity on Rafael's host
Level 6: complete cross-application workflow with visual verification
```

The core, including the Python distribution build, is validated through Level 4. Levels 5–6 are the next meaningful gates.

## Known cleanup that should wait for local dependency resolution

- `httpx` is still declared directly but has no current direct import. Remove it during the next intentional `uv` dependency update if no concrete localhost bridge needs it; regenerate `uv.lock` with `uv`, never by hand.

## Next Rafael gate

On the target Windows machine:

```powershell
git pull
uv python install 3.12
uv sync --all-groups
uv run playwright install chromium
Copy-Item .env.example .env
```

Fill the capabilities you intend to test:

```dotenv
DEEPSEEK_API_KEY=...
BLENDER_PATH=...
UNITY_PATH=...
HARNESS_UNITY_SMOKE_PROJECT=C:\path\to\DisposableUnitySmokeProject
```

Run core-only acceptance first:

```powershell
.\scripts\validate-local.ps1
```

Then DeepSeek:

```powershell
.\scripts\validate-local.ps1 -Online
```

Then the real application bridges:

```powershell
.\scripts\validate-local.ps1 -Browser -Blender -Unity
```

Or, once every required value/app is configured:

```powershell
.\scripts\validate-local.ps1 -All
```

Do not advance to desktop coordinate automation until the API/CLI/browser paths have been validated and shown insufficient.
