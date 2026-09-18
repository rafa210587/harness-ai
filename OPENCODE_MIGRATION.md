# OpenCode Core Migration

> Status: ACTIVE MIGRATION
>
> Decision date: 2026-09-17
>
> Baseline main commit: `bf46d6276e6a53ecc79300862332202fe18e89fa`
>
> Migration branch: `migration/opencode-core`

## 1. Decision

`harness-ai` will stop treating its custom Python agent runtime as the default long-term architecture.

OpenCode becomes the preferred generic agent runtime when it provides equal or better capability. Mature MCP servers and other maintained integrations are preferred over custom implementations when they pass our acceptance gates.

The repository will keep custom code only where it provides a concrete advantage or fills a capability gap.

The decision rule is:

```text
1. OpenCode built-in
2. official / well-maintained MCP or native integration
3. mature open-source integration
4. thin adapter around an existing capability
5. custom implementation only for a proven gap
```

Existing code is not preserved merely because it is already implemented.

## 2. Migration objective

Move from:

```text
custom Python runtime
├── LLM provider
├── agent loop
├── context + compaction
├── sessions
├── approvals
├── tool registry
├── filesystem/shell
├── skills
├── browser
├── Blender
└── Unity
```

toward:

```text
OpenCode
├── providers / models
├── agent loop
├── sessions
├── context / compaction
├── permissions
├── built-in coding/filesystem/shell
├── skills / agents
└── MCP clients
    ├── Playwright MCP            candidate replacement
    ├── Unity MCP                 candidate replacement
    ├── Blender MCP               benchmark candidates
    ├── computer-use MCP          benchmark candidates
    └── harness-local MCP         only for remaining gaps
```

## 3. Non-negotiable migration rules

### 3.1 No permanent dual runtime

Temporary parity code may exist only on this migration branch.

The final state must not contain both:

```text
OpenCode runtime
+
custom AgentLoop runtime
```

There will be one owner for each generic concern.

### 3.2 No residual legacy directories

Do not finish the migration with:

```text
legacy/
old/
v1/
runtime_old/
compat/
deprecated/
```

Git history is the archive.

### 3.3 Replacement before deletion

A capability is deleted only after its replacement passes the relevant gate.

After parity is proven, the old implementation is removed immediately rather than kept as a fallback.

### 3.4 Build only proven gaps

Before adding new code, document why OpenCode, an official MCP, or a mature existing integration does not satisfy the requirement.

### 3.5 Security remains deterministic

OpenCode permissions handle user approval and normal tool gating, but they are **not accepted as the sole security boundary** for this project.

Current upstream behavior/bugs mean we must separately defend against:

```text
indirect grep/glob exposure
outside-root traversal
subagent permission inconsistencies
shell pattern/obfuscation bypasses
Desktop plugin-hook differences
```

Current migration policy:

```text
task/subagents            -> deny
direct sensitive paths    -> harness-policy plugin + OpenCode deny rules
outside-root/symlink      -> harness-policy plugin for direct file tools
git/ripgrep secret files  -> .gitignore
provider credentials      -> OpenCode/provider auth outside the final worktree
arbitrary shell           -> approval boundary; never claimed as a secret sandbox
Desktop local plugins     -> not trusted until separately validated
```

Application integrations must still enforce their own structural invariants where required:

```text
path boundaries
secret redaction where technically enforceable
SSRF/network restrictions
Unity project boundaries
Blender output boundaries
dangerous operation validation
artifact path validation
```

The project-local policy plugin is deliberately small. It must not evolve into another agent runtime.

## 4. Current evidence baseline

At the migration baseline the custom runtime has already demonstrated:

```text
Level 1  unit / contract
Level 2  deterministic integration / fakes
Level 3  Linux CI
Level 4  Windows CI
Level 5  real DeepSeek / Chrome / Blender / Unity
Level 6A real Blender -> Unity workflow
```

The migration is not complete until the new stack re-establishes the applicable evidence levels.

Level 6B remains the target visual loop:

```text
Blender
-> Unity
-> screenshot
-> vision
-> defect evaluation
-> correction
-> verification
```

## 5. Component replacement matrix

