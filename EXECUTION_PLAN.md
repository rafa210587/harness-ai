# Execution Plan

> Permanent roadmap for building `harness-ai` from repository bootstrap to a usable v1.
>
> This file answers **what is built, in what order, who executes each step, and what must be true before we advance**. It does not replace feature specs. Medium and large phases create temporary work artifacts under `.work/<feature>/` when execution starts.

## 1. Execution model

There are three execution roles.

| Role | Meaning |
|---|---|
| **Coding Agent** | Claude Code, Codex, ChatGPT Work, or another coding agent operating on the repository. |
| **Me (Rafa)** | Actions that require my local Windows machine, credentials, account login, application installation, visual acceptance, or explicit approval. |
| **Harness** | Automated behavior that the product itself must perform once the relevant phase exists. |

Default rule:

```text
repository code/docs/tests       -> Coding Agent
credentials / local applications -> Me (Rafa)
repetitive runtime work          -> Harness
```

A coding agent may prepare commands or configuration for me, but it must not pretend that local Blender, Unity, browser-login, GPU, or account-dependent validation happened when it did not.

---

## 2. Feature execution workflow

Each phase is implemented using the repository workflow from `AGENTS.md`.

```text
small  -> inspect -> change -> test
medium -> refine -> SPEC -> TASKS -> implement -> simplify -> review
large  -> refine -> SPEC -> PLAN -> TASKS -> implement -> simplify -> review
```

Temporary files:

```text
.work/<feature>/
├── REFINEMENT.md   # large only when scope needs refinement
├── SPEC.md
├── PLAN.md         # large only
└── TASKS.md
```

Rules:

- `.work/` is never committed.
- Do not pre-create specs for future phases.
- Start a phase only when its dependencies and entry criteria are satisfied.
- Permanent architecture decisions go to `ARCHITECTURE.md`.
- Permanent setup changes go to `SETUP.md`.
- Repository-process changes go to `REPOSITORY.md` / `AGENTS.md`.
- The roadmap tracks phase status and durable milestones only.

---

## 3. Status legend

```text
DONE        implemented or repository work complete
PARTIAL     some repository work exists, but exit criteria are not met
READY       dependencies satisfied; implementation may start
BLOCKED     requires a previous phase or a manual action
FUTURE      intentionally later in the roadmap
```

---

# Phase 0 — Repository and engineering workflow

**Status:** DONE

## Goal

Create a repository that coding agents can modify safely without generating unnecessary architecture, documentation, or framework complexity.

## Repository work

Implemented:

- `ARCHITECTURE.md`
- `REPOSITORY.md`
- `SETUP.md`
- `AGENTS.md`
- `CLAUDE.md`
- `SKILLS_HOOKS.md`
- Python 3.12 project definition
- `uv` dependency model
- `.env.example`
- config examples
- Ruff / mypy / pytest / pre-commit configuration
- Claude Code skills
- Claude Code development hooks
- Cursor rule
- initial package layout
- initial CLI
- initial tests
- feature workflow: refine/spec/plan/tasks/implement/simplify/review

## I (Rafa) need to do

Nothing else for repository bootstrap.

## Exit criteria

- [x] Repository exists and `main` is usable.
- [x] Architecture source of truth exists.
- [x] Coding-agent rules exist.
- [x] Development skills/hooks exist.
- [x] Python project scaffold exists.

---

# Phase 1 — Local development environment

**Status:** BLOCKED on my local machine

## Goal

Make my Windows machine capable of running, testing, and later controlling the harness, Chromium, Blender, and Unity.

## Coding Agent executes

The agent may update setup scripts or `harness doctor`, but should not install account-specific software remotely unless explicitly operating on my machine with permission.

## I (Rafa) execute

From PowerShell:

```powershell
git clone https://github.com/rafa210587/harness-ai.git
cd harness-ai

uv python install 3.12
uv sync
uv run playwright install chromium
Copy-Item .env.example .env
```

If `uv` is not installed:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Install or confirm locally:

```text
Git
Blender
Unity Hub
Unity Editor version used by the target project
```

Fill `.env` locally:

```dotenv
DEEPSEEK_API_KEY=<my key>
BLENDER_PATH=<my blender.exe>
UNITY_PATH=<my Unity.exe>
```

