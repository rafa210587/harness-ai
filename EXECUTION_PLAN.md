# Execution Plan

> Durable roadmap for taking `harness-ai` from repository implementation to a usable v1.
>
> Current factual evidence lives in `IMPLEMENTATION_STATUS.md`. Architecture decisions live in `ARCHITECTURE.md`; setup commands live in `SETUP.md`. This file defines order, ownership and exit gates without duplicating those documents.

## 1. Execution roles

| Role | Responsibility |
|---|---|
| **Coding Agent** | Repository code, tests, CI, docs and deterministic fixtures. |
| **Me (Rafa)** | Real Windows host, credentials, installed apps, authenticated browser state and visual acceptance. |
| **Harness** | Runtime execution after the relevant capability exists. |

Default rule:

```text
repository code/docs/tests       -> Coding Agent
credentials / local applications -> Me (Rafa)
repetitive runtime work          -> Harness
```

A coding agent must never claim that DeepSeek, Chromium, Blender, Unity, authenticated browser state or visual quality was validated unless that real gate actually ran.

---

## 2. Feature workflow

Follow `AGENTS.md`.

```text
small  -> inspect -> change -> test
medium -> refine -> SPEC -> TASKS -> implement -> simplify -> review
large  -> refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review
```

Temporary work artifacts belong under `.work/<feature>/` and are not committed.

Do not introduce LangGraph, Temporal, Redis, PostgreSQL, a vector database, Kubernetes, multi-agent orchestration or desktop coordinate automation without a measured requirement and an architecture decision.

---

## 3. Status meanings

```text
DONE          repository work and required non-local evidence are complete
LOCAL GATE    implementation exists; the next missing proof requires Rafael's machine/account/apps
PARTIAL       useful implementation exists, but a repository or real-world acceptance item remains
NOT STARTED   intentionally deferred
```

`IMPLEMENTATION_STATUS.md` is authoritative when a detailed evidence question conflicts with this roadmap.

---

## 4. Current checkpoint

The repository core is implemented and validated through **Evidence Level 4**:

```text
Level 1  unit / contract behavior
Level 2  deterministic local integration / fakes
Level 3  GitHub CI on Linux
Level 4  GitHub CI on Windows
Level 5  real DeepSeek / Chromium / Blender / Unity on Rafael's host
Level 6  complete cross-application workflow with visual verification
```

Current remote evidence includes:

```text
Python 3.12 + uv project
provider-neutral DeepSeek contract
single-agent loop
Tool Registry
filesystem + shell
permissions + approvals
SQLite sessions/persistence/artifacts/events
browser/Playwright integration
screenshot + vision abstractions
Blender CLI/Python integration
Unity CLI/Editor-script integration
verification/self-correction
context compaction
runtime skills
eval runner + smoke suite
secret/path protections
browser SSRF/network protections
Linux quality CI
Windows core acceptance CI
uv build on Linux and Windows acceptance paths
```

The next meaningful work is not another speculative framework. It is **Level 5 real-host acceptance**, followed by **Level 6 end-to-end acceptance**.

---

## 5. Phase status

| Phase | Capability | Status | Next missing proof |
|---|---|---|---|
| 0 | Repository + engineering workflow | DONE | None |
| 1 | Local development environment | LOCAL GATE | Clean sync/config on Rafael's Windows host |
| 2 | Typed config + doctor | LOCAL GATE | Real `doctor --online` and installed-app detection |
| 3 | LLM contract + DeepSeek | LOCAL GATE | Real DeepSeek request/account access |
| 4 | Tool Registry + filesystem + shell | LOCAL GATE | Real Windows smoke tasks |
| 5 | Agent loop | LOCAL GATE | Real DeepSeek → tool → result → DeepSeek run |
| 6 | Sessions + persistence + artifacts | LOCAL GATE | Restart/resume on the real host |
| 7 | Permissions + approvals + runtime hooks | LOCAL GATE | Manual approval UX validation |
| 8 | Observability | LOCAL GATE | Inspect real successful and failing runs |
| 9 | Browser / Playwright | LOCAL GATE | Real Chromium runtime smoke |
| 10 | Interactive ChatGPT browser workflow | NOT STARTED | Only if interactive ChatGPT remains useful after core acceptance |
| 11 | Screenshot + vision abstraction | PARTIAL | Real vision provider and visual inspection |
| 12 | Blender | LOCAL GATE | Real Blender smoke with configured executable |
| 13 | Unity | LOCAL GATE | Real Unity smoke with disposable project |
| 14 | Generic image providers | PARTIAL | Concrete provider only if included in v1 scope |
| 15 | Verification / self-correction | LOCAL GATE | Real visual correction loop |
| 16 | Context management | LOCAL GATE | Long-session behavior on real tasks |
| 17 | Runtime skills | LOCAL GATE | Real DeepSeek smoke requiring `skill_list` + `skill_load` |
| 18 | Desktop/computer-control fallback | NOT STARTED | Decide only after API/CLI/browser gaps are demonstrated |
| 19 | Reliability / evals | LOCAL GATE | Run smoke eval against real DeepSeek/apps |
| 20 | Packaging + bootstrap | LOCAL GATE | Clean-clone/real-host reproducibility |
| 21 | v1 end-to-end acceptance | NOT STARTED | Requires Level 5 gates first |