| Current capability | Preferred target | Migration action |
|---|---|---|
| LLM provider abstraction | OpenCode providers | Replace |
| DeepSeek client/retry | OpenCode provider layer | Replace |
| Agent loop | OpenCode | Replace |
| Context builder | OpenCode | Replace |
| Context compaction | OpenCode | Replace |
| Sessions/messages | OpenCode | Replace |
| Approval engine | OpenCode permissions | Replace |
| Runtime skill loader | OpenCode skills | Replace |
| Generic filesystem tools | OpenCode built-ins | Replace |
| Generic shell tool | OpenCode built-in shell | Replace |
| Tool Registry | OpenCode built-ins + MCP | Replace |
| Coding/repository intelligence | OpenCode | Replace |
| Browser controller | Microsoft Playwright MCP first | Benchmark then replace if parity passes |
| Unity controller/tools | CoplayDev Unity MCP first | Benchmark then replace if parity passes |
| Blender controller/tools | mature Blender MCP candidates | Benchmark before retaining custom code |
| Desktop/computer use | existing MCP candidates | Benchmark before building |
| Vision | provider/MCP candidates | Benchmark; retain only gap |
| Image generation | provider/MCP candidates | Benchmark; retain only gap |
| Artifact conventions | repository-specific | Keep only minimal domain layer if needed |
| Security invariants | OpenCode permissions + tool-level validation | Preserve/reimplement only required invariants |
| Evals | repository-specific | Keep and retarget to OpenCode/MCP |
| Local acceptance scripts | repository-specific | Keep and retarget |
| CI | repository-specific | Keep and retarget |

## 6. Verified external candidates

### 6.1 OpenCode

The migration is based on current OpenCode capabilities including:

```text
project JSON/JSONC config
providers
permissions: allow / ask / deny
granular shell/path rules
sessions
context/compaction
skills
agents
local/remote MCP servers
CLI/headless operation
```

Project config is committed as `opencode.jsonc`.

OpenCode version must be pinned once the first real-host spike identifies the tested version.

### 6.2 Browser

Primary candidate:

```text
@playwright/mcp
```

Reasons:

```text
official Microsoft/Playwright project
accessibility-snapshot interaction
Chrome / Firefox / WebKit / Edge
persistent profiles
existing-browser attachment
screenshots
network/storage/tracing support
MCP-native
```

Do not migrate the current Python Playwright code into another custom MCP before evaluating this server.

### 6.3 Unity

Primary candidate:

```text
CoplayDev/unity-mcp v10.2.0
package: com.coplaydev.unity-mcp
Unity requirement: 2021.3+
```

The upstream project has an OpenCode configurator and can register either stdio or remote MCP transport. For this repository we will pin the Unity package version and keep project-level OpenCode configuration authoritative rather than silently relying on mutable global config.

Pinned Unity Package Manager source for the benchmark:

```text
https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0
```

It must be validated against our current Unity Level 5 and Blender -> Unity Level 6A scenarios before the custom Unity controller is removed.

### 6.4 Blender

No implementation is selected yet.

Benchmark mature Blender MCP candidates against the current controller using the same acceptance scenarios.

Selection criteria:

```text
reliability
tool coverage
maintenance/activity
Windows behavior
artifact/export support
headless/automation behavior
security boundary
latency/context overhead
testability
```

### 6.5 Windows / computer use

Do not build a desktop automation framework during this migration.

Current shortlist for a later benchmark:

```text
sandraschi/windows-computer-use-mcp
- primary functional candidate
- Python / pywinauto
- UI Automation + screenshots + OCR + mouse/keyboard
- active in September 2026
- MIT
- includes explicit safety documentation

deploymenttheory/windows-mcp-server
- policy/security candidate
- Go
- UI Automation + screenshots + Windows/system capabilities
- device-policy / egress / audit focus
- active in September 2026
- MIT
```

Other candidates remain useful references but are currently smaller, less active, or explicitly provide little/no security gating.

No Windows computer-use MCP is pinned yet. Selection requires a real-host benchmark after the structured Blender/Unity/browser paths are working, because desktop automation remains a fallback capability.

## 7. Target repository shape

The target is intentionally smaller than the current repository.

