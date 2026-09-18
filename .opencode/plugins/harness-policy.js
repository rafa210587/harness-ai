import fs from "node:fs"
import path from "node:path"

import {
  assertSafeBash,
  assertSafePath,
  assertSafeSearch,
  pathArgs,
} from "../lib/harness-policy-core.js"

export const HarnessPolicy = async ({ directory }) => {
  const projectRoot = fs.realpathSync.native(path.resolve(directory))

  return {
    "tool.execute.before": async (input, output) => {
      const tool = input.tool
      const args = output.args ?? {}

      for (const rawPath of pathArgs(tool, args)) {
        assertSafePath(tool, rawPath, projectRoot)
      }

      assertSafeSearch(tool, args)
      assertSafeBash(tool, args)
    },
  }
}
