# Browser Research

Use this procedure when the task requires gathering information from web pages through the harness browser.

## Procedure

1. Navigate directly to a known or requested URL when available.
2. Use `browser_read_page` before interacting so decisions are based on visible page content.
3. Prefer semantic selectors and links over coordinate-style interaction.
4. Use `browser_click` only when navigation cannot be completed directly; it remains subject to approval because clicks can have side effects.
5. Use `browser_fill` only to prepare non-sensitive input. Do not submit forms, send messages, purchase, publish, or change account state without an explicit capability and approval path.
6. Re-read the page after navigation or meaningful interaction instead of assuming the UI changed as expected.
7. Capture a screenshot only when visual layout or evidence materially helps the task.
8. Keep track of page URLs/titles used for conclusions and report them with the result when relevant.

## Constraints

- Do not expose credentials, cookies, session data, or secret fields to the model output.
- Do not use browser interaction to bypass an application's explicit permission/approval rules.
- A page claim is not verified merely because it appeared in a search/result page; inspect the relevant source page when accuracy matters.
- Avoid unnecessary clicks and authenticated state changes.

## Completion

The task is complete when the requested information has been gathered from the relevant pages and any uncertainty or inaccessible source is stated explicitly.