```text
harness-ai/
├── README.md
├── ARCHITECTURE.md
├── EXECUTION_PLAN.md
├── IMPLEMENTATION_STATUS.md
├── OPENCODE_MIGRATION.md
├── REPOSITORY.md
├── SETUP.md
├── AGENTS.md
├── CLAUDE.md
│
├── opencode.jsonc
├── .opencode/
│   ├── skills/
│   ├── agents/
│   └── plugins/            # only if a measured need remains
│
├── custom/                 # only proven gaps
│   └── ...
│
├── evals/
├── tests/
├── scripts/
├── workspace/
└── data/
```

The final repository may contain less than this if mature external components cover more capabilities.

## 8. Configuration ownership

Final ownership rules:

```text
providers/models          -> OpenCode config
permissions               -> OpenCode config
agents                    -> OpenCode
runtime skills            -> .opencode/skills
generic coding tools      -> OpenCode
external capabilities     -> MCP config
domain-specific settings  -> only if still required by retained custom code
secrets                   -> environment / provider auth; never Git
```

Do not keep the same setting in both YAML and `opencode.jsonc`.

## 9. Runtime ownership

Final generic-runtime ownership:

```text
OpenCode owns:
- model execution
- tool orchestration
- agent loop
- session lifecycle
- context
- compaction
- generic permissions
- generic shell
- generic filesystem/coding tools
- skill discovery/loading
- subagents
- MCP client lifecycle
```

The repository must not recreate these layers unless a documented OpenCode defect or missing requirement forces a replacement.

## 10. Migration roadmap

### M0 — Baseline and freeze

Status: COMPLETE

Tasks:

- [x] record baseline SHA `bf46d6276e6a53ecc79300862332202fe18e89fa`
- [x] create `migration/opencode-core`
- [x] trigger CI on the migration branch
- [x] Linux quality CI passes
- [x] Windows core CI passes
- [x] OpenCode foundation Windows CI passes
- [x] freeze new feature work in the old runtime through `AGENTS.md`
- [x] add migration decision to architecture/roadmap docs

Exit:

```text
baseline reproducible
rollback SHA known
migration branch exists
```

### M1 — OpenCode foundation spike

Pinned baseline:

```text
OpenCode stable: 1.18.31
Playwright MCP: 0.0.81
```

Tasks:

- [x] add project `opencode.jsonc`
- [x] define safe initial permissions
- [x] document OpenCode installation/version pin strategy
- [x] add repository validator for `opencode debug config`
- [x] configure official Playwright MCP as the first MCP integration
- [x] prove `opencode debug config` on CI
- [x] prove enabled Playwright MCP handshake on Windows CI
- [ ] prove `opencode debug config` on Rafael's Windows host
- [ ] prove `opencode run`
- [ ] connect real DeepSeek or current selected provider
- [ ] prove one real model response
- [ ] prove model -> Playwright MCP -> Chrome round-trip

Exit:

```text
OpenCode starts from the repository
project config resolves
real model works
local MCP round-trip works
```

CI evidence:

```text
GitHub Actions run: 35286379422
quality:             success
windows-core:        success
opencode-foundation: success
```

Additional MCP evidence:

```text
GitHub Actions run: 35286792113
quality:             success
windows-core:        success
opencode-foundation: success

OpenCode MCP status:
✓ playwright connected
○ unityMCP disabled
○ blenderMCP disabled
```

The validator now fails if an enabled MCP reports `failed` or `timed out`. This closes a false-green discovered in an earlier run where `opencode mcp list` returned exit code 0 despite a server timeout.

Real Windows host foundation evidence:

```text
OpenCode 1.18.31: PASS
project opencode.jsonc resolution: PASS
Playwright MCP 0.0.81 package resolution: PASS
Playwright MCP connection: PASS
Unity MCP candidate listed disabled: PASS
Blender MCP candidate listed disabled: PASS
```

This is repository/runtime foundation evidence. It does not yet prove a model-driven browser interaction.

### M2 — Browser replacement benchmark

Current finding:

```text
@playwright/mcp 0.0.81 is the primary automation candidate.
It provides allowed/blocked origin controls and workspace file restrictions.
However, upstream explicitly states origin allow/block lists are NOT a security boundary
and do not cover redirects.
```

Therefore the custom browser implementation may only be deleted after we prove an equivalent DNS/redirect/private-network SSRF boundary. If the MCP cannot provide that itself, retain or rebuild only the smallest security-policy layer needed; do not retain a second browser automation stack merely for compatibility.