Run:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run harness doctor
```

Commit the real generated `uv.lock` after `uv sync` succeeds.

## Artifacts

```text
uv.lock
local .env          # never committed
local .venv/        # never committed
Playwright Chromium # local runtime
```

## Exit criteria

- [ ] `uv sync` succeeds.
- [ ] `uv.lock` is generated and committed.
- [ ] fast tests pass locally.
- [ ] `harness doctor` runs.
- [ ] Blender executable is resolvable.
- [ ] Unity executable is resolvable.

**Next:** Phase 2.

---

# Phase 2 — Configuration and `doctor`

**Status:** PARTIAL

## Goal

Create one typed configuration path and make environment failures obvious before the agent starts doing work.

## Dependencies

- Phase 1 local environment.

## Coding Agent executes

Create/refine:

```text
src/harness/config.py or config package
Pydantic settings models
config YAML loading
.env loading
path normalization
validation errors
```

Extend `harness doctor` to validate:

```text
Python version
workspace/data write access
SQLite availability
DeepSeek configuration
DeepSeek connectivity (optional explicit online check)
Playwright package
Chromium launch
Blender executable + version
Unity executable + version
Git
```

Important behavior:

- static doctor checks must work offline;
- external connectivity checks must be explicit and clearly labeled;
- missing optional apps must not prevent core CLI operation;
- secrets must never be printed.

## Tests

```text
configuration precedence
missing required value behavior
path parsing
secret redaction
doctor result aggregation
```

Commands:

```powershell
uv run pytest tests/unit
uv run harness doctor
```

## I (Rafa) execute

- confirm detected paths are correct;
- fix `.env` if my local install paths differ;
- approve the final doctor output as understandable enough to diagnose a fresh machine.

## Exit criteria

- [ ] one typed settings model owns configuration;
- [ ] `doctor` distinguishes OK / warning / failure;
- [ ] no secret appears in logs/output;
- [ ] my Windows machine passes all checks for installed capabilities.

---

# Phase 3 — LLM provider contract + DeepSeek

**Status:** READY after Phase 2

## Goal

Make DeepSeek usable through a provider-neutral interface.

## Coding Agent executes

Create:

```text
src/harness/llm/base.py
src/harness/llm/models.py
src/harness/llm/deepseek.py
```

Define normalized contracts such as:

```text
LLMMessage
LLMRequest
LLMResponse
LLMToolCall
LLMUsage
LLMError
LLMProvider
```

DeepSeek implementation must support at minimum:

```text
text input
system instructions
conversation messages
tool definitions
tool-call responses
normalized usage where available
timeout
provider error normalization
```

Do not add routing, fallback, multi-model orchestration, or multiple agents yet.

Add CLI smoke path:

```powershell
uv run harness llm test "Reply with OK"
```

or equivalent `doctor --online` check.

## Tests

Unit tests mock the provider transport and verify:

```text
request mapping
response normalization
tool call parsing
HTTP/provider errors
timeouts
missing API key
```

One explicitly marked online smoke test validates the real key.

## I (Rafa) execute

- provide `DEEPSEEK_API_KEY` only in local `.env`;
- run the real online smoke test;
- confirm billing/access works for the configured model.

## Exit criteria

- [ ] DeepSeek returns a normalized text response.
- [ ] a synthetic tool-call response parses correctly.
- [ ] real online smoke test passes on my machine.
- [ ] runtime code outside `llm/` does not depend on DeepSeek SDK-specific types.

---

# Phase 4 — Tool contracts, registry, filesystem and shell

**Status:** BLOCKED by Phase 3

## Goal

Build the main capability boundary of the harness and prove it with useful local tools.

## Coding Agent executes

Create:

```text
src/harness/tools/base.py
src/harness/tools/registry.py
src/harness/tools/filesystem.py
src/harness/tools/shell.py
```

Core contracts:

```text
Tool
ToolRisk
ToolResult
ToolError
ToolRegistry
```

Initial tools:

```text
filesystem.list
filesystem.read
filesystem.write
filesystem.patch
filesystem.search
filesystem.mkdir
filesystem.copy
filesystem.move
shell.run
```

Do not expose delete/elevated behavior without the permission phase.

Tool results must retain useful error information and never throw provider-specific objects into the agent loop.

## Tests

Use temporary directories and controlled subprocesses.

Validate:

```text
path boundaries
schema generation
argument validation
stdout/stderr/exit codes
timeouts
unknown tool handling
registry duplicate detection
```

## I (Rafa) execute

Run the smoke scenarios on Windows:

```text
list this repository
read README.md
write a temporary workspace file
run `git status`
```

No administrator privileges should be needed.

## Exit criteria

- [ ] tool schemas can be sent to an LLM;
- [ ] registry resolves tools deterministically;
- [ ] filesystem operations are restricted to allowed roots;
- [ ] shell timeout/output handling works on Windows;
- [ ] no destructive tool bypass exists.

---

# Phase 5 — First complete agent loop

**Status:** BLOCKED by Phases 3-4

## Goal

Reach the first true harness milestone:

```text
User
 -> DeepSeek
 -> tool request
 -> Tool Registry
 -> local execution
 -> ToolResult
 -> DeepSeek
 -> final answer
