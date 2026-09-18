param(
    [switch]$EnforceResidue
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== OpenCode cutover readiness ==="

$requiredFiles = @(
    "opencode.jsonc",
    ".opencode-version",
    ".opencode/plugins/harness-policy.js",
    ".opencode/agents/browser-smoke.md",
    ".opencode/agents/unity-smoke.md",
    ".opencode/agents/blender-smoke.md",
    ".opencode/agents/security-smoke.md",
    ".opencode/skills/browser-research/SKILL.md",
    ".opencode/skills/create-blender-prop/SKILL.md",
    ".opencode/skills/import-asset-to-unity/SKILL.md",
    "scripts/validate-opencode.ps1",
    "scripts/validate-opencode-deepseek.ps1",
    "scripts/validate-opencode-browser.ps1",
    "scripts/validate-opencode-security.ps1",
    "scripts/validate-opencode-unity.ps1",
    "scripts/validate-opencode-blender.ps1"
)

$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$missing = @()
foreach ($relative in $requiredFiles) {
    if (-not (Test-Path (Join-Path $repoRoot $relative))) {
        $missing += $relative
    }
}

if ($missing.Count -gt 0) {
    throw "Missing OpenCode migration artifacts: $($missing -join ', ')"
}

Write-Host "[ok] Required OpenCode migration artifacts exist."

if ($EnforceResidue) {
    & (Join-Path $scriptRoot "scan-opencode-cutover-residue.ps1") -Enforce
}
else {
    & (Join-Path $scriptRoot "scan-opencode-cutover-residue.ps1")
}

Write-Host ""
Write-Host "Readiness note:"
Write-Host "  Repository artifacts are present."
Write-Host "  Destructive cutover remains blocked until real DeepSeek/browser/Unity/Blender/security parity gates pass."