Tasks:

- [ ] pin a tested `@playwright/mcp` version
- [ ] configure Chrome path/profile behavior
- [ ] reproduce navigation/read/click/type
- [ ] reproduce screenshot artifact
- [ ] reproduce persistent/authenticated profile behavior
- [ ] reproduce network restrictions needed by this project
- [ ] run current browser acceptance scenarios
- [ ] compare with custom browser implementation

Decision:

```text
if parity or better:
    remove custom Playwright controller/tools/tests/dependency
else:
    document exact gap and keep only the missing layer
```

Real Windows host evidence:

```text
Pinned MCP package/entrypoint resolution:
- mcpforunityserver==10.2.0 -> mcp-for-unity: PASS
- mcp-for-blender==2.0.0 -> mcp-for-blender: PASS
```

This proves package resolution and CLI entrypoints on Rafael's Windows host. It does not yet prove a live Unity or Blender connection.

### M3 — Unity replacement benchmark

Tasks:

- [ ] pin tested Unity MCP release
- [ ] install in disposable Unity project
- [ ] connect from OpenCode
- [ ] reproduce project info
- [ ] reproduce scene/GameObject operations required by our scenarios
- [ ] reproduce script/edit/compile/error inspection
- [ ] reproduce tests/build or current equivalent
- [ ] reproduce Blender-export import path
- [ ] run current Unity Level 5 gate
- [ ] run Blender -> Unity path when Blender side is available

Decision:

```text
if parity or better:
    delete custom Unity controller/tools/tests
else:
    keep only demonstrated gap
```

### M4 — Blender replacement benchmark

Primary Blender candidate:

```text
ahujasid/mcp-for-blender
PyPI package: mcp-for-blender
pinned version: 2.0.0
telemetry: disabled
safe mode: enabled
```

The candidate is actively maintained, documents OpenCode configuration, supports arbitrary Blender Python execution, scene inspection, screenshots and asset workflows. Safe mode remains enabled by default because upstream states it blocks risky direct filesystem/process/network behavior while retaining normal modeling, rendering, saving and import/export operations.


Tasks:

- [ ] shortlist mature Blender MCP candidates
- [ ] pin candidate versions/commits
- [ ] compare tool coverage
- [ ] create object
- [ ] execute scripted modification
- [ ] render
- [ ] export FBX/GLTF as required
- [ ] capture diagnostics
- [ ] run real Blender gate
- [ ] compare reliability and context/tool overhead

Decision:

```text
choose exactly one implementation
delete all superseded Blender code
```

### M5 — Skills / agents migration

Tasks:

- [x] migrate current browser/Blender/Unity runtime procedures to `.opencode/skills`
- [ ] prove OpenCode advertises/loads the migrated skills in a real model run
- [ ] remove duplicate runtime skill loader
- [ ] define specialized OpenCode agents only where justified by evals
- [ ] keep development-agent instructions separate from product runtime skills

Exit:

```text
OpenCode is the only runtime skill loader
```

Smoke-agent permission ordering was inspected from OpenCode's resolved agent output in Windows CI:

```text
browser-smoke:  final * deny -> playwright_* allow
unity-smoke:    final * deny -> unityMCP_* allow
blender-smoke:  final * deny -> blenderMCP_* allow
```

This proves the agent-local restrictions are appended after inherited/global permissions and therefore take precedence under OpenCode's last-match permission model.

### M6 — Permissions and security parity

Tasks:

- [x] port conservative generic approval policy to OpenCode permissions
- [x] disable task/subagents during migration
- [x] deny direct secret files in OpenCode config
- [x] add project-local direct-path/outside-root/symlink policy plugin
- [x] add Git/ripgrep ignores for credential/key material
- [x] review destructive shell rules and keep broad shell on approval
- [ ] prove the policy plugin is loaded and blocking through real OpenCode CLI execution
- [ ] run exfiltration regression cases against real OpenCode
- [ ] remove project-local .env credential dependency from the final OpenCode path
- [ ] preserve only application-level security invariants still required
- [ ] explicitly document residual shell trust boundary

Exit:

```text
no security regression
no duplicate permission engine
```

### M7 — Sessions/context/runtime cutover

Tasks:

