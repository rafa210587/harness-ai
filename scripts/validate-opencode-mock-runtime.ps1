param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    try {
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    }
    finally {
        $listener.Stop()
    }
}

$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$fixtureDir = Join-Path $repoRoot "workspace\opencode-mock"
New-Item -ItemType Directory -Force -Path $fixtureDir | Out-Null

$readFixture = Join-Path $fixtureDir "read-fixture.txt"
Set-Content -LiteralPath $readFixture -Value "MOCK_READ_FIXTURE_OK" -Encoding utf8

$secretMarker = "MOCK_POLICY_SECRET_" + [guid]::NewGuid().ToString("N")
$secretFixture = Join-Path $repoRoot ".env.opencode-policy-ci"
Set-Content -LiteralPath $secretFixture -Value "SYNTHETIC_SECRET=$secretMarker" -Encoding utf8

$port = Get-FreeTcpPort
$stdout = Join-Path $fixtureDir "provider.stdout.log"
$stderr = Join-Path $fixtureDir "provider.stderr.log"
Remove-Item $stdout, $stderr -Force -ErrorAction SilentlyContinue

$serverScript = Join-Path $repoRoot "tests\fixtures\openai_compatible_mock.py"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "python was not found on PATH."
}

$startArgs = @{
    FilePath = $python.Source
    ArgumentList = @(
        "-u", $serverScript,
        "--port", $port,
        "--read-path", $readFixture,
        "--secret-path", $secretFixture
    )
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
    PassThru = $true
    NoNewWindow = $true
}
$process = Start-Process @startArgs

$previousConfigContent = $env:OPENCODE_CONFIG_CONTENT
$previousOpenAiApiKey = $env:OPENAI_API_KEY
$previousSafeEnv = $env:HARNESS_SAFE_ENV

$envSecretMarker = "MOCK_ENV_SECRET_" + [guid]::NewGuid().ToString("N")
$safeEnvMarker = "MOCK_SAFE_ENV_" + [guid]::NewGuid().ToString("N")
$env:OPENAI_API_KEY = $envSecretMarker
$env:HARNESS_SAFE_ENV = $safeEnvMarker