---

# Phase 20 — Packaging and bootstrap

## Goal

A fresh Windows clone can install, diagnose and run the harness without undocumented global Python dependencies.

## Repository side

Implemented:

```text
Python package metadata
CLI entrypoint
committed uv.lock
scripts/validate-local.ps1
Linux distribution build gate
Windows distribution build gate
SETUP.md bootstrap instructions
harness doctor
```

## Me (Rafa)

On the target Windows host:

```powershell
git pull
uv python install 3.12
uv sync --all-groups
uv run playwright install chromium
Copy-Item .env.example .env
```

Then configure only the capabilities being tested:

```dotenv
DEEPSEEK_API_KEY=...
BLENDER_PATH=...
UNITY_PATH=...
HARNESS_UNITY_SMOKE_PROJECT=C:\path\to\DisposableUnitySmokeProject
```

Core gate:

```powershell
.\scripts\validate-local.ps1
```

Exit criteria:

- [x] package builds in Linux CI;
- [x] package builds through the Windows acceptance path;
- [x] CLI/package metadata are valid in CI;
- [ ] clean clone works on Rafael's real Windows host;
- [ ] no undocumented prerequisite blocks the local CLI;
- [ ] doctor gives actionable diagnostics for missing local capabilities.

---

# Phase 21 — v1 end-to-end acceptance

## Goal

Declare v1 only after representative workflows work safely on the target Windows machine.

## Gate A — Core Windows

Run:

```powershell
.\scripts\validate-local.ps1
```

Prove:

```text
uv sync
Ruff
mypy
core pytest
uv build
offline doctor
filesystem/shell
SQLite/session persistence
```

Also perform one explicit restart/resume smoke test.

## Gate B — Real DeepSeek

Run:

```powershell
.\scripts\validate-local.ps1 -Online
```

Must prove:

```text
real API authentication
configured model responds
DeepSeek selects a real tool
ToolResult returns to DeepSeek
final answer reflects actual tool output
smoke eval requires real tool + runtime-skill use
usage/events are persisted without secret leakage
```

## Gate C — Real Chromium

Run:

```powershell
.\scripts\validate-local.ps1 -Browser
```

Must prove:

```text
Chromium launches
semantic navigation/read works
screenshot artifact works
local/private network protections remain enforced
redirect/DNS-aware SSRF guard does not break normal public browsing
```

Authenticated browser-profile behavior is a separate explicit gate and must never expose profile secrets to the model or repository.

## Gate D — Real Blender

Configure `BLENDER_PATH`, then run:

```powershell
.\scripts\validate-local.ps1 -Blender
```

First vertical slice:

```text
DeepSeek
-> blender.execute_python
-> create simple object
-> render
-> persist artifact
-> report actual output path
```

Do not build a persistent Blender addon/bridge unless CLI + Python becomes a measured limitation.

## Gate E — Real Unity

Use a disposable project and configure:

```dotenv
UNITY_PATH=...
HARNESS_UNITY_SMOKE_PROJECT=...
```

Run:

```powershell
.\scripts\validate-local.ps1 -Unity
```

Must prove:

```text
Unity executable launches in supported batch path
Editor script executes
asset refresh/import path works
console/errors are observable
generated smoke-project modifications are bounded
```

