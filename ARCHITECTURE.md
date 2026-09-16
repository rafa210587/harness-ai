# Local AI Harness — Architecture

> Status: Initial Architecture / MVP  
> Goal: build a small, local, functional AI harness capable of reasoning with DeepSeek and operating real tools on the user's computer, including shell, filesystem, browser, Blender and Unity.

---

# 1. Vision

The project is a **local AI agent runtime**.

Its purpose is not to build another general-purpose chatbot.

The harness must allow an LLM to receive a goal, reason about it, execute tools on the local computer, inspect the result, correct itself and continue until the task is complete or human approval is required.

Example:

```text
User:
"Create a medieval barrel in Blender, export it and put it in my Unity project."

Harness:
1. understands the task
2. inspects the Unity project
3. opens/controls Blender
4. creates or modifies the model
5. renders a preview
6. analyzes the preview
7. exports FBX
8. copies/imports it into Unity
9. opens the Unity scene
10. places the object
11. captures the result
12. verifies whether the result is acceptable
13. fixes problems if necessary
```

The system should eventually be capable of performing long multi-application workflows.

The MVP, however, should remain deliberately small.

---

# 2. Core Principle

Separate:

```text
LLM reasoning

from

computer capabilities
```

DeepSeek does not need native knowledge of Blender, Unity, Windows or Chrome.

The harness exposes those capabilities as tools.

```text
              ┌─────────────────┐
              │    DeepSeek     │
              │                 │
              │ Planner / Agent │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │     Harness     │
              │                 │
              │ Agent Runtime   │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             │     Tool Layer    │
             └─────────┬─────────┘
                       │
    ┌──────────┬───────┼───────┬─────────┬─────────┐
    ▼          ▼       ▼       ▼         ▼         ▼
 Filesystem   Shell   Browser Blender   Unity    Images
```

The LLM decides **what to do**.

The harness decides **how to safely execute it**.

---

# 3. Main Architectural Decisions

## ADR-001 — Build our own harness

Decision:

```text
Build a small custom harness.
```

Do not use OpenCode as the core runtime.

OpenCode can still be studied and reused conceptually.

Reason:

The target system needs capabilities beyond coding:

- browser control
- Blender control
- Unity control
- image generation
- screenshots
- vision
- human approvals
- filesystem operations
- shell operations
- potentially desktop automation

Using a coding harness as the central abstraction would eventually require working around its assumptions.

Our runtime should treat coding as only one capability among many.

---

# 4. ADR-002 — DeepSeek as Primary Executor

DeepSeek will initially serve as the main reasoning/execution model.

Architecture:

```text
User
 ↓
DeepSeek
 ↓
Tool calls
 ↓
Harness
 ↓
Computer
```

The harness must not depend directly on DeepSeek-specific APIs internally.

Create a generic interface:

```python
class LLMProvider:
    async def complete(
        self,
        messages,
        tools=None,
        response_schema=None,
    ):
        ...
```

Implementation:

```text
LLMProvider
   │
   ├── DeepSeekProvider
   │
   ├── OpenAIProvider         future
   │
   ├── AnthropicProvider      future
   │
   └── LocalModelProvider     future
```

This allows model replacement without changing the agent runtime.

---

# 5. ADR-003 — No Multi-Agent Architecture Initially

The MVP should NOT begin with:

```text
Planner Agent
Executor Agent
Reviewer Agent
Research Agent
Unity Agent
Blender Agent
Browser Agent
...
```

That adds complexity without proving that the fundamental runtime works.

Initial design:

```text
ONE AGENT
   │
   ├── reasoning
   ├── tool selection
   ├── execution
   └── verification
```

Later:

```text
Orchestrator
     │
     ├── Coding Agent
     ├── Blender Agent
     ├── Unity Agent
     └── Research Agent
```

Only introduce specialized agents when evals show they improve outcomes.

---

# 6. ADR-004 — Simple Agent Loop