try {
    $healthy = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 250
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
            if ($health.ok -eq $true) {
                $healthy = $true
                break
            }
        }
        catch {
            if ($process.HasExited) {
                break
            }
        }
    }

    if (-not $healthy) {
        if (Test-Path $stdout) { Get-Content $stdout | Write-Host }
        if (Test-Path $stderr) { Get-Content $stderr | Write-Host }
        throw "Local OpenAI-compatible mock provider did not become healthy."
    }

    $override = @{
        mcp = @{
            playwright = @{ enabled = $false }
            unityMCP = @{ enabled = $false }
            blenderMCP = @{ enabled = $false }
        }
        provider = @{
            harnessmock = @{
                npm = "@ai-sdk/openai-compatible"
                name = "Harness CI Mock"
                options = @{
                    baseURL = "http://127.0.0.1:$port/v1"
                    apiKey = "synthetic-ci-key"
                }
                models = @{
                    "mock-model" = @{
                        id = "mock-model"
                        name = "Harness Mock Model"
                        attachment = $false
                        reasoning = $false
                        temperature = $false
                        tool_call = $true
                        release_date = "2026-01-01"
                        limit = @{
                            context = 32768
                            output = 1024
                        }
                        cost = @{
                            input = 0
                            output = 0
                        }
                        options = @{}
                    }
                }
            }
        }
    } | ConvertTo-Json -Depth 20 -Compress

    $env:OPENCODE_CONFIG_CONTENT = $override
    $model = "harnessmock/mock-model"

    Write-Host "Testing OpenCode provider + built-in read tool loop..."
    $readResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @(
        "run", "--model", $model, "--agent", "mock-runtime",
        "--format", "json", "--title", "harness-mock-read",
        "MOCK_READ_LOOP: use the read tool when requested."
    )
    $readResult.Output | Write-Host
    if ($readResult.ExitCode -ne 0 -or $readResult.Output -notmatch "MOCK_READ_LOOP_OK") {
        throw "OpenCode mock read/tool-loop gate failed."
    }

    Write-Host "Testing project plugin blocks sensitive read in the real OpenCode runtime..."
    $policyResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @(
        "run", "--model", $model, "--agent", "mock-runtime",
        "--format", "json", "--title", "harness-mock-policy",
        "MOCK_SECRET_READ_LOOP: attempt the requested sensitive read."
    )
    $policyResult.Output | Write-Host

    if ($policyResult.Output -match [regex]::Escape($secretMarker)) {
        throw "OpenCode policy integration failure: synthetic secret marker was exposed."
    }
    if ($policyResult.Output -notmatch "harness-policy: blocked") {
        throw "OpenCode policy integration failure: project plugin did not block the sensitive read."
    }
    Write-Host "[ok] OpenCode project plugin blocked sensitive read before file contents were returned."

    Write-Host "Testing OpenCode shell environment secret isolation..."
    $envResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @(
        "run", "--model", $model, "--agent", "security-smoke",
        "--format", "json", "--title", "harness-mock-env",
        "MOCK_ENV_SHELL_LOOP: run the requested shell environment listing."
    )
    $envResult.Output | Write-Host

    if ($envResult.ExitCode -ne 0 -or $envResult.Output -notmatch "MOCK_ENV_SHELL_LOOP_OK") {
        throw "OpenCode shell environment isolation gate failed."
    }
    if ($envResult.Output -match [regex]::Escape($envSecretMarker)) {
        throw "OpenCode shell environment isolation failure: synthetic provider secret was exposed."
    }
    if ($envResult.Output -notmatch [regex]::Escape($safeEnvMarker)) {
        throw "OpenCode shell environment isolation failure: safe environment marker was not preserved."
    }
    Write-Host "[ok] OpenCode shell preserved safe env and hid provider secret."

    Write-Host "Testing OpenCode native skill tool..."
    $skillResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @(
        "run", "--model", $model, "--agent", "mock-runtime",
        "--format", "json", "--title", "harness-mock-skill",
        "MOCK_SKILL_LOOP: load the browser-research skill when requested."
    )
    $skillResult.Output | Write-Host
    if ($skillResult.ExitCode -ne 0 -or $skillResult.Output -notmatch "MOCK_SKILL_LOOP_OK") {
        throw "OpenCode native skill-load gate failed."
    }

    $sessionMatch = [regex]::Match($skillResult.Output, '"sessionID"\s*:\s*"([^"]+)"')
    if (-not $sessionMatch.Success) {
        throw "Could not extract OpenCode sessionID from JSON event output."
    }
    $sessionId = $sessionMatch.Groups[1].Value
    Write-Host "[ok] captured session $sessionId"

    Write-Host "Testing OpenCode session resume..."
    $continueResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 60 -Arguments @(
        "run", "--session", $sessionId, "--model", $model,
        "--agent", "mock-runtime", "--format", "json",
        "MOCK_CONTINUE_OK"
    )
    $continueResult.Output | Write-Host
    if ($continueResult.ExitCode -ne 0 -or $continueResult.Output -notmatch "MOCK_CONTINUE_OK") {
        throw "OpenCode session-resume gate failed."
    }

    $deleteResult = Invoke-NativeCommandCapture -FilePath "opencode" -TimeoutSeconds 30 -Arguments @(
        "session", "delete", $sessionId
    )
    if ($deleteResult.ExitCode -ne 0) {
        Write-Warning "Mock session cleanup failed: $($deleteResult.Output)"
    }

    Write-Host ""
    Write-Host "[ok] OpenCode mock provider/runtime gate passed:"
    Write-Host "     provider -> opencode run"
    Write-Host "     model -> built-in read tool -> model"
    Write-Host "     project plugin -> sensitive read blocked"
    Write-Host "     shell env -> provider secret hidden + safe env preserved"
    Write-Host "     model -> native skill tool -> model"
    Write-Host "     session -> resume"
}
finally {
    if ($null -eq $previousConfigContent) {
        Remove-Item Env:OPENCODE_CONFIG_CONTENT -ErrorAction SilentlyContinue
    }
    else {
        $env:OPENCODE_CONFIG_CONTENT = $previousConfigContent
    }

    if ($null -eq $previousOpenAiApiKey) {
        Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:OPENAI_API_KEY = $previousOpenAiApiKey
    }

    if ($null -eq $previousSafeEnv) {
        Remove-Item Env:HARNESS_SAFE_ENV -ErrorAction SilentlyContinue
    }
    else {
        $env:HARNESS_SAFE_ENV = $previousSafeEnv
    }

    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $process.WaitForExit()
    }

    Remove-Item -LiteralPath $secretFixture -Force -ErrorAction SilentlyContinue
}