- [ ] validate OpenCode session continuity/resume
- [ ] validate long-task context/compaction behavior
- [ ] stop writing new custom runtime sessions
- [ ] remove custom agent loop
- [ ] remove custom context/compaction
- [ ] remove custom LLM provider/retry layer
- [ ] remove custom approval/session persistence
- [ ] remove generic Tool Registry
- [ ] remove generic filesystem/shell tools

Exit:

```text
OpenCode is the only generic runtime
```

### M8 — Remaining capability gap review

For each remaining custom capability:

```text
vision
image generation
computer use
artifacts
observability
```

run the same decision process:

```text
built-in?
official MCP?
mature MCP?
thin adapter?
only then custom
```

Delete any custom implementation that no longer has a measured reason to exist.

### M9 — Evals and CI retarget

Tasks:

- [ ] retarget evals to OpenCode/MCP behavior
- [ ] preserve Linux CI
- [ ] preserve Windows CI
- [ ] avoid paid-provider requirements in normal CI
- [ ] add deterministic integration fixtures where practical
- [ ] remove tests for deleted implementations

Exit:

```text
Level 1-4 evidence restored on new architecture
```

Local acceptance scripts now exist for:

```text
OpenCode foundation
pinned MCP package resolution
DeepSeek real-provider call
Playwright MCP -> Chrome
Unity MCP bounded create/verify/delete
Blender MCP bounded scene -> PNG artifact
combined requested-gate runner
```

These scripts are syntax-checked in Windows CI. They do not count as Level 5 until executed on Rafael's real Windows host.

### M10 — Real host Level 5

Revalidate:

```text
real provider
real Chrome/browser stack
real Blender
real Unity
permissions
failures/diagnostics
```

Exit:

```text
Level 5 restored
```

### M11 — Level 6A

Revalidate the existing real workflow:

```text
goal
-> Blender
-> export artifact
-> Unity
-> import/place/inspect
-> final evidence
```

Exit:

```text
Level 6A restored with OpenCode as runtime
```

### M12 — Level 6B

Complete:

```text
execute
-> capture visual result
-> vision inspect
-> identify issue
-> correct
-> re-run
-> verify
```

### M13 — Destructive cleanup

Only after replacement gates pass.

Delete superseded:

```text
src/harness/runtime/
src/harness/llm/
generic ToolRegistry
generic filesystem tools
generic shell tool
runtime skills loader
custom session/approval/context infrastructure
custom browser code if Playwright MCP wins
custom Unity code if Unity MCP wins
custom Blender code if selected MCP wins
dead storage/observability code
duplicate configs
dead dependencies
obsolete tests
migration-only adapters
```

Do not rename them to legacy directories.

### M14 — Residue scan

Search for old symbols and paths.

Expected runtime references: zero.

Examples:

```text
AgentLoop
ToolRegistry
LLMProvider
DeepSeekProvider
skill_list
skill_load
harness.runtime
harness.llm
config/models.yaml
config/permissions.yaml
```

Historical references in changelog/migration history are allowed.

### M15 — Final documentation and clean clone

Tasks:

- [ ] rewrite architecture to describe only final state
- [ ] rewrite setup
- [ ] update repository ownership
- [ ] update implementation status
- [ ] remove migration-only instructions
- [ ] clean-clone bootstrap
- [ ] final Linux CI
- [ ] final Windows CI
- [ ] final Level 5/6 acceptance
- [ ] merge migration branch

## 11. Replacement acceptance rule

A candidate replaces custom code only when all relevant conditions hold:

```text
functional coverage >= required scenario
reliability >= current implementation
security boundary acceptable
Windows behavior acceptable
diagnostics usable
maintenance/activity acceptable
license acceptable
setup reproducible
no unacceptable context/token explosion
no hidden dependency on a manual UI flow unless intended
```

This is a scenario-based decision, not a feature-count decision.

## 12. Cleanup rule

After a replacement wins:

```text
replacement validated
-> old implementation removed
-> old tests removed/replaced
-> old config removed
-> dependencies pruned
-> docs updated
-> residue scan
```

Do not keep fallback implementations.

## Generic runtime cutover manifest

This is the exact deletion/retention boundary for the first destructive cutover.

### Delete as generic-runtime duplication