Do not introduce LangGraph or Temporal initially.

Use a simple explicit loop.

Conceptually:

```python
while not finished:

    context = build_context()

    response = await llm.complete(
        context,
        tools=tool_registry.schemas()
    )

    if response.tool_call:
        result = await tool_registry.execute(response.tool_call)
        memory.append(result)
        continue

    if response.finished:
        return response.output
```

Real implementation will include:

```text
maximum steps
timeouts
approval gates
retry limits
error handling
logging
context compaction
```

This loop should be readable in one file.

Target:

```text
runtime/agent_loop.py
```

approximately:

```text
200-400 lines
```

not a framework.

---

# 7. Programming Language

Use:

```text
Python 3.12+
```

Reasons:

- excellent AI ecosystem
- excellent Playwright support
- Blender uses Python natively
- easy subprocess control
- simple JSON handling
- simple async runtime
- strong image-processing ecosystem
- easy future integration with ML models

Avoid mixing TypeScript and Python in the initial runtime.

---

# 8. Execution Environment

Primary environment:

```text
Windows host
```

The harness should be able to operate:

```text
Windows
├── Blender
├── Unity
├── Chrome / Chromium
├── filesystem
└── applications

WSL
└── optional development/runtime environment
```

For controlling Windows applications, running the primary harness directly on Windows is simpler than hiding it inside WSL.

WSL may later be exposed as a shell tool.

Example:

```text
shell.windows()
shell.wsl()
```

---

# 9. Repository Structure

Initial repository:

```text
ai-harness/
│
├── README.md
├── ARCHITECTURE.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── config/
│   ├── harness.yaml
│   ├── permissions.yaml
│   └── models.yaml
│
├── src/
│   └── harness/
│
│       ├── cli.py
│       │
│       ├── runtime/
│       │   ├── agent.py
│       │   ├── agent_loop.py
│       │   ├── context.py
│       │   ├── session.py
│       │   └── approvals.py
│       │
│       ├── llm/
│       │   ├── base.py
│       │   └── deepseek.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── base.py
│       │   │
│       │   ├── filesystem.py
│       │   ├── shell.py
│       │   ├── browser.py
│       │   ├── blender.py
│       │   ├── unity.py
│       │   ├── image.py
│       │   └── screenshot.py
│       │
│       ├── browser/
│       │   └── playwright_controller.py
│       │
│       ├── blender/
│       │   ├── controller.py
│       │   └── scripts/
│       │
│       ├── unity/
│       │   ├── controller.py
│       │   └── editor/
│       │
│       ├── images/
│       │   ├── base.py
│       │   ├── interactive_chatgpt.py
│       │   └── providers/
│       │
│       ├── storage/
│       │   ├── database.py
│       │   └── artifacts.py
│       │
│       └── observability/
│           ├── events.py
│           └── logger.py
│
├── workspace/
│
├── data/
│   └── harness.db
│
└── tests/
```

---

# 10. CLI

The first interface should be a CLI.

Example:

```bash
harness run "Open my Unity project and inspect the current scene."
```

Interactive:

```bash
harness
```

Result:

```text
Harness > Create a barrel in Blender and import it into Unity.

Agent:
I'll inspect the current Unity project first.

Tool: filesystem.list
Tool: unity.project_info
Tool: blender.execute
...
```

Other commands:

```bash
harness sessions

harness resume <session-id>

harness tools

harness config

harness doctor
```

`harness doctor` should validate:

```text
DeepSeek API
Python
Playwright
Chrome
Blender
Unity
workspace permissions
database
```

---

# 11. Tool Contract

Every tool should follow the same conceptual contract.

```python
class Tool:
    name: str
    description: str

    def schema(self) -> dict:
        ...

    async def execute(self, arguments: dict) -> ToolResult:
        ...
```

Result:

```python
class ToolResult:
    success: bool
    output: str | dict
    artifacts: list[str]
    error: str | None
```

