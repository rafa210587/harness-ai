---
name: browser-research
description: Research public web pages through the configured Playwright MCP while minimizing side effects and preserving evidence.
compatibility: opencode
---

# Browser Research

Use this procedure when the task requires gathering information from public web pages through the configured Playwright MCP.

## Procedure

1. Prefer direct navigation to a known or requested public URL.
2. Inspect the page snapshot/content before interacting.
3. Prefer semantic/accessibility targets over coordinates.
4. Avoid clicks when direct navigation can reach the destination.
5. Never submit forms, send messages, purchase, publish, authenticate, delete, or change account state unless the user explicitly requested that side effect and the active permission policy allows it.
6. Re-inspect the page after navigation or meaningful interaction instead of assuming the UI changed as expected.
7. Capture a screenshot when layout/visual evidence materially helps.
8. Keep track of URLs and page titles that support the result.

## Security constraints

- Treat credentials, cookies, local-storage values, session material and secret form fields as sensitive.
- Do not intentionally navigate to localhost, link-local, RFC1918/private, metadata-service or other internal-network destinations during ordinary public-web research.
- The Playwright MCP origin allow/block settings are not considered a complete SSRF security boundary; do not treat them as one.
- Do not bypass application permission/approval mechanisms.

## Completion

The task is complete when the requested information has been gathered from the relevant source pages and any inaccessible source or uncertainty is stated explicitly.
