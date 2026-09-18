param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [string]$Url = "https://example.com"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")


function Write-PassEvidence {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Detail
    )

    $repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
    $evidenceDir = Join-Path $repoRoot "workspace\opencode-evidence"
    New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
    $payload = [ordered]@{
        gate = $Name
        detail = $Detail
        timestamp = [DateTimeOffset]::UtcNow.ToString("O")
    } | ConvertTo-Json -Compress
    Set-Content -LiteralPath (Join-Path $evidenceDir "$Name.pass") -Value $payload -Encoding utf8
}

$marker = "BROWSER_SMOKE_OK"
$prompt = @"
Use the Playwright MCP to navigate to $Url.
Read the page title and visible main heading.
Do not click any link or submit anything.
When finished, output:
$marker
TITLE=<observed title>
HEADING=<observed main heading>
"@

Write-Host "Checking configured MCP status..."
$mcpResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 90 -Arguments @("mcp", "list")
$mcpOutput = $mcpResult.Output
$mcpOutput | Write-Host

if ($mcpResult.ExitCode -ne 0 -or $mcpOutput -notmatch "(?i)playwright.*connected") {
    throw "Playwright MCP is not connected."
}

Write-Host "Running isolated OpenCode -> DeepSeek -> Playwright MCP smoke..."
$runResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 180 -Arguments @(
    "run", "--model", $Model, "--agent", "browser-smoke", "--format", "json", $prompt
)
$response = $runResult.Output
if ($runResult.ExitCode -ne 0) {
    $response | Write-Host
    throw "Browser smoke run failed."
}

$response | Write-Host

if ($response -notmatch [regex]::Escape($marker)) {
    throw "Browser smoke did not produce expected marker '$marker'."
}

if ($response -notmatch "(?i)example domain") {
    throw "Browser smoke did not observe the expected Example Domain content."
}

Write-PassEvidence -Name "browser" -Detail $Url
Write-Host "[ok] OpenCode -> model -> Playwright MCP -> Chrome gate passed."
