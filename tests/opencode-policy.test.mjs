import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"

import * as policyPluginModule from "../.opencode/plugins/harness-policy.js"
import { HarnessPolicy } from "../.opencode/plugins/harness-policy.js"

async function hooksFor(root) {
  return HarnessPolicy({ directory: root })
}

test("plugin module exports only plugin functions", () => {
  for (const [name, value] of Object.entries(policyPluginModule)) {
    assert.equal(
      typeof value,
      "function",
      `plugin export ${name} must be a function for OpenCode 1.18.31 legacy loader`,
    )
  }
})

test("direct sensitive read is blocked but env template is allowed", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await hooksFor(root)

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "read", sessionID: "s", callID: "c" },
        { args: { filePath: path.join(root, ".env.local") } },
      ),
    /sensitive path/,
  )

  await assert.doesNotReject(() =>
    hooks["tool.execute.before"](
      { tool: "read", sessionID: "s", callID: "c2" },
      { args: { filePath: path.join(root, ".env.example") } },
    ),
  )
})

test("direct file tools cannot escape project root", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-outside-"))
  const hooks = await hooksFor(root)

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "read", sessionID: "s", callID: "c" },
        { args: { filePath: path.join(outside, "file.txt") } },
      ),
    /outside project root/,
  )
})

test("targeted grep/glob secret patterns are blocked", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await hooksFor(root)

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "grep", sessionID: "s", callID: "c" },
        { args: { path: root, pattern: "TOKEN", include: ".env*" } },
      ),
    /sensitive file patterns/,
  )

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "glob", sessionID: "s", callID: "c2" },
        { args: { path: root, pattern: "**/*.pem" } },
      ),
    /sensitive file patterns/,
  )
})

test("shell references to secret paths or env vars are blocked", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await hooksFor(root)

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "bash", sessionID: "s", callID: "c" },
        { args: { command: "cat .env" } },
      ),
    /sensitive material/,
  )

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "bash", sessionID: "s", callID: "c2" },
        { args: { command: "echo $env:DEEPSEEK_API_KEY" } },
      ),
    /sensitive material/,
  )
})

test("shell.env strips common provider API keys", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await hooksFor(root)
  const output = {
    env: {
      DEEPSEEK_API_KEY: "synthetic",
      OPENAI_API_KEY: "synthetic",
      PATH: "safe",
    },
  }

  await hooks["shell.env"]({ cwd: root }, output)

  assert.equal(output.env.DEEPSEEK_API_KEY, undefined)
  assert.equal(output.env.OPENAI_API_KEY, undefined)
  assert.equal(output.env.PATH, "safe")
})
