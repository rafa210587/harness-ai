# Implementation Status

> Factual snapshot of what exists in code, what CI has proved, and what still requires Rafael's local Windows machine.
>
> **Migration status:** OpenCode-first migration is active on `migration/opencode-core`. The current custom runtime remains the evidence baseline until each replacement passes parity. See `OPENCODE_MIGRATION.md`.
>
> `EXECUTION_PLAN.md` remains the durable roadmap. This file tracks current evidence so roadmap intent is not confused with completed validation.

## OpenCode migration checkpoint

Repository-side work completed on `migration/opencode-core`:

```text
baseline SHA recorded: bf46d6276e6a53ecc79300862332202fe18e89fa
OpenCode-first ADR adopted
migration specification committed
OpenCode stable pinned: 1.18.31
Playwright MCP pinned: 0.0.81
Blender MCP pinned: 2.0.0
Blender MCP safe mode enabled; telemetry disabled
project opencode.jsonc added
conservative permission baseline added
Windows validation script added
CI job added for OpenCode configuration
real Windows CI MCP handshake proven: Playwright MCP connected
smoke-agent permission precedence verified from resolved OpenCode agent output
```

Real-host evidence added:

```text
real-host OpenCode foundation + Playwright MCP connection passed
real-host MCP package resolution: Unity 10.2.0 + Blender 2.0.0 passed
```

Real-host Stage 2 evidence:

```text
DeepSeek v4 Flash real-host gate: PASS
direct .env read: BLOCKED
targeted .env grep: BLOCKED
outside-root/junction read: BLOCKED
direct shell secret path: BLOCKED
Playwright MCP -> Chrome: PASS
environment-variable secret isolation: FAIL (provider secrets inherited by shell)
```

The environment leak root cause is now fixed on the migration branch: the OpenCode shell merges `process.env` first and plugin env overrides second, so secret keys must be explicitly overridden with empty values rather than deleted from the plugin env object. CI now includes a real OpenCode bash regression requiring a safe env marker to remain visible while a synthetic provider secret does not appear.

Still pending real-host evidence:

```text
OpenCode 1.18.31 installed on Rafael's Windows host
DeepSeek authenticated through OpenCode
real opencode run
real Playwright MCP -> Chrome interaction
Unity MCP benchmark
Blender MCP benchmark
OpenCode-native runtime skill files added; real skill-load proof pending
runtime cutover/deletion
```

The old custom runtime remains only as the parity baseline until those gates pass.

## Status meanings

