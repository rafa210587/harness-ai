param(
    [string]$Model
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found on PATH."
    }
}

Require-Command "opencode"

Write-Host "Checking OpenCode DeepSeek authentication..."
$authResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 30 -Arguments @("auth", "list")
$authOutput = $authResult.Output
if ($authResult.ExitCode -ne 0) {
    throw "opencode auth list failed."
}
$authOutput | Write-Host

if ($authOutput -notmatch "(?i)deepseek") {
    throw @"
DeepSeek is not authenticated in OpenCode.

Run:
  opencode auth login

Select DeepSeek and enter the API key, then run this script again.
"@
}

Write-Host "Refreshing/listing DeepSeek models..."
$modelResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @("models", "deepseek", "--refresh")
$modelOutput = $modelResult.Output
if ($modelResult.ExitCode -ne 0) {
    throw "opencode models deepseek --refresh failed."
}
$modelOutput | Write-Host

if ([string]::IsNullOrWhiteSpace($Model)) {
    throw @"
No -Model was supplied.

Choose one exact provider/model id from the list above and run, for example:
  .\scripts\validate-opencode-deepseek.ps1 -Model "deepseek/<model-id>"
"@
}

if ($modelOutput -notmatch [regex]::Escape($Model)) {
    throw "Requested model '$Model' was not found in 'opencode models deepseek --refresh'."
}

$marker = "OPENCODE_DEEPSEEK_OK"
$prompt = "Reply with exactly: $marker. Do not call any tool."

Write-Host "Running real OpenCode -> DeepSeek request with $Model ..."
$runResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 180 -Arguments @(
    "run", "--model", $Model, "--format", "json", $prompt
)
$response = $runResult.Output
if ($runResult.ExitCode -ne 0) {
    $response | Write-Host
    throw "opencode run failed."
}

$response | Write-Host

if ($response -notmatch [regex]::Escape($marker)) {
    throw "DeepSeek response did not contain expected marker '$marker'."
}

Write-Host "[ok] OpenCode -> DeepSeek real-provider gate passed."