Example tool:

```text
filesystem.read
```

Input:

```json
{
  "path": "Assets/Scripts/Player.cs"
}
```

Output:

```json
{
  "success": true,
  "content": "..."
}
```

---

# 12. Tool Registry

The agent should never directly know implementation classes.

Use:

```text
ToolRegistry
```

Example:

```python
registry.register(FilesystemReadTool())
registry.register(FilesystemWriteTool())
registry.register(ShellTool())
registry.register(BrowserTool())
registry.register(BlenderTool())
registry.register(UnityTool())
```

Then:

```python
registry.execute(
    "filesystem.read",
    arguments
)
```

This becomes an important architectural boundary.

Later MCP tools can simply be mounted into the same registry.

---

# 13. Filesystem Tools

Initial filesystem tools:

```text
filesystem.read
filesystem.write
filesystem.patch
filesystem.list
filesystem.search
filesystem.mkdir
filesystem.move
filesystem.copy
```

Dangerous operations require special treatment:

```text
filesystem.delete
```

Should default to human approval.

Workspace boundaries must be configurable.

Example:

```yaml
filesystem:
  allowed_roots:
    - "C:/Projects"
    - "D:/Games"
```

The agent should not automatically gain unrestricted filesystem access.

---

# 14. Shell Tool

Initial API:

```text
shell.run
```

Arguments:

```json
{
  "command": "git status",
  "cwd": "C:/Projects/MyGame",
  "timeout_seconds": 60
}
```

Return:

```json
{
  "exit_code": 0,
  "stdout": "...",
  "stderr": "..."
}
```

Possible future split:

```text
shell.windows
shell.powershell
shell.wsl
```

MVP can use one generic subprocess tool.

---

# 15. Browser Tool

Use:

```text
Playwright
```

Browser controller should expose semantic operations.

Not:

```text
mouse_move(426, 381)
```

Prefer:

```text
browser.open
browser.navigate
browser.click
browser.type
browser.screenshot
browser.read_page
browser.wait
```

Example:

```json
{
  "tool": "browser.navigate",
  "arguments": {
    "url": "https://..."
  }
}
```

The browser should use a persistent profile when explicitly configured.

Example:

```text
data/browser-profile/
```

This allows sessions to remain authenticated.

---

# 16. Browser Security Boundary

Browser automation is extremely powerful.

The harness should differentiate:

```text
SAFE

read web page
navigate
search
capture screenshot
```

from:

```text
SIDE EFFECT

submit form
purchase
delete
send message
publish content
change account configuration
```

Side-effect actions should require approval by default.

---

# 17. ChatGPT Browser Integration

ChatGPT Web should NOT be treated as a normal autonomous API.

If used through the browser, model it as:

```text
InteractiveImageProvider
```

Flow:

```text
Agent
 ↓
builds image prompt
 ↓
opens ChatGPT
 ↓
fills prompt
 ↓
requests human confirmation
 ↓
user triggers/confirms operation
 ↓
image becomes available
 ↓
harness imports artifact
```

This allows the existing ChatGPT subscription to participate in the workflow without designing the system around browser scraping.

For fully autonomous image generation, use an API-based image provider.

---

# 18. Image Provider Abstraction

Interface:

```python
class ImageProvider:

    async def generate(
        self,
        prompt: str,
        references: list[str] | None = None,
    ) -> ImageResult:
        ...
```

Potential implementations:

```text
ImageProvider
│
├── ChatGPTInteractiveProvider
├── OpenAIImageProvider
├── GeminiImageProvider
├── ComfyUIProvider
└── OtherProvider
```

The agent calls:

```text
image.generate
```

It does not need to know which provider is active.

Configuration:

```yaml
images:
  provider: chatgpt_interactive
```

or:

```yaml
images:
  provider: openai
```

---

# 19. Blender Integration

