import fs from "node:fs"
import path from "node:path"

const SENSITIVE_BASENAMES = new Set([
  ".env",
  "id_rsa",
  "id_dsa",
  "id_ecdsa",
  "id_ed25519",
])

const SENSITIVE_EXTENSIONS = new Set([
  ".pem",
  ".key",
  ".p12",
  ".pfx",
])

const SENSITIVE_SEGMENTS = new Set([
  ".ssh",
  "browser-profile",
])

function canonicalize(candidate, root) {
  const absolute = path.resolve(root, candidate)
  let probe = absolute

  while (!fs.existsSync(probe)) {
    const parent = path.dirname(probe)
    if (parent === probe) break
    probe = parent
  }

  let realProbe = probe
  try {
    realProbe = fs.realpathSync.native(probe)
  } catch {
    realProbe = path.resolve(probe)
  }

  const suffix = path.relative(probe, absolute)
  return path.resolve(realProbe, suffix)
}

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate)
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))
}

function isSensitive(candidate) {
  const normalized = candidate.replaceAll("\\", "/").toLowerCase()
  const basename = path.posix.basename(normalized)

  if (basename === ".env.example") return false
  if (SENSITIVE_BASENAMES.has(basename)) return true
  if (basename.startsWith(".env.")) return true
  if (SENSITIVE_EXTENSIONS.has(path.posix.extname(basename))) return true

  const segments = normalized.split("/").filter(Boolean)
  return segments.some((segment) => SENSITIVE_SEGMENTS.has(segment))
}

function pathArgs(tool, args) {
  switch (tool) {
    case "read":
    case "write":
    case "edit":
      return [args?.filePath]
    case "patch":
      return [args?.filePath, args?.path]
    case "list":
    case "glob":
    case "grep":
      return [args?.path]
    default:
      return []
  }
}

function assertSafePath(tool, rawPath, root) {
  if (typeof rawPath !== "string" || rawPath.trim() === "") return

  const canonical = canonicalize(rawPath, root)

  if (!isWithin(root, canonical)) {
    throw new Error(
      `harness-policy: blocked ${tool} outside project root: ${rawPath}`,
    )
  }

  if (isSensitive(canonical)) {
    throw new Error(
      `harness-policy: blocked ${tool} access to sensitive path: ${rawPath}`,
    )
  }
}

function assertSafeSearch(tool, args) {
  if (tool !== "glob" && tool !== "grep") return

  const include = typeof args?.include === "string" ? args.include : ""
  const pattern = typeof args?.pattern === "string" ? args.pattern : ""
  const combined = `${include} ${pattern}`.toLowerCase()

  if (
    combined.includes(".env") ||
    combined.includes(".pem") ||
    combined.includes(".key") ||
    combined.includes("id_rsa") ||
    combined.includes("id_ed25519")
  ) {
    throw new Error(
      `harness-policy: blocked ${tool} query targeting sensitive file patterns`,
    )
  }
}

function assertSafeBash(tool, args) {
  if (tool !== "bash" && tool !== "shell") return

  const command = typeof args?.command === "string" ? args.command.toLowerCase() : ""
  if (!command) return

  const sensitiveTokens = [
    ".env",
    ".pem",
    ".key",
    "id_rsa",
    "id_ed25519",
    ".ssh",
    "browser-profile",
  ]

  if (sensitiveTokens.some((token) => command.includes(token))) {
    throw new Error("harness-policy: blocked shell command referencing a sensitive path")
  }
}

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

export const __test = {
  canonicalize,
  isWithin,
  isSensitive,
  pathArgs,
  assertSafePath,
  assertSafeSearch,
  assertSafeBash,
}
