---
name: add-llm-provider
description: Use when adding or materially changing an LLM provider integration.
---

# Add LLM Provider

1. Read the normalized provider contract and DeepSeek implementation first.
2. Keep authentication/configuration provider-specific.
3. Translate normalized harness messages and tool schemas into the provider request format.
4. Translate provider responses, text, finish reasons, and tool calls back into normalized harness types.
5. Normalize provider errors and retryability at the provider boundary.
6. Do not leak provider SDK response objects into `runtime/` or `tools/`.
7. Keep streaming behavior explicit; do not introduce streaming complexity unless the runtime uses it.
8. Add tests for text output, tool calls, malformed responses, authentication/config errors, and retryable/non-retryable failures.
9. Never hard-code API keys or account-specific endpoints.
10. Update model configuration examples and docs when required.

The runtime should be able to replace the provider without changing the agent loop.
