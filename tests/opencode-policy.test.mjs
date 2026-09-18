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

test("shell.env overrides inherited provider secrets while preserving safe env", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await hooksFor(root)
  const output = {
    env: {
      PATH: "safe",
      HARNESS_SAFE_ENV: "HARNESS_SAFE_ENV_OK",
    },
  }

  await hooks["shell.env"]({ cwd: root }, output)

  for (const key of [
    "DEEPSEEK_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AZURE_OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "NPM_TOKEN",
    "PYPI_API_TOKEN",
  ]) {
    assert.equal(output.env[key], "", key + " must be explicitly overridden")
  }

  assert.equal(output.env.PATH, "safe")
  assert.equal(output.env.HARNESS_SAFE_ENV, "HARNESS_SAFE_ENV_OK")
})