Do not use an important production/game project for the first integration proof.

## Gate F — Level 6 cross-application workflow

After Gates A-E:

```text
DeepSeek goal
-> Blender creates/exports artifact
-> artifact metadata persists
-> Unity imports artifact
-> scene/result is captured
-> vision/verifier inspects result
-> correction loop runs when necessary
-> final result is inspectable and resumable
```

This is the first full product acceptance workflow.

## v1 scenarios

### Scenario A — Local coding/tool task

```text
Inspect a project, make a bounded change, run verification, persist the session and report exactly what changed.
```

Requires filesystem, shell, permissions, persistence and verification.

### Scenario B — Browser research task

```text
Open a public test/research site, collect information, capture evidence and save an artifact.
```

Requires semantic browser operations, screenshots, network policy and artifact handling.

### Scenario C — Blender asset

```text
Create a simple game-ready prop, render a preview, verify it and export it.
```

Requires Blender CLI/Python, artifacts and verification.

### Scenario D — Blender → Unity

```text
Create/export the prop, import it into a disposable Unity project, place/inspect it, validate the result and show evidence.
```

Requires the Level 6 multi-application path.

### Scenario E — Image-assisted workflow

Optional for the first v1 unless image generation is explicitly included in scope.

If included, at least one configured image-provider path must work. Interactive ChatGPT is allowed to remain human-in-the-loop.

## v1 exit criteria

- [ ] Gates A-E pass on Rafael's Windows host.
- [ ] Scenario D passes as a Level 6 workflow.
- [ ] dangerous actions cannot bypass approval/policy.
- [ ] core CI remains green on Linux and Windows.
- [ ] package build remains green on Linux and Windows paths.
- [ ] browser/Blender/Unity runtime tests pass on the target machine.
- [ ] real failures are diagnosable from sessions/events/tool results.
- [ ] setup reproduces the environment from a clean clone.
- [ ] limitations are documented factually.

---

## 6. Immediate execution sequence

Current sequence:

```text
1. Coding Agent: keep remote core/CI green and avoid speculative abstractions.
2. Me (Rafa): pull/sync/configure the real Windows host.
3. Me + Harness: run core-only local acceptance.
4. Me + Harness: run real DeepSeek acceptance/eval.
5. Me + Harness: run Chromium runtime acceptance.
6. Me + Harness: run Blender runtime acceptance.
7. Me + Harness: run Unity runtime acceptance in a disposable project.
8. Me + Harness: run Blender -> Unity -> visual verification Level 6 workflow.
9. Coding Agent: fix only failures discovered by those real gates and add regression tests.
10. Me + Coding Agent: perform final v1 acceptance.
```

If a local gate fails, the next repository change should target that concrete failure. Do not skip ahead by inventing another abstraction.

---

## 7. Decisions intentionally left open

| Decision | Decide when | Current default |
|---|---|---|
| Real vision provider | When Gate F needs it | Keep `VisionProvider` abstraction; choose the smallest usable provider. |
| Autonomous image provider | Only if v1 needs unattended image generation | Interactive/human path is acceptable first. |
| Persistent Blender bridge | After real Blender measurements | CLI + Python first. |
| Persistent Unity bridge | After real Unity measurements | CLI + Editor scripts first. |
| Desktop automation | After API/CLI/browser insufficiency is demonstrated | Do not choose a library yet. |
| LangGraph/Temporal | Only after measured simple-loop failure | Do not use. |
| External observability/eval platform | Only after native facilities prove insufficient | SQLite/events/native evals first. |
| Multi-agent architecture | Only if evals show measurable gain | Single agent + tools + skills first. |

---

## 8. Known cleanup

`httpx` remains declared directly but currently has no concrete direct runtime import. Do not churn the lockfile solely for cosmetic cleanup during acceptance. Remove it during the next intentional dependency update if no localhost bridge requires it.

---

## 9. Completion definition

The project is complete enough for v1 when a real task can safely traverse:

```text
understand goal
-> inspect environment
-> select tools
-> execute
-> observe
-> verify
-> correct
-> request approval when required
-> persist state/artifacts/events
-> resume when needed
-> report what actually happened
```

Completion is demonstrated by real Level 5/6 workflows, not by the existence of planned classes.