```

## Coding Agent executes

Create/refine:

```text
src/harness/runtime/agent_loop.py
src/harness/runtime/context.py
src/harness/runtime/limits.py
```

Loop responsibilities:

```text
receive goal
build context
call LLM
parse zero/many tool calls
execute tools
append observations
continue
finish
```

Required protections:

```text
max steps
max consecutive failures
tool timeout
LLM timeout
cancellation
clear terminal state
```

Do not introduce LangGraph, Temporal, or multi-agent orchestration.

Add:

```powershell
harness run "List the Python files in this repository and tell me how many there are."
```

## Tests

Use a fake scripted LLM provider:

```text
response 1 -> tool call
response 2 -> final answer
```

Test:

```text
successful loop
unknown tool
invalid args
tool failure
LLM failure
step limit
cancellation
```

## I (Rafa) execute

Run the same task with the real DeepSeek provider and inspect:

- whether the right tool is selected;
- whether the tool result is correctly fed back;
- whether the final answer matches the actual filesystem.

## Exit criteria

- [ ] real DeepSeek completes at least one filesystem task through tools;
- [ ] no hidden hardcoded workflow is required;
- [ ] limits stop bad loops;
- [ ] failures are understandable.

**Milestone A:** the project is now a real tool-using harness.

---

# Phase 6 — Sessions, persistence and artifacts

**Status:** BLOCKED by Phase 5

## Goal

Make tasks resumable, inspectable, and able to refer to generated files consistently.

## Coding Agent executes

Implement SQLite persistence:

```text
sessions
messages / turns
tool calls
approvals
artifacts
events
```

Create:

```text
Session
SessionStatus
Artifact
ArtifactType
ArtifactRepository
SessionRepository
```

CLI:

```powershell
harness sessions
harness session show <id>
harness resume <id>
```

Artifact storage must distinguish:

```text
metadata in SQLite
files on disk
```

No binary blobs inside SQLite unless a later measured need justifies it.

## Tests

```text
create/load session
persist tool call/result
resume context
artifact metadata
transaction rollback
schema initialization/migration strategy
```

## I (Rafa) execute

- run a task;
- close the CLI;
- reopen it;
- inspect and resume the session;
- verify generated artifacts remain accessible.

## Exit criteria

- [ ] task history survives process restart;
- [ ] session can be resumed;
- [ ] every generated file may be referenced as an artifact;
- [ ] storage errors do not silently corrupt session state.

---

# Phase 7 — Runtime hooks, permissions and human approval

**Status:** BLOCKED by Phase 5; persistence from Phase 6 strongly preferred

## Goal

Enforce side-effect safety outside the prompt.

## Coding Agent executes

Create:

```text
src/harness/hooks/base.py
src/harness/hooks/dispatcher.py
src/harness/hooks/builtin/permissions.py
src/harness/hooks/builtin/audit.py
src/harness/runtime/approvals.py
```

Events:

```text
SESSION_START
BEFORE_LLM_REQUEST
AFTER_LLM_RESPONSE
BEFORE_TOOL
AFTER_TOOL
TOOL_ERROR
BEFORE_APPROVAL
AFTER_APPROVAL
ARTIFACT_CREATED
SESSION_END
```

Permission actions:

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

Initial policy:

```text
read                           -> automatic
write inside configured roots -> configurable/automatic
file deletion                 -> approval
normal shell                  -> configurable
elevated/destructive shell    -> approval or deny
browser read/navigation       -> automatic
browser submit/account action -> approval
purchase                      -> deny by default
git push                      -> approval
```

## Tests

Permission tests must not depend on LLM behavior.

Test precedence:

```text
DENY wins over REQUIRE_APPROVAL
REQUIRE_APPROVAL wins over ALLOW
```

## I (Rafa) execute

Manually validate:

- allowed read happens without interruption;
- deletion asks me;
- denied operation cannot be tricked by prompt wording;
- approval clearly shows operation and arguments.

## Exit criteria

- [ ] dangerous behavior cannot bypass the permission path;
- [ ] approval decisions are persisted/audited;
- [ ] model prompt is guidance, not enforcement.

---

# Phase 8 — Structured observability

**Status:** BLOCKED by Phase 5

## Goal

Make every agent run debuggable without introducing an external observability platform.

## Coding Agent executes

Structured events/logging for:

```text
LLM request metadata
LLM response metadata
tool start/end/error
duration
usage/cost fields where available
session/step ids
artifact ids
approval decisions
```

Requirements:

- no API keys/secrets;
- do not log giant file contents by default;
- human-readable console + structured persisted event;
- correlation by session and step.

CLI:

```powershell
harness session events <id>
```

## I (Rafa) execute

Run one failing and one successful task and confirm I can identify:

```text
which LLM call happened
which tool ran
how long it took
where it failed
what artifact was produced
```

## Exit criteria

- [ ] one run can be reconstructed from events;
- [ ] secrets are redacted;
- [ ] logging failure does not normally crash the run.

---

# Phase 9 — Browser automation

**Status:** BLOCKED by Phases 5 and 7

## Goal

Expose Chromium/Playwright as semantic tools.

## Coding Agent executes

Create/refine:

```text
src/harness/browser/playwright_controller.py
src/harness/tools/browser.py
```

Initial tools:

```text
browser.open
browser.navigate
browser.read_page
browser.click
browser.type
browser.wait
browser.screenshot
```

Priority:

```text
DOM / accessible locator
> semantic selector
> explicit coordinates only as fallback
```

Support:

```text
headless mode
visible mode
persistent profile when explicitly enabled
screenshots/traces on failure
```

Risk classification must distinguish reading from side effects.

## Tests

Use a local deterministic HTML test site for most integration tests.

Test:

```text
navigation
text extraction
form filling
clicking
screenshots
timeouts
failed locator diagnostics
permission on submit
```

## I (Rafa) execute

- run visible Chromium locally;
- validate the persistent profile path;
- optionally log into services that later require a human-authenticated profile;
- never commit the browser profile.

## Exit criteria

- [ ] agent can research/read a page;
- [ ] agent can interact with a controlled form;
- [ ] side-effect submission requires permission according to policy;
- [ ] screenshot becomes an Artifact.

---

# Phase 10 — Interactive ChatGPT browser capability

**Status:** BLOCKED by Phase 9

## Goal

Allow the harness to use my already-authenticated ChatGPT web session as an explicitly interactive/human-in-the-loop capability where appropriate, especially for image generation.

## Coding Agent executes

Create the abstraction:

```text
InteractiveImageProvider
ChatGPTInteractiveProvider
```

The flow should be explicit:

```text
agent builds prompt
-> browser opens/focuses ChatGPT
-> prompt is prepared
-> human approval/interaction gate
-> generated image is saved/imported as Artifact
```

This provider must not be treated internally as an unattended API.

Do not couple the rest of the harness to ChatGPT DOM details. Browser/UI-specific logic stays in the provider/controller boundary.

## I (Rafa) execute

- use a persistent browser profile;
- sign in to ChatGPT manually;
- complete any MFA/captcha/account verification myself;
- approve the interactive image-generation action when requested;
- validate that the resulting image is imported correctly.

## Exit criteria

- [ ] image request can reach an authenticated interactive browser flow;
- [ ] human approval/interaction is explicit;
- [ ] resulting image is represented as an Artifact;
- [ ] failure of ChatGPT UI does not break generic image-provider contracts.

---

# Phase 11 — Screenshot and vision abstraction

**Status:** BLOCKED by artifact support; browser screenshot may already exist

## Goal

Give the agent a generic way to inspect visual outputs from browser, Blender, Unity, and eventually desktop control.

## Coding Agent executes

Define:

```text
screenshot.capture / application-specific capture
VisionProvider
VisionRequest
VisionResult
```

Do not assume the DeepSeek text provider is the vision provider.

The provider must be configurable independently.

Sources:

```text
browser screenshot
Blender render
Unity Game View capture
desktop screenshot later
user-provided image artifact
```

The vision result should be useful for verification, e.g.:

```text
description
issues found
structured checks when requested
confidence/limitations where available
```

## I (Rafa) execute

Choose/configure the actual vision-capable provider when this phase starts if the current provider set cannot satisfy it.

This is a deliberate decision gate; do not add a paid provider before it is required.

## Exit criteria

- [ ] a screenshot Artifact can be sent to a vision provider;
- [ ] result returns through a provider-neutral contract;
- [ ] agent can use the observation in a later reasoning step.

---

# Phase 12 — Blender vertical slice

**Status:** BLOCKED by Phases 5-7 and local Blender

## Goal

Prove that the harness can create a real 3D asset programmatically and inspect its result.

## Coding Agent executes

Create:

```text
src/harness/blender/controller.py
src/harness/tools/blender.py
workspace/blender generated-script convention
```

MVP implementation:

```text
Blender CLI/background mode
+ generated Python script
```

Initial capabilities:

```text
blender.execute_python
blender.open_file
blender.save_file
blender.render
blender.export_fbx
blender.export_gltf
```

First deterministic demo:

```text
create cube
set camera/light/material
render PNG
save .blend
export FBX
register artifacts
```

Do not build a persistent Blender addon/socket bridge yet.

## Tests

Unit:

```text
command construction
script paths
artifact paths
timeouts
error parsing
```

Marked integration test with real Blender:

```powershell
uv run pytest -m blender
```

## I (Rafa) execute

- confirm `BLENDER_PATH`;
- run marked Blender integration test locally;
- visually inspect the first render;
- confirm generated `.blend` and FBX open correctly.

## Exit criteria

- [ ] agent can create a cube through Blender Python;
- [ ] Blender returns a render Artifact;
- [ ] FBX/GLTF export exists;
- [ ] failures return useful console/script errors.

**Milestone B:** DeepSeek can cause a real visual asset to be produced on my machine.

---

# Phase 13 — Unity vertical slice

**Status:** BLOCKED by local Unity and preferably Phase 12

## Goal

Import a harness-generated asset into a real Unity project without desktop clicking.

## Coding Agent executes

Create:

```text
src/harness/unity/controller.py
src/harness/tools/unity.py
Editor-script templates/bridge convention
```

MVP integration:

```text
Unity CLI
+ Editor scripts
+ filesystem
```

Initial capabilities:

```text
unity.project_info
unity.refresh_assets
unity.execute_editor_script
unity.import_asset
unity.open_scene
unity.create_game_object
unity.read_console
unity.capture_game_view
```

First deterministic demo:

```text
copy Blender FBX into Assets/
refresh/import
create GameObject
place asset in scene
save scene
capture result
```

Do not build a persistent HTTP/WebSocket editor plugin unless this approach proves insufficient.

## Tests

Unit:

```text
project validation
command construction
editor script generation
log parsing
```

Marked real Unity tests:

```powershell
uv run pytest -m unity
```

## I (Rafa) execute

- choose a disposable/sandbox Unity project for integration tests;
- configure its path;
- run the real integration test;
- inspect the scene and Game View;
- confirm the harness does not damage unrelated project assets.

## Exit criteria

- [ ] generated Blender asset enters Unity automatically;
- [ ] object is placed/saved in a scene;
- [ ] console errors are readable by the harness;
- [ ] Game View/screenshot becomes an Artifact.

**Milestone C:** Blender -> Unity end-to-end asset workflow exists.

---

# Phase 14 — Generic image providers

**Status:** BLOCKED only by image abstraction; can run after browser/vision foundations

## Goal

Make image generation provider-independent so interactive ChatGPT is only one implementation.

## Coding Agent executes

Define:

```text
ImageProvider
ImageRequest
ImageResult
image.generate tool
```

Support provider capabilities/metadata such as:

```text
text-to-image
reference images
image editing if provider supports it
size/aspect options
human-interaction requirement
```

Possible providers later:

```text
ChatGPTInteractiveProvider
OpenAIImageProvider
GeminiImageProvider
ComfyUIProvider
other/local provider
```

Only implement providers that we actually configure/use.

## I (Rafa) execute

Choose whether I want an autonomous paid/API image provider in addition to my interactive ChatGPT flow.

If yes:

- create/configure its API credential;
- set budget limits where the provider offers them;
- run a smoke generation.

## Exit criteria

- [ ] agent invokes `image.generate` without provider-specific branching;
- [ ] at least one configured provider works end-to-end;
- [ ] generated images become Artifacts.

---

# Phase 15 — Verification and self-correction loop

**Status:** BLOCKED by Agent Loop + observation/artifact capabilities

## Goal

Move from "execute commands" to "do -> observe -> evaluate -> correct".

## Coding Agent executes

Add explicit verification behavior without creating a second agent yet.

Pattern:

```text
execute action
-> collect deterministic result/artifact
-> verify against acceptance goal
-> if mismatch, reason about correction
-> retry within limits
-> finish or BLOCKED
```

Verification sources:

```text
tool return codes
filesystem state
Unity console
Blender output
screenshots / vision
artifact existence
user-defined checks
```

Avoid asking an LLM to judge facts that can be checked deterministically.

Add retry budgets separately from the global step limit.

## Tests

Scenarios:

```text
first attempt succeeds
first attempt fails, second succeeds
permanent failure becomes BLOCKED
verification contradiction
retry budget exhausted
```

## I (Rafa) execute

Run real scenarios:

1. ask for an intentionally simple Blender result;
2. introduce a recoverable error;
3. verify the harness observes and corrects it;
4. do the same with a safe Unity sandbox workflow.

## Exit criteria

- [ ] at least one Blender workflow self-corrects after a failed attempt;
- [ ] at least one code/filesystem workflow self-corrects;
- [ ] retry loops have deterministic limits;
- [ ] final result states what was actually verified.

**Milestone D:** the harness is an autonomous iterative worker, not only a tool caller.

---

# Phase 16 — Context management and compaction

**Status:** BLOCKED until real sessions are long enough to measure

## Goal

Keep long runs usable without sending the entire session every turn.

## Coding Agent executes

Context Builder should select:

```text
stable system instructions
current goal
current working summary
recent turns
relevant tool results
relevant artifacts
pending approvals/errors
```

Add compaction only after measuring context growth.

Do not add vector DB/RAG here.

Compaction output must retain:

```text
goal
important decisions
current state
files/artifacts changed
unresolved problems
next intended action
```

## I (Rafa) execute

Run a long task and inspect whether the model forgets important state before/after compaction.

## Exit criteria

- [ ] long session stays under configured context budget;
- [ ] compaction preserves required execution state;
- [ ] regressions are covered by tests/evals.

---

# Phase 17 — Runtime skills

**Status:** FUTURE; implement only after repeated patterns exist

## Goal

Allow the harness itself to load procedural knowledge without hardcoding every workflow in Python.

## Entry criterion

We must have at least two or three repeated workflows where stable procedural instructions clearly improve behavior.

Examples:

```text
create-blender-prop
import-asset-to-unity
inspect-unity-scene
debug-unity-console
browser-research
generate-game-texture
```

## Coding Agent executes

Build a minimal loader for:

```text
skills/<name>/SKILL.md
```

Requirements:

```text
metadata/name/description
explicit skill selection/injection
size/context controls
no arbitrary code execution just because a skill exists
```

Do not turn skills into another tool/plugin framework.

## I (Rafa) execute

Review the first skills for whether they encode my desired workflow rather than unnecessary verbosity.

## Exit criteria

- [ ] one repeated workflow demonstrably improves with a runtime skill;
- [ ] skill loading is observable;
- [ ] skills remain instructions, not hidden executable plugins.

---

# Phase 18 — Desktop/computer control fallback

**Status:** FUTURE

## Goal

Control applications that expose no usable API, scripting interface, CLI, or browser semantics.

## Entry criterion

A real required workflow cannot be solved reliably by:

```text
native API
application scripting
CLI
browser semantic automation
```

## Coding Agent executes

Define generic capability boundaries such as:

```text
computer.screenshot
computer.window_list
computer.focus_window
computer.click
computer.type
computer.hotkey
```

Choose the concrete Windows automation library only at this phase after testing alternatives.

Safety requirements:

```text
visible target/window context
screenshot before risky interaction
approval for destructive/account side effects
coordinate actions treated as fragile
```

## I (Rafa) execute

- approve installation of any OS automation dependency;
- run GUI tests only on a safe desktop state;
- validate DPI/multi-monitor/scaling behavior;
- explicitly decide which apps may be controlled this way.

## Exit criteria

- [ ] one API-inaccessible application can be controlled reliably enough;
- [ ] failures cannot silently click/type into an unrelated foreground window;
- [ ] GUI automation remains fallback, not the default integration pattern.

---

# Phase 19 — Reliability and eval suite

**Status:** FUTURE, but test fixtures accumulate throughout earlier phases

## Goal

Measure whether changes improve or regress actual harness behavior.

## Coding Agent executes

Create a small deterministic eval suite covering capabilities, not benchmark theater.

Initial task set:

```text
filesystem inspection
shell command + interpretation
multi-tool sequence
recoverable tool failure
permission-required operation
browser research task
Blender cube/render
Blender export
Unity import/placement
visual verification
session resume
```

Measure:

```text
success/failure
steps
tool errors
retries
latency
LLM usage/cost where available
human approvals required
```

Add regression fixtures for every important production failure we discover.

Do not add Harbor/Langfuse or another eval framework unless the native suite becomes insufficient.

## I (Rafa) execute

Run the external-app eval subset on the actual Windows workstation when requested.

Review results for usefulness, not only pass percentage.

## Exit criteria

- [ ] core deterministic suite is repeatable;
- [ ] external application suite has documented environment requirements;
- [ ] architecture/provider changes can be compared against the same tasks.

---

# Phase 20 — Packaging and one-command bootstrap

**Status:** FUTURE

## Goal

Make a fresh Windows machine able to install and diagnose the harness without reading the source tree first.

## Coding Agent executes

Preferred first packaging:

```text
Python package + uv
```

Support:

```powershell
uv sync
uv run harness doctor
```

Optionally later:

```text
uv tool install
standalone Windows package
```

Create/complete:

```text
scripts/bootstrap.py or PowerShell bootstrap if justified
harness doctor --all
clear first-run configuration errors
```

Do not build an installer EXE until there is a real need.

## I (Rafa) execute

Test installation from a clean clone or clean Windows environment/profile.

Record any manual prerequisite that remains unavoidable.

## Exit criteria

- [ ] clean clone -> working CLI is documented and reproducible;
- [ ] doctor identifies missing dependencies;
- [ ] no undocumented global Python package is required.

---

# Phase 21 — v1 end-to-end acceptance

**Status:** FUTURE

## Goal

Declare v1 only after the product can complete representative real workflows safely.

## Required acceptance scenarios

### Scenario A — Local coding/tool task

Prompt example:

```text
Inspect this project, find the relevant files, make a bounded change, run verification, and report what changed.
```

Must demonstrate:

```text
DeepSeek reasoning
tool use
filesystem/shell
permissions
session persistence
verification
```

### Scenario B — Browser task

Prompt example:

```text
Open a test/research site, collect required information, capture evidence, and save a result artifact.
```

Must demonstrate:

```text
semantic browser automation
screenshots
side-effect policy
artifact handling
```

### Scenario C — Blender asset

Prompt example:

```text
Create a simple game-ready prop in Blender, render a preview, verify it, and export it.
```

Must demonstrate:

```text
Blender Python/CLI
artifacts
vision or deterministic verification
retry/correction
```

### Scenario D — Blender -> Unity

Prompt example:

```text
Create/export the prop, import it into the Unity sandbox project, place it in the scene, run validation, and show the result.
```

Must demonstrate:

```text
multi-application workflow
Blender
Unity
session state
artifacts
console inspection
visual verification
```

### Scenario E — Image-assisted workflow

Prompt example:

```text
Prepare a concept/texture image request, use the configured image provider, import the result as an artifact, and use it in the workflow.
```

For ChatGPT Interactive, the expected human interaction/approval is allowed and must be explicit.

## I (Rafa) execute

I perform final acceptance on my actual machine:

- approve any required human-in-the-loop steps;
- inspect generated visual assets;
- confirm Blender/Unity results are useful, not merely technically generated;
- confirm the safety prompts are neither missing nor unusably noisy;
- confirm I can understand failures and resume sessions.

## v1 exit criteria

- [ ] Scenarios A-D pass reliably on my Windows machine.
- [ ] At least one image-provider path works if image generation is included in v1 scope.
- [ ] No known path bypasses dangerous-action approval.
- [ ] Core tests are green.
- [ ] External Blender/Unity/browser integration tests are green on the target machine.
- [ ] `SETUP.md` reproduces a working environment.
- [ ] `harness doctor` diagnoses missing prerequisites.
- [ ] Failures and limitations are documented factually.

---

# 22. Dependency map

```text
Phase 0  Repository/workflow
   |
