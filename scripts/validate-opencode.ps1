param(
    [switch]$SkipMcp
)

$ErrorActionPreference = "Stop"

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

$openCodeVersion = (& opencode --version).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "opencode --version failed."
}

if ($openCodeVersion -notmatch [regex]::Escape($ExpectedOpenCodeVersion)) {
    throw "Expected OpenCode $ExpectedOpenCodeVersion, got '$openCodeVersion'."
}
Write-Host "[ok] OpenCode version $ExpectedOpenCodeVersion"

$nodeVersion = (& node --version).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "node --version failed."
}

$nodeMajor = [int](($nodeVersion.TrimStart("v") -split "\.")[0])
if ($nodeMajor -lt 20) {
    throw "Playwright MCP requires Node.js 20+. Found '$nodeVersion'."
}
Write-Host "[ok] Node $nodeVersion"

Write-Host "Resolving committed OpenCode configuration..."
& opencode debug config | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "opencode debug config failed."
}
Write-Host "[ok] OpenCode project configuration resolves"

if (-not $SkipMcp) {
    Write-Host "Checking pinned Playwright MCP package..."
    $mcpPackageVersion = (& npm view "@playwright/mcp@$ExpectedPlaywrightMcpVersion" version).Trim()
    if ($LASTEXITCODE -ne 0 -or $mcpPackageVersion -ne $ExpectedPlaywrightMcpVersion) {
        throw "Could not resolve @playwright/mcp@$ExpectedPlaywrightMcpVersion."
    }
    Write-Host "[ok] @playwright/mcp@$ExpectedPlaywrightMcpVersion resolves"

    Write-Host "Checking OpenCode MCP registration..."
    $mcpOutput = (& opencode mcp list 2>&1 | Out-String)
    $mcpExitCode = $LASTEXITCODE
    $mcpOutput | Write-Host

    if ($mcpExitCode -ne 0) {
        throw "opencode mcp list failed with exit code $mcpExitCode."
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