- **Implemented** — code and automated tests exist.
- **CI validated** — automated GitHub Actions checks have exercised the implementation without external credentials/apps.
- **Local gate pending** — requires the real Windows host, credentials, login, Blender, Unity, Chrome, or visual acceptance.
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
| 9 | Browser / Playwright | Implemented | Controller/tool tests; real-runtime smoke test exists but is excluded from fast CI | `pytest -m browser_runtime` against installed Google Chrome |
| 10 | Interactive ChatGPT browser workflow | Not started | — | Requires authenticated browser profile and explicitly interactive/human-controlled flow |
| 11 | Screenshot + vision abstraction | Implemented / partial | Screenshot artifacts, `VisionProvider`, `vision_inspect`, visual verifier tests | Choose/inject a real vision provider |
| 12 | Blender | Implemented / partial | CLI/controller/tool tests with fakes; real Blender smoke test exists | `pytest -m blender` with real `BLENDER_PATH` |
| 13 | Unity | Implemented / partial | CLI/controller/editor-script tests with fakes; real Unity smoke test exists | `pytest -m unity` with real `UNITY_PATH` + disposable smoke project |
| 14 | Generic image providers | Abstraction implemented | `ImageProvider` + `image_generate` tool tests | Add at least one concrete provider if autonomous image generation is in v1 scope |
| 15 | Verification / self-correction | Implemented | Generic verifier + visual verifier retry tests | Real image/vision correction loop |
| 16 | Context management | Implemented | Compaction tests incl. tool-call boundary safety | Run forced-compaction scenario in `validate-full-local.ps1` |
| 17 | Runtime skills | Implemented | Bounded loader tests; real Blender/Unity/browser skills; smoke eval requires `skill_list` + `skill_load` | Run real DeepSeek smoke eval |
| 18 | Desktop/computer-control fallback | Not started | — | Decide only after CLI/API/browser gaps are proven |
| 19 | Reliability / evals | Implemented / partial | YAML eval runner, required tools, token/step/error metrics, smoke + full-local reliability suites | Run `scripts/validate-full-local.ps1` against the real host |
| 20 | Packaging + bootstrap | Repo side implemented | `uv build` and core acceptance pass on Linux and Windows GitHub runners; local acceptance script includes the distribution build | Clean-clone / real-host acceptance on Rafael's Windows machine |
| 21 | v1 end-to-end acceptance | In progress | Level 5 individual real-host gates passed; Level 6A Blender -> Unity workflow validated; full-local package implemented | Run the full-local package, then add real vision provider and complete Level 6B visual verification/correction |

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
Playwright browser tools with configurable browser channel; installed Chrome is the local default
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
explicit real-runtime smoke tests for Chrome, Blender and Unity
Windows local acceptance PowerShell script with distribution build gate
```

## Evidence levels

```text
Level 1: unit/contract behavior
Level 2: integration with deterministic local components/fakes
Level 3: GitHub CI on Linux
Level 4: GitHub CI on Windows
Level 5: real DeepSeek / Chrome / Blender / Unity on Rafael's host
Level 6: complete cross-application workflow with visual verification
```

The core, including the Python distribution build, is validated through Level 4. Level 5 has been validated on Rafael's Windows host for DeepSeek, Chrome, Blender, Unity, agent/tool use, and the real Blender -> Unity Level 6A workflow. Level 6B visual verification/correction remains.

## OpenCode generic-runtime replacement evidence

```text
OpenCode mock runtime replacement evidence: PASS
- custom provider config -> opencode run
- model -> built-in read -> model
- model -> native OpenCode skill -> model
- OpenCode session -> resume
```

This is sufficient CI evidence for replacement of the custom generic runtime layer, but destructive deletion remains blocked until the real DeepSeek/security/browser gates pass on Rafael's Windows host.

## Active OpenCode migration security finding

OpenCode permissions are not accepted as the sole deterministic secret boundary.

Repository-side mitigations now implemented:

```text
task/subagents denied
explicit .env/key read/edit denies
credential/key patterns ignored by Git/ripgrep
CLI/headless harness-policy plugin
direct sensitive-path rejection
outside-root + symlink escape rejection for direct file-tool paths
explicit sensitive grep/glob target rejection
explicit sensitive shell-reference rejection
```

Known limitation:

```text
arbitrary shell command approval is not equivalent to sandboxing;
broad grep safety still depends in part on keeping secrets out of the worktree/rg search set;
Desktop plugin hooks are not trusted until separately validated.
```

Generic-runtime cutover remains blocked until the final OpenCode path no longer needs worktree `.env` credentials and real exfiltration tests pass.

## Known cleanup that should wait for local dependency resolution

- `httpx` is still declared directly but has no current direct import. Remove it during the next intentional `uv` dependency update if no concrete localhost bridge needs it; regenerate `uv.lock` with `uv`, never by hand.

## Next Rafael gate

On the target Windows machine:

```powershell
git pull
uv python install 3.12
uv sync --all-groups
Copy-Item .env.example .env
```

The browser defaults to the installed Google Chrome. No `playwright install chromium` step is required unless `HARNESS_BROWSER_CHANNEL=playwright` is selected explicitly.

Fill the capabilities you intend to test:

```dotenv
DEEPSEEK_API_KEY=...
HARNESS_BROWSER_CHANNEL=chrome
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
