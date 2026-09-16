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
| 0 | Repository + engineering workflow | Implemented | CI workflow active | None |
| 1 | Local development environment | Repo side implemented | `uv sync` works in CI; package installs | Clone/sync on Rafael's Windows machine; local `.env`; local apps |
| 2 | Typed config + doctor | Implemented | Unit tests; offline + online diagnostic code tested with fakes | `harness doctor --online` on Windows |
| 3 | LLM contract + DeepSeek | Implemented | Provider mapping/tool-call/usage/error tests | Real DeepSeek key + live request |
| 4 | Tool registry + filesystem + shell | Implemented | Unit/integration tests; global tool timeout | Real Windows smoke tasks |
| 5 | Agent loop | Implemented | Fake-provider end-to-end tests, limits, cancellation | Real DeepSeek → tool → result → DeepSeek run |
| 6 | Sessions + persistence + artifacts | Implemented | SQLite integration tests, resume, schema guard, foreign keys | Process restart/resume on Windows |
| 7 | Permissions + approvals + runtime hooks | Implemented | Deterministic permission/approval tests | Manual approval UX validation |
| 8 | Observability | Implemented | Persisted events, timing, token usage, CLI inspection | Inspect one real success and failure run |
| 9 | Browser / Playwright | Implemented | Controller/tool tests; online doctor probe available | Install Chromium and run real browser smoke task |
| 10 | Interactive ChatGPT browser workflow | Not started | — | Requires authenticated browser profile and interactive policy |
| 11 | Screenshot + vision abstraction | Implemented / partial | Screenshot artifacts, `VisionProvider`, `vision_inspect`, visual verifier tests | Choose/inject a real vision provider |
| 12 | Blender | Implemented / partial | CLI/controller/tool tests with fakes | Real `blender.exe`, create/render/export validation |
| 13 | Unity | Implemented / partial | CLI/controller/editor-script tests with fakes | Real `Unity.exe`, project/import/editor validation |
| 14 | Generic image providers | Abstraction implemented | `ImageProvider` + `image_generate` tool tests | Add at least one concrete provider |
| 15 | Verification / self-correction | Implemented | Generic verifier + visual verifier retry tests | Real image/vision correction loop |
| 16 | Context management | Implemented | Compaction tests incl. tool-call boundary safety | Evaluate long real sessions |
| 17 | Runtime skills | Implemented | Bounded `skill_list` / `skill_load` tests | Add useful production skills and run smoke eval |
| 18 | Desktop/computer-control fallback | Not started | — | Decide only after CLI/API/browser gaps are proven |
| 19 | Reliability / evals | Implemented / partial | YAML eval runner, required tools, token/step/error metrics, smoke suite | Run `evals/smoke.yaml` against real DeepSeek and apps |
| 20 | Packaging + v1 acceptance | Partial | CLI package entrypoint; Linux CI; Windows CI added | Real Windows acceptance suite + external app flows |

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

The project is currently strong through Levels 1–3. Windows CI has been added and must stay green. Levels 5–6 are intentionally still manual gates.

## Next Rafael gate

Once CI is green, run on the target Windows machine:

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

Then run:

```powershell
uv run harness doctor
uv run harness doctor --online
uv run harness eval evals/smoke.yaml --json-out data/smoke-report.json
```

Do not advance to desktop coordinate automation until the API/CLI/browser paths have been validated and shown insufficient.
