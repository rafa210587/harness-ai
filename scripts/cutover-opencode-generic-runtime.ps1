param(
    [switch]$Execute,
    [switch]$ConfirmCutover
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path

$deletePaths = @(
    "src/harness/runtime",
    "src/harness/llm",
    "src/harness/tools/base.py",
    "src/harness/tools/registry.py",
    "src/harness/tools/filesystem.py",
    "src/harness/tools/shell.py",
    "src/harness/tools/skills.py",
    "src/harness/storage",
    "skills/browser-research",
    "skills/create-blender-prop",
    "skills/import-asset-to-unity",
    "skills/README.md",
    "config/models.yaml",
    "config/models.example.yaml",
    "config/permissions.yaml",
    "config/permissions.example.yaml",
    "tests/integration/test_agent_loop.py",
    "tests/integration/test_sqlite_store.py",
    "tests/unit/test_context.py",
    "tests/unit/test_deepseek_provider.py",
    "tests/unit/test_llm_instructions.py",
    "tests/unit/test_llm_retry.py",
    "tests/unit/test_runtime_factory.py",
    "tests/unit/test_runtime_hooks.py",
    "tests/unit/test_runtime_skills.py",
    "tests/unit/test_filesystem_tools.py",
    "tests/unit/test_shell_tool.py",
    "tests/unit/test_tool_registry.py",
    "tests/unit/test_verification_loop.py"
)

Write-Host "=== Generic runtime cutover plan ==="
foreach ($relative in $deletePaths) {
    $full = Join-Path $repoRoot $relative
    $state = if (Test-Path $full) { "present" } else { "already absent" }
    Write-Host ("{0,-65} {1}" -f $relative, $state)
}

if (-not $Execute) {
    Write-Host ""
    Write-Host "[dry-run] No files changed."
    Write-Host "Execution requires BOTH -Execute and -ConfirmCutover."
    Write-Host "Do not execute until DeepSeek + security + browser real-host gates are green."
    exit 0
}

if (-not $ConfirmCutover) {
    throw "Refusing destructive cutover without -ConfirmCutover."
}

$requiredEvidence = @(
    "workspace/opencode-evidence/deepseek.pass",
    "workspace/opencode-evidence/security.pass",
    "workspace/opencode-evidence/browser.pass"
)

$missingEvidence = @()
foreach ($relative in $requiredEvidence) {
    if (-not (Test-Path (Join-Path $repoRoot $relative))) {
        $missingEvidence += $relative
    }
}

if ($missingEvidence.Count -gt 0) {
    throw "Refusing cutover; missing local evidence markers: $($missingEvidence -join ', ')"
}

foreach ($relative in $deletePaths) {
    $full = Join-Path $repoRoot $relative
    if (Test-Path $full) {
        Remove-Item -LiteralPath $full -Recurse -Force
        Write-Host "[deleted] $relative"
    }
}

Write-Host ""
Write-Host "Generic runtime files deleted."
Write-Host "NEXT REQUIRED ACTIONS:"
Write-Host "  1. Rewrite src/harness/cli.py, config.py, diagnostics.py and evals.py for OpenCode ownership."
Write-Host "  2. Prune Python dependencies with uv."
Write-Host "  3. Run scan-opencode-cutover-residue.ps1 -Enforce."
Write-Host "  4. Run full CI and clean-clone acceptance."
Write-Host ""
Write-Host "This script intentionally does NOT modify rewrite-required files automatically."
