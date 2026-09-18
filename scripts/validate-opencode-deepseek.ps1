param(
    [string]$Model
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

$evidenceDir = Join-Path (Resolve-Path (Join-Path $scriptRoot "..")).Path "workspace\opencode-evidence"
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
Remove-Item -LiteralPath (Join-Path $evidenceDir "deepseek.pass") -Force -ErrorAction SilentlyContinue

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

$cleanAuthOutput = [regex]::Replace($authOutput, "`e\[[0-9;?]*[ -/]*[@-~]", "")
$credentialsSection = ($cleanAuthOutput -split "(?i)Environment", 2)[0]

if (
    $credentialsSection -notmatch "(?i)DeepSeek" -or
    $credentialsSection -match "(?i)\b0 credentials\b"
) {
    throw @"
DeepSeek is not stored in OpenCode auth.json.

Environment-only DEEPSEEK_API_KEY is not accepted for migration cutover.

Run:
  opencode auth login --provider deepseek

Enter the DeepSeek API key so OpenCode stores it outside the repository, then run this script again.
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

Write-PassEvidence -Name "deepseek" -Detail $Model
Write-Host "[ok] OpenCode -> DeepSeek real-provider gate passed."