Blender is particularly suitable because it exposes Python.

Avoid screen clicking where possible.

Primary integration:

```text
Harness
 ↓
BlenderController
 ↓
Python commands/scripts
 ↓
Blender
```

Initial capabilities:

```text
blender.create_scene
blender.execute_python
blender.open_file
blender.save_file
blender.render
blender.export_fbx
blender.export_gltf
```

Example:

```json
{
  "tool": "blender.execute_python",
  "arguments": {
    "script": "..."
  }
}
```

The controller should save generated scripts into:

```text
workspace/blender/
```

This makes actions inspectable and reproducible.

---

# 20. Blender MVP Strategy

The simplest first implementation can invoke Blender through CLI:

```bash
blender file.blend --background --python task.py
```

This gives us reliable automation immediately.

It supports:

```text
model creation
scene modification
rendering
exports
asset processing
```

Later we can support interactive Blender control via:

```text
local socket
WebSocket
Blender addon
```

That allows controlling an already-open Blender instance.

Do not build the addon first.

---

# 21. Unity Integration

Unity should follow a similar principle.

Avoid desktop clicking whenever Unity exposes programmatic alternatives.

Architecture:

```text
Harness
 ↓
UnityController
 ↓
Unity Editor Bridge
 ↓
Unity Editor API
```

Capabilities eventually:

```text
unity.project_info
unity.refresh_assets
unity.import_asset
unity.open_scene
unity.create_game_object
unity.add_component
unity.set_property
unity.enter_play_mode
unity.exit_play_mode
unity.capture_game_view
unity.read_console
unity.execute_editor_script
```

---

# 22. Unity MVP Strategy

Initial integration should use:

```text
Unity command line
+
Editor scripts
+
filesystem
```

The harness can generate C# editor scripts when needed.

Example:

```text
Assets/
└── Editor/
    └── HarnessBridge.cs
```

Later introduce a persistent local bridge.

Example:

```text
Unity Editor
     │
 localhost
     │
Harness
```

Possible protocol:

```text
HTTP
WebSocket
JSON-RPC
```

Recommendation for later:

```text
WebSocket or HTTP localhost bridge
```

Do not build it until CLI/editor-script integration becomes limiting.

---

# 23. Screenshots and Vision

The agent must be able to inspect visual outputs.

Common artifact:

```text
Screenshot
```

Sources:

```text
Browser
Blender render
Unity Game View
Windows screen
```

Generic interface:

```text
screenshot.capture
```

Artifacts stored under:

```text
workspace/artifacts/
```

Example:

```text
workspace/artifacts/
  2026-09-15/
    unity-game-view-001.png
    blender-render-002.png
```

Vision-capable models can later analyze those outputs.

DeepSeek model selection may differ depending on whether vision is required.

Therefore vision must be a separate provider capability.

---

# 24. Artifact Model

Everything produced should be represented as an artifact.

Examples:

```text
image
screenshot
FBX
GLTF
blend
Unity scene
source file
log
report
```

Metadata:

```json
{
  "id": "artifact_01",
  "type": "image",
  "path": "...",
  "created_by": "blender.render",
  "session_id": "...",
  "timestamp": "..."
}
```

This gives the agent a consistent way to reference outputs.

---

# 25. Session State

Each user task becomes a session.

Example:

```text
Session
├── task
├── messages
├── tool calls
├── tool results
├── artifacts
├── approvals
└── status
```

Status:

```text
RUNNING
WAITING_APPROVAL
COMPLETED
FAILED
CANCELLED
```

---

# 26. Persistence

Use:

```text
SQLite
```

Do not introduce PostgreSQL.

Initial tables:

```text
sessions
messages
tool_calls
artifacts
approvals
events
```

Database:

```text
data/harness.db
```

SQLite is sufficient until we prove otherwise.

---

# 27. Context Management

The agent should not continually resend the entire history.

Maintain:

