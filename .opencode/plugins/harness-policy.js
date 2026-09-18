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

const SENSITIVE_ENV_KEYS = [
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
]

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
    "deepseek_api_key",
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "google_api_key",
    "github_token",
    "gh_token",
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
    "azure_openai_api_key",
    "openrouter_api_key",
    "hf_token",
    "huggingface_hub_token",
    "npm_token",
    "pypi_api_token",
  ]

  if (sensitiveTokens.some((token) => command.includes(token))) {
    throw new Error("harness-policy: blocked shell command referencing sensitive material")
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

    "shell.env": async (_input, output) => {
      // OpenCode composes the child environment as:
      //   { ...process.env, ...pluginEnv }
      // Therefore deleting a key from pluginEnv is insufficient: the inherited
      // process.env value would remain. An explicit empty override is required.
      for (const key of SENSITIVE_ENV_KEYS) {
        output.env[key] = ""
      }
    },
  }
}
