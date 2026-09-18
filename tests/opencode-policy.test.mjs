import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"

import { HarnessPolicy } from "../.opencode/plugins/harness-policy.js"
import {
  assertSafeBash,
  assertSafePath,
  assertSafeSearch,
  isSensitive,
} from "../.opencode/lib/harness-policy-core.js"

test("sensitive path detection blocks secrets but allows env template", () => {
  assert.equal(isSensitive("C:/repo/.env"), true)
  assert.equal(isSensitive("C:/repo/.env.local"), true)
  assert.equal(isSensitive("C:/repo/private.pem"), true)
  assert.equal(isSensitive("C:/repo/id_ed25519"), true)
  assert.equal(isSensitive("C:/repo/.env.example"), false)
})

test("direct file tools cannot escape project root", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-outside-"))

  assert.throws(
    () => assertSafePath("read", path.join(outside, "file.txt"), root),
    /outside project root/,
  )
})

test("symlink escape is rejected", { skip: process.platform === "win32" }, () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-outside-"))
  const link = path.join(root, "escape")
  fs.symlinkSync(outside, link, "dir")

  assert.throws(
    () => assertSafePath("read", path.join(link, "secret.txt"), root),
    /outside project root/,
  )
})

test("grep and glob cannot explicitly target secret patterns", () => {
  assert.throws(
    () => assertSafeSearch("grep", { pattern: "TOKEN", include: ".env*" }),
    /sensitive file patterns/,
  )
  assert.throws(
    () => assertSafeSearch("glob", { pattern: "**/*.pem" }),
    /sensitive file patterns/,
  )
  assert.doesNotThrow(() =>
    assertSafeSearch("grep", { pattern: "class Foo", include: "*.py" }),
  )
})

test("shell commands explicitly referencing secret paths are blocked", () => {
  assert.throws(
    () => assertSafeBash("bash", { command: "cat .env" }),
    /sensitive path/,
  )
  assert.doesNotThrow(() =>
    assertSafeBash("bash", { command: "git status --short" }),
  )
})

test("plugin hook blocks direct sensitive read", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "harness-policy-root-"))
  const hooks = await HarnessPolicy({ directory: root })

  await assert.rejects(
    () =>
      hooks["tool.execute.before"](
        { tool: "read", sessionID: "s", callID: "c" },
        { args: { filePath: path.join(root, ".env") } },
      ),
    /sensitive path/,
  )
})