```text
system context
task
working summary
recent messages
relevant artifacts
recent tool outputs
```

Concept:

```text
Full session
      │
      ▼
Context Builder
      │
      ├── stable instructions
      ├── current goal
      ├── working memory
      ├── last N events
      └── relevant artifacts
```

Initially context compression can simply ask the LLM to create a working summary when token usage exceeds a threshold.

No vector database is needed for MVP.

---

# 28. Memory

Separate:

```text
Session Memory
```

from:

```text
Long-Term Memory
```

MVP only needs session memory.

Later long-term memory can store:

```text
project conventions
preferred workflows
Unity project structure
Blender asset conventions
coding preferences
frequently used directories
```

Do not introduce RAG yet.

---

# 29. Human Approval

Some actions should require explicit approval.

Categories:

### Read

Usually automatic.

```text
read file
inspect project
read webpage
capture screenshot
```

### Write

Configurable.

```text
modify source
create asset
modify Unity scene
modify Blender scene
```

### Dangerous

Approval required.

```text
delete files
git push
install software
execute elevated shell
send messages
purchase
publish
modify accounts
```

Tool metadata:

```python
risk = "read" | "write" | "dangerous"
```

---

# 30. Permission Configuration

Example:

```yaml
permissions:

  filesystem:
    read: auto
    write: auto
    delete: approval

  shell:
    normal: auto
    elevated: approval

  browser:
    read: auto
    submit: approval

  git:
    commit: auto
    push: approval
```

This allows the system to become progressively more autonomous.

---

# 31. Observability

Every significant event should be recorded.

Event types:

```text
SESSION_STARTED

LLM_REQUEST
LLM_RESPONSE

TOOL_STARTED
TOOL_COMPLETED
TOOL_FAILED

APPROVAL_REQUESTED
APPROVAL_GRANTED

ARTIFACT_CREATED

SESSION_COMPLETED
SESSION_FAILED
```

Initially:

```text
structured JSON logs
+
SQLite events
```

Later integration:

```text
Langfuse
OpenTelemetry
```

No external observability dependency is needed initially.

---

# 32. Error Handling

Every tool failure should become information available to the agent.

Example:

```text
Tool:
unity.enter_play_mode

Result:
FAILED

Reason:
Compilation errors detected.

Compiler output:
Assets/Scripts/Player.cs(47,18): ...
```

The agent should then be capable of:

```text
inspect
fix
retry
```

Do not hide tool errors behind generic exceptions.

---

# 33. Retry Strategy

Retry must not be global and blind.

Tool result should communicate:

```text
retryable
```

Example:

```json
{
  "success": false,
  "retryable": true,
  "error": "Unity editor still compiling."
}
```

Agent can then wait and retry.

---

# 34. Task Limits

Prevent infinite loops.

Default configuration:

```yaml
agent:
  max_steps: 50
  max_consecutive_errors: 5
  max_tool_runtime_seconds: 300
```

Agent can return:

```text
BLOCKED
```

with the reason.

---

# 35. Configuration

`config/models.yaml`

```yaml
default_model:
  provider: deepseek
  model: ${DEEPSEEK_MODEL}

providers:

  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    base_url: ${DEEPSEEK_BASE_URL}
```

`config/harness.yaml`

```yaml
workspace:
  root: "C:/AIHarness/workspace"

browser:
  persistent_profile: true

database:
  path: "./data/harness.db"

agent:
  max_steps: 50
```

Secrets belong in:

```text
.env
```

Never commit secrets.

---

# 36. Dependency Philosophy

Keep dependencies small.

Likely initial dependencies:

```text
httpx
pydantic
pyyaml
playwright
rich
typer
aiosqlite
```

Potentially:

```text
Pillow
```

Avoid adding:

```text
LangChain
LangGraph
Temporal
Redis
PostgreSQL
Qdrant
Kafka
Celery
```

until a concrete requirement exists.

---

