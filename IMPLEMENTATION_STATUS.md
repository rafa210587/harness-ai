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
| 1 | Local development environment | Repo side implemented | `uv sync`, package install and CLI entrypoint pass on Windows CI | Clone/sync on Rafael's Windows machine; local `.env`; local apps |
| 2 | Typed config + doctor | Implemented | Unit tests; offline + online diagnostic code tested with fakes | `harness doctor --online` on Rafael's Windows machine |
| 3 | LLM contract + DeepSeek | Implemented | Provider mapping/tool-call/usage/error + bounded retry tests | Real DeepSeek key + live request |
| 4 | Tool registry + filesystem + shell | Implemented | Linux + Windows core tests; global tool timeout; workspace + symlink boundary tests | Real local smoke tasks |
| 5 | Agent loop | Implemented | Fake-provider end-to-end tests, limits, cancellation | Real DeepSeek → tool → result → DeepSeek run |
| 6 | Sessions + persistence + artifacts | Implemented | SQLite integration tests, resume, schema guard, indexes, foreign keys | Process restart/resume on Rafael's machine |
| 7 | Permissions + approvals + runtime hooks | Implemented | Deterministic permission/approval + tool-risk invariant tests | Manual approval UX validation |
| 8 | Observability | Implemented | Persisted events, timing, token usage, CLI inspection | Inspect one real success and failure run |
| 9 | Browser / Playwright | Implemented | Controller/tool tests; real-runtime smoke test exists but is excluded from CI until Chromium is installed | `pytest -m browser_runtime` after Playwright Chromium install |
| 10 | Interactive ChatGPT browser workflow | Not started | — | Requires authenticated browser profile and interactive policy |
| 11 | Screenshot + vision abstraction | Implemented / partial | Screenshot artifacts, `VisionProvider`, `vision_inspect`, visual verifier tests | Choose/inject a real vision provider |
| 12 | Blender | Implemented / partial | CLI/controller/tool tests with fakes; real Blender smoke test exists | `pytest -m blender` with real `BLENDER_PATH` |
| 13 | Unity | Implemented / partial | CLI/controller/editor-script tests with fakes; real Unity smoke test exists | `pytest -m unity` with real `UNITY_PATH` + disposable smoke project |
| 14 | Generic image providers | Abstraction implemented | `ImageProvider` + `image_generate` tool tests | Add at least one concrete provider |
| 15 | Verification / self-correction | Implemented | Generic verifier + visual verifier retry tests | Real image/vision correction loop |
| 16 | Context management | Implemented | Compaction tests incl. tool-call boundary safety | Evaluate long real sessions |
| 17 | Runtime skills | Implemented | Bounded `skill_list` / `skill_load` tests | Add useful production skills and run smoke eval |
| 18 | Desktop/computer-control fallback | Not started | — | Decide only after CLI/API/browser gaps are proven |
| 19 | Reliability / evals | Implemented / partial | YAML eval runner, required tools, token/step/error metrics, smoke suite | Run `evals/smoke.yaml` against real DeepSeek |
| 20 | Packaging + v1 acceptance | Partial | CLI package entrypoint and core suite pass on both Linux and Windows GitHub runners | Real host/app acceptance suite + cross-application flows |

## Core already implemented

The current repository includes:

```text
typed YAML/.env configuration
DeepSeek provider abstraction
provider-neutral LLM timeout/retry
normalized token usage
Tool + ToolResult + ToolRegistry
global tool timeout
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
YAML eval runner
smoke eval suite
resource cleanup + cancelled session state
Linux quality CI + Windows core CI
explicit real-runtime smoke tests for Chromium, Blender and Unity
```

## Evidence levels

Do not conflate these levels:

```text
Level 1: unit/contract behavior
Level 2: integration with local deterministic components
Level 3: GitHub CI on Linux
Level 4: GitHub CI on Windows
Level 5: real DeepSeek / Chromium / Blender / Unity on Rafael's host
Level 6: complete cross-application workflow with visual verification
```

The project is currently validated through Level 4 for the core. Levels 5–6 are intentionally still local/manual gates.

## Known cleanup that should wait for local dependency resolution

- `httpx` is still declared directly but has no current direct import. Remove it during the next intentional `uv` dependency update if no concrete localhost bridge needs it; regenerate `uv.lock` with `uv`, never by hand.

## Next Rafael gate

On the target Windows machine:

```powershell
git pull
uv python install 3.12
uv sync
uv run playwright install chromium
Copy-Item .env.example .env
```

Fill at minimum:

```dotenv
DEEPSEEK_API_KEY=...
BLENDER_PATH=...
UNITY_PATH=...
```

For the Unity integration smoke test, point only to a disposable test project:

```dotenv
HARNESS_UNITY_SMOKE_PROJECT=C:\path\to\DisposableUnitySmokeProject
```

Then run the core/provider gates:

```powershell
uv run harness doctor
uv run harness doctor --online
uv run harness eval evals/smoke.yaml --json-out data/smoke-report.json
```

Then run each real application bridge independently:

```powershell
uv run pytest -m browser_runtime
uv run pytest -m blender
uv run pytest -m unity
```

Do not advance to desktop coordinate automation until the API/CLI/browser paths have been validated and shown insufficient.
