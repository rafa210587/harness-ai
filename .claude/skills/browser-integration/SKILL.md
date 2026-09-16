---
name: browser-integration
description: Use for Playwright, browser tools, authenticated profiles, web interaction, screenshots, or browser-side effects.
---

# Browser Integration

1. Prefer semantic locators and DOM/application APIs over screen coordinates.
2. Prefer Playwright/browser automation over desktop mouse/keyboard automation.
3. Classify every operation as read-only or side-effecting.
4. Navigation, reading, search, and screenshots may normally be automatic.
5. Form submission, messaging, publishing, purchases, deletion, and account changes require explicit risk handling/approval.
6. Persistent authenticated profiles must be opt-in and stored only under ignored local runtime directories.
7. Never commit cookies, tokens, credentials, profiles, traces containing secrets, or downloaded private data.
8. Produce screenshots/traces for failures when useful, but register them as artifacts rather than hiding files in ad-hoc paths.
9. Keep Playwright mechanics in `browser/`; expose stable LLM-facing contracts through `tools/browser.py`.
10. Add deterministic integration tests against local/test pages where possible. Mark external-web tests separately.

Desktop automation is the last fallback, not the default browser implementation.