# 37. MCP

MCP should be supported conceptually, but not be the internal architecture.

Correct relationship:

```text
Harness Tool Registry
      │
      ├── Native tools
      │
      └── MCP Adapter
             │
             └── external MCP servers
```

Not:

```text
Harness == MCP
```

This lets MCP become another source of tools.

---

# 38. Computer Use

Eventually we may need real desktop control.

Possible capabilities:

```text
computer.screenshot
computer.click
computer.type
computer.hotkey
computer.window_list
computer.focus_window
```

But this is a fallback.

Priority order should be:

```text
1. native API
2. application scripting
3. CLI
4. browser semantic automation
5. desktop mouse/keyboard automation
```

GUI clicking is the least reliable integration and should only be used when necessary.

---

# 39. Example End-to-End Flow

User:

```text
Create a wooden crate for my game and put it into the current Unity scene.
```

Agent:

```text
1. filesystem.inspect_project

2. unity.project_info

3. blender.execute_python
   creates crate

4. blender.render
   returns preview.png

5. vision.inspect
   checks asset

6. blender.export_fbx

7. filesystem.copy
   moves FBX into Assets/

8. unity.refresh_assets

9. unity.create_game_object

10. unity.capture_game_view

11. vision.inspect

12. final response
```

That is the target experience.

---

# 40. MVP Definition

The MVP is complete when this works reliably:

```text
User
 ↓
CLI
 ↓
DeepSeek
 ↓
Agent Loop
 ↓
Tool calls
 ↓
Local computer
```

with these tools:

```text
filesystem
shell
browser
Blender
Unity
```

Not every feature needs to be sophisticated.

Each only needs one useful vertical slice.

---

# 41. MVP Phase 1 — Runtime

Implement:

```text
CLI
LLM provider interface
DeepSeek provider
Agent loop
Tool registry
SQLite session persistence
logging
```

Test:

```text
harness run "List the files in this directory."
```

---

# 42. MVP Phase 2 — Filesystem + Shell

Implement:

```text
filesystem.read
filesystem.write
filesystem.list
filesystem.search

shell.run
```

Target:

```text
Agent can inspect and modify a normal software project.
```

---

# 43. MVP Phase 3 — Browser

Add Playwright.

Implement:

```text
browser.open
browser.navigate
browser.read
browser.click
browser.type
browser.screenshot
```

Target:

```text
Agent can perform research and interact with web applications.
```

---

# 44. MVP Phase 4 — Blender

Implement:

```text
blender.execute_python
blender.render
blender.export
```

Initial implementation:

```text
Blender CLI/background mode
```

Target:

```text
Agent creates a basic Blender object and renders it.
```

---

# 45. MVP Phase 5 — Unity

Implement:

```text
unity.project_info
unity.refresh
unity.execute_editor_script
unity.capture
```

Target:

```text
Agent imports the Blender asset into Unity.
```

At this point the first major end-to-end demo exists.

---

# 46. MVP Phase 6 — Images

Implement:

```text
image.generate
```

Initial providers:

```text
ChatGPTInteractiveProvider
```

and eventually one fully autonomous API provider.

Target:

```text
Agent can request textures, concepts or references.
```

---

# 47. MVP Phase 7 — Verification Loop

Add:

```text
screenshots
visual verification
retry loop
artifact comparison
```

Then the runtime becomes capable of:

```text
do
observe
evaluate
correct
repeat
```

This is the point where the harness starts behaving like a genuine autonomous worker rather than a tool caller.

---

# 48. What We Are Explicitly NOT Building Yet

Do not initially build:

```text
distributed workers
Kubernetes
multi-agent orchestration
Temporal
LangGraph
vector database
knowledge graph
remote execution
complex scheduler
multi-user authentication
web frontend
mobile frontend
plugin marketplace
custom protocol
custom model router
advanced RAG
```

The first version runs on one machine for one user.

---