```text
src/harness/runtime/
src/harness/llm/

src/harness/tools/base.py
src/harness/tools/registry.py
src/harness/tools/filesystem.py
src/harness/tools/shell.py
src/harness/tools/skills.py

src/harness/storage/

skills/browser-research/
skills/create-blender-prop/
skills/import-asset-to-unity/
skills/README.md

config/models.yaml
config/models.example.yaml
config/permissions.yaml
config/permissions.example.yaml
```

Delete or rewrite the corresponding legacy tests:

```text
tests/integration/test_agent_loop.py
tests/integration/test_sqlite_store.py

tests/unit/test_context.py
tests/unit/test_deepseek_provider.py
tests/unit/test_llm_instructions.py
tests/unit/test_llm_retry.py
tests/unit/test_runtime_factory.py
tests/unit/test_runtime_hooks.py
tests/unit/test_runtime_skills.py
tests/unit/test_filesystem_tools.py
tests/unit/test_shell_tool.py
tests/unit/test_tool_registry.py
tests/unit/test_verification_loop.py
```

### Rewrite, not blindly delete

```text
src/harness/cli.py
src/harness/config.py
src/harness/diagnostics.py
src/harness/evals.py

scripts/validate-local.ps1
scripts/validate-full-local.ps1
scripts/validate-level6a.ps1
```

Their final responsibility must become OpenCode/MCP acceptance and repository-specific diagnostics, not a second runtime.

### Retain until each external replacement wins its real-host benchmark

```text
src/harness/browser/
src/harness/tools/browser.py
tests/unit/test_browser_security.py
tests/unit/test_browser_tools.py
tests/integration/test_browser_runtime_real.py

src/harness/unity/
src/harness/tools/unity.py
tests/integration/test_unity_real.py

src/harness/blender/
src/harness/tools/blender.py
tests/integration/test_blender_real.py
```

The controller/tool pair for each application is deleted only after its selected MCP reproduces the existing real-host scenario with equal or better security/reliability.

### Re-evaluate separately

```text
src/harness/images/
src/harness/vision/
src/harness/tools/image.py
src/harness/tools/vision.py
src/harness/security.py
src/harness/process.py
tests/unit/test_image_vision_tools.py
tests/unit/test_visual_verifier.py
tests/unit/test_tool_risk_invariants.py
```

These are product capabilities/helpers, not automatically generic runtime duplication.

### Dependency cutover plan

After the first generic-runtime deletion:

```text
remove:
- aiosqlite      # custom session/event/approval persistence
- openai         # custom DeepSeek provider
- httpx          # no retained direct consumer expected
```

Do not remove yet:

```text
playwright         # until Playwright MCP wins the real browser benchmark
pydantic           # retained eval/domain models
pydantic-settings  # until config rewrite
python-dotenv      # until project-local legacy .env path is removed
pyyaml             # until config/eval rewrite
rich / typer       # until CLI rewrite
```

After each application MCP wins, repeat dependency pruning. No dependency is retained merely for historical compatibility.

OpenCode mock provider/runtime CI: PASS

```text
provider -> opencode run          PASS
built-in read tool loop           PASS
native skill load                 PASS
session resume                    PASS
```

This is the CI evidence that the custom AgentLoop/provider/runtime skill loader/session engine have an OpenCode replacement. Their destructive deletion is still gated on the real DeepSeek + security + browser host checks below.

### Cutover trigger

The generic-runtime deletion above is allowed when all of these are green:

```text
OpenCode mock provider/runtime CI:
- provider -> opencode run
- built-in read tool loop
- native skill load
- session resume

Rafael real host:
- OpenCode project foundation
- DeepSeek real response
- synthetic security/exfiltration probes
- Playwright MCP -> installed Chrome
```

Unity/Blender custom code may remain temporarily after that first generic-runtime cutover until their own real MCP gates pass.

## 13. Definition of done

The migration is complete when:

```text
OpenCode is the only generic agent runtime.

Every retained custom module has a documented reason to exist.

No mature replacement that passed our gates is duplicated locally.

No legacy runtime code remains.

No duplicate sessions/context/permissions/skills systems remain.

No obsolete configuration remains.

No dead runtime dependency remains.

Linux CI is green.

Windows CI is green.

Real-host Level 5 is green.

Blender -> Unity Level 6A is green.

Level 6B visual verification/correction is complete.

A clean clone can reproduce the setup.
```
