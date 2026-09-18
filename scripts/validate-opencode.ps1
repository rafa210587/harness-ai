param(
    [switch]$SkipMcp
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

$ExpectedOpenCodeVersion = "1.18.31"
$ExpectedPlaywrightMcpVersion = "0.0.81"

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found on PATH."
    }

    Write-Host "[ok] $Name -> $($command.Source)"
}

Write-Host "Validating OpenCode migration prerequisites..."

Require-Command "opencode"
Require-Command "node"
Require-Command "npm"
Require-Command "npx"

$openCodeVersionResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 30 -Arguments @("--version")
if ($openCodeVersionResult.ExitCode -ne 0) {
    throw "opencode --version failed."
}
$openCodeVersion = $openCodeVersionResult.Output.Trim()

if ($openCodeVersion -notmatch [regex]::Escape($ExpectedOpenCodeVersion)) {
    throw "Expected OpenCode $ExpectedOpenCodeVersion, got '$openCodeVersion'."
}
Write-Host "[ok] OpenCode version $ExpectedOpenCodeVersion"

$nodeVersionResult = Invoke-NativeCommandCapture -FilePath "node" -TimeoutSeconds 30 -Arguments @("--version")
if ($nodeVersionResult.ExitCode -ne 0) {
    throw "node --version failed."
}
$nodeVersion = $nodeVersionResult.Output.Trim()

$nodeMajor = [int](($nodeVersion.TrimStart("v") -split "\.")[0])
if ($nodeMajor -lt 20) {
    throw "Playwright MCP requires Node.js 20+. Found '$nodeVersion'."
}
Write-Host "[ok] Node $nodeVersion"

Write-Host "Resolving committed OpenCode configuration..."
$debugConfigResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 90 -Arguments @("debug", "config")
$debugConfigResult.Output | Write-Host
if ($debugConfigResult.ExitCode -ne 0) {
    throw "opencode debug config failed."
}
Write-Host "[ok] OpenCode project configuration resolves"

if (-not $SkipMcp) {
    Write-Host "Checking pinned Playwright MCP package..."
    $mcpPackageResult = Invoke-NativeCommandCapture -FilePath "npm" -TimeoutSeconds 60 -Arguments @(
        "view", "@playwright/mcp@$ExpectedPlaywrightMcpVersion", "version"
    )
    $mcpPackageVersion = $mcpPackageResult.Output.Trim()
    if ($mcpPackageResult.ExitCode -ne 0 -or $mcpPackageVersion -ne $ExpectedPlaywrightMcpVersion) {
        throw "Could not resolve @playwright/mcp@$ExpectedPlaywrightMcpVersion."
    }
    Write-Host "[ok] @playwright/mcp@$ExpectedPlaywrightMcpVersion resolves"

    Write-Host "Checking OpenCode MCP registration..."
    $mcpResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 90 -Arguments @("mcp", "list")
    $mcpOutput = $mcpResult.Output
    $mcpOutput | Write-Host

    if ($mcpResult.ExitCode -ne 0) {
        throw "opencode mcp list failed with exit code $($mcpResult.ExitCode)."
    }

    if ($mcpOutput -match "(?i)\bfailed\b|timed out") {
        throw "At least one enabled MCP server failed to connect."
    }

    if ($mcpOutput -notmatch "(?i)playwright") {
        throw "The configured Playwright MCP server was not listed."
    }

    Write-Host "[ok] Enabled MCP servers connected successfully"
}

Write-Host ""
Write-Host "Repository-side OpenCode foundation is healthy."
Write-Host "Real-provider validation is intentionally separate:"
Write-Host "  1. Run: opencode"
Write-Host "  2. Use /connect and select DeepSeek"
Write-Host "  3. Use /models and select the desired DeepSeek model"
Write-Host "  4. Run a real prompt before any custom runtime code is removed"