# 49. Open Decisions

There are only a few relevant open decisions.

## 49.1 DeepSeek Model

The architecture does not depend on a particular DeepSeek model.

Configuration should determine it.

```yaml
model: ${DEEPSEEK_MODEL}
```

We can benchmark models later.

---

## 49.2 Autonomous Image Provider

For the first version:

```text
ChatGPT Web
+
human-in-the-loop
```

is enough.

For unattended runs we will eventually need an API-based provider.

This does not block the MVP.

---

## 49.3 Unity Persistent Bridge

Two possibilities:

### A — Editor scripts / command line

Simpler.

Use for MVP.

### B — Persistent Unity plugin

More powerful.

Implement later if required.

Decision:

```text
A first.
```

---

## 49.4 Blender Persistent Bridge

Same reasoning.

Start with:

```text
Blender CLI + Python
```

Later:

```text
Blender addon + local connection
```

---

# 50. Current Decisions Summary

| Area | Decision |
|---|---|
| Runtime | Custom |
| Language | Python 3.12+ |
| Interface | CLI |
| Main LLM | DeepSeek |
| Agent architecture | Single agent initially |
| Orchestration | Simple internal loop |
| Persistence | SQLite |
| Browser | Playwright |
| Browser profile | Persistent, configurable |
| Blender | Python + Blender CLI first |
| Unity | Editor scripts + CLI first |
| Images | Provider abstraction |
| ChatGPT Web | Interactive/human-in-loop |
| Autonomous image generation | API provider later |
| MCP | Optional adapter |
| LangGraph | Not initially |
| Temporal | Not initially |
| RAG | Not initially |
| Vector DB | Not initially |
| Observability | JSON + SQLite |
| GUI automation | Fallback only |

---

# 51. Target Architecture

```text
                      USER
                       │
                       ▼
                 ┌───────────┐
                 │    CLI    │
                 └─────┬─────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Agent Runtime   │
              │                  │
              │  Session         │
              │  Context         │
              │  Agent Loop      │
              │  Approvals       │
              └────────┬─────────┘
                       │
            ┌──────────▼──────────┐
            │    LLM Provider     │
            │                     │
            │      DeepSeek       │
            └──────────┬──────────┘
                       │
                       ▼
               ┌───────────────┐
               │ Tool Registry │
               └───────┬───────┘
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
  Filesystem          Shell           Browser
                                       │
                                  Playwright
                                       │
                                   Chromium

       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
    Blender           Unity           Images
       │               │                │
 Blender Python    Editor API       Provider
 Blender CLI       CLI/scripts      abstraction

                                         │
                         ┌───────────────┴───────────────┐
                         │                               │
                         ▼                               ▼
                  ChatGPT Interactive               API Provider
                   human approval                    autonomous
```

---

# 52. Design Rule

Every new capability should answer:

```text
Can this be implemented as a Tool?
```

If yes:

```text
implement it as a Tool.
```

The core agent runtime should remain small.

This is the main design constraint of the project.

---

# 53. First Technical Goal

The first vertical slice should be:

```text
User:
"Create a cube in Blender and render it."

DeepSeek
 ↓
blender.execute_python
 ↓
Blender
 ↓
render.png
 ↓
artifact returned to the agent
 ↓
Agent reports completion
```

Then:

```text
"Import that cube into Unity."
```

Once both work, we join the flows.

That proves the architecture before we invest in advanced orchestration.

---

# 54. Definition of Success

The project succeeds if the harness becomes capable of handling tasks like:

```text
"Look at this Unity game and improve this environment."

"Create the missing prop in Blender."

"Search for a reference image."

"Generate a texture."

"Modify the asset."

"Import it."

"Run the game."

"Look at the result."

"Fix what is wrong."
```

without needing custom orchestration code for each task.

The intelligence lives in the model.

The harness provides:

```text
tools
state
permissions
observation
execution
```

That is the system.
