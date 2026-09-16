# Changelog

## Unreleased

### Runtime

- Typed YAML + `.env` configuration and offline/online diagnostics.
- DeepSeek provider behind a provider-neutral LLM contract.
- Provider-neutral LLM timeout/retry and normalized token usage.
- Explicit single-agent tool loop with limits, cancellation, approvals, resume, context compaction, verification, and self-correction.
- Stable runtime system instruction that treats web/file/tool content as untrusted data.
- Runtime skill discovery/loading with bounded skill files.

### Tools and integrations

- Filesystem and shell tools with workspace boundaries and global tool timeouts.
- Playwright browser tools and screenshot artifacts.
- Blender background CLI/Python execution and rendering tools.
- Unity batch-mode Editor-script tools.
- ImageProvider and VisionProvider abstractions plus LLM-visible tools.
- Initial runtime skills for Blender props, Unity asset import, and browser research.

### Persistence and observability

- SQLite sessions, messages, tool calls, approvals, events, and artifacts.
- Persisted blocked-session resume and approval decisions.
- Schema version guard, indexes, and foreign-key enforcement.
- Session/event/artifact CLI inspection.
- Timing and token-usage events.

### Reliability and security

- Deterministic permission hooks and risk invariants for dangerous capabilities.
- Sensitive workspace path protection for environment files, credential directories, and private-key formats.
- Known-secret redaction at the tool boundary before model/persistence exposure.
- Resource cleanup and cancelled-session state.
- YAML eval runner with required-tool assertions, error/step/token metrics, and a real-tool smoke suite.
- Linux quality CI and Windows core acceptance CI.
- Opt-in real-runtime smoke tests for Chromium, Blender, and Unity.
- Windows `scripts/validate-local.ps1` acceptance workflow.

### Development workflow

- Concise spec/plan/task workflow with temporary `.work/` artifacts.
- Coding-agent skills for implementation, review, simplification, security, and integrations.
- Claude Code hooks and Cursor/shared agent rules.
- `IMPLEMENTATION_STATUS.md` separates implemented/CI evidence from real-machine acceptance.