Phase 1  Local environment
   |
Phase 2  Config + doctor
   |
Phase 3  LLM provider
   |
Phase 4  Tool contracts + filesystem/shell
   |
Phase 5  Agent loop
   +--------------------+
   |                    |
Phase 6 Sessions     Phase 8 Observability
   |                    |
Phase 7 Permissions ----+
   |
Phase 9 Browser
   |        \
   |         -> Phase 10 ChatGPT Interactive
   |
Phase 11 Vision/artifact observation
   |
Phase 12 Blender
   |
Phase 13 Unity
   |
Phase 15 Verification/self-correction
   |
Phase 16 Context management (when measured)
   |
Phase 19 Evals
   |
Phase 20 Packaging
   |
Phase 21 v1 acceptance

Optional/on-demand branches:
Phase 14 Generic image providers
Phase 17 Runtime skills
Phase 18 Desktop control fallback
```

Some phases can overlap once the core loop exists, but dependencies above define the safe default order.

---

# 23. Recommended immediate sequence

Do not start Blender or Unity implementation yet.

The next concrete sequence is:

```text
1. I (Rafa): clone/sync/configure the local environment and commit uv.lock.
2. Coding Agent: finish typed config + doctor.
3. I (Rafa): validate doctor on Windows.
4. Coding Agent: implement DeepSeek provider contract.
5. I (Rafa): run real DeepSeek smoke test.
6. Coding Agent: implement Tool/ToolRegistry + filesystem/shell.
7. I (Rafa): run Windows filesystem/shell smoke tests.
8. Coding Agent: implement the first complete agent loop.
9. I (Rafa): run the first real DeepSeek -> tool -> result task.
```

Only after step 9 passes do we move into persistence, permissions, browser, Blender, and Unity.

---

# 24. Decision gates that remain intentionally open

These are not missing planning. They should be decided only when the relevant phase provides evidence.

| Decision | Decide when | Current default |
|---|---|---|
| Vision model/provider | Phase 11 | Separate provider abstraction; no premature paid dependency. |
| Autonomous image API provider | Phase 14 | Interactive ChatGPT first; API only if unattended generation is needed. |
| Persistent Blender bridge/addon | After Phase 12 measurements | CLI + Python first. |
| Persistent Unity bridge | After Phase 13 measurements | CLI + Editor scripts first. |
| Runtime skills loader | Phase 17 entry criterion | Do not build yet. |
| Desktop automation library | Phase 18 entry criterion | Do not choose yet. |
| LangGraph/Temporal | Only after measured failure of simple loop | Do not use. |
| External observability/eval platforms | Only after native facilities prove insufficient | JSON/SQLite/native tests first. |
| Multi-agent Architect/Implementer/Reviewer | Only if evals show measurable gain over role skills | Skills/single coding agent first. |

---

# 25. What completion means

The harness is not complete because every planned class exists.

It is complete when I can give it a real goal and it can safely perform work on my computer through explicit capabilities:

```text
understand goal
-> inspect environment
-> select tools
-> execute
-> observe
-> verify
-> correct
-> request human approval when required
-> persist the result
-> explain what actually happened
```

The architecture should remain as small as possible while satisfying that behavior.
