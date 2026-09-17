param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [string]$Url = "https://example.com"
)

$ErrorActionPreference = "Stop"

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
$mcpOutput = (& opencode mcp list 2>&1 | Out-String)
$mcpOutput | Write-Host

if ($LASTEXITCODE -ne 0 -or $mcpOutput -notmatch "(?i)playwright.*connected") {
    throw "Playwright MCP is not connected."
}

Write-Host "Running isolated OpenCode -> DeepSeek -> Playwright MCP smoke..."
$response = (& opencode run --model $Model --agent browser-smoke --format json $prompt 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
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

Write-Host "[ok] OpenCode -> model -> Playwright MCP -> Chrome gate passed."
