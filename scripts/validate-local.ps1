param(
    [switch]$Online,
    [switch]$Browser,
    [switch]$Blender,
    [switch]$Unity,
    [switch]$All
)

$ErrorActionPreference = "Stop"

if ($All) {
    $Online = $true
    $Browser = $true
    $Blender = $true
    $Unity = $true
}

$HarnessEnvironmentKeys = @(
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "HARNESS_DATA_DIR",
    "HARNESS_WORKSPACE",
    "HARNESS_SKILLS_DIR",
    "HARNESS_LOG_LEVEL",
    "HARNESS_BROWSER_PROFILE",
    "HARNESS_BROWSER_HEADLESS",
    "HARNESS_UNITY_SMOKE_PROJECT",
    "BLENDER_PATH",
    "UNITY_PATH",
    "AGENT_MAX_STEPS",
    "AGENT_MAX_CONSECUTIVE_ERRORS",
    "AGENT_MAX_TOOL_RUNTIME_SECONDS",
    "AGENT_LLM_TIMEOUT_SECONDS",
    "AGENT_LLM_MAX_ATTEMPTS",
    "AGENT_LLM_RETRY_BASE_SECONDS",
    "CONTEXT_MAX_MESSAGES",
    "CONTEXT_KEEP_RECENT"
)

$OriginalHarnessEnvironment = @{}
foreach ($name in $HarnessEnvironmentKeys) {
    $OriginalHarnessEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

function Clear-HarnessEnvironment {
    foreach ($name in $HarnessEnvironmentKeys) {
        [Environment]::SetEnvironmentVariable($name, $null, "Process")
    }
}

function Restore-HarnessEnvironment {
    foreach ($name in $HarnessEnvironmentKeys) {
        [Environment]::SetEnvironmentVariable($name, $OriginalHarnessEnvironment[$name], "Process")
    }
}

function Import-DotEnv {
    if (-not (Test-Path ".env")) {
        return
    }

    foreach ($line in Get-Content ".env") {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed -split "=", 2
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

try {
    # Core validation must be deterministic even when the caller already loaded a real .env.
    Clear-HarnessEnvironment

    Invoke-Step "Sync dependencies" { uv sync --all-groups }
    Invoke-Step "Ruff format" { uv run ruff format --check src tests .claude/hooks }
    Invoke-Step "Ruff lint" { uv run ruff check src tests .claude/hooks }
    Invoke-Step "Mypy" { uv run mypy src }
    Invoke-Step "Core tests" {
        uv run pytest -m "not blender and not unity and not browser_runtime and not browser_external"
    }
    Invoke-Step "Build distribution" { uv build }
    Invoke-Step "Offline doctor" { uv run harness doctor }

    # Capability gates intentionally use the caller environment plus the real local .env.
    Restore-HarnessEnvironment
    if ($Online -or $Browser -or $Blender -or $Unity) {
        Import-DotEnv
    }

    if ($Online) {
        if (-not $env:DEEPSEEK_API_KEY) {
            throw "DEEPSEEK_API_KEY is required for -Online"
        }
        Invoke-Step "Online doctor" { uv run harness doctor --online }
        Invoke-Step "Real DeepSeek smoke eval" {
            uv run harness eval evals/smoke.yaml --json-out data/smoke-report.json
        }
    }

    if ($Browser) {
        Invoke-Step "Chromium runtime smoke" { uv run pytest -m browser_runtime }
    }

    if ($Blender) {
        if (-not $env:BLENDER_PATH) {
            throw "BLENDER_PATH is required for -Blender"
        }
        Invoke-Step "Blender smoke" { uv run pytest -m blender }
    }

    if ($Unity) {
        if (-not $env:UNITY_PATH) {
            throw "UNITY_PATH is required for -Unity"
        }
        if (-not $env:HARNESS_UNITY_SMOKE_PROJECT) {
            throw "HARNESS_UNITY_SMOKE_PROJECT is required for -Unity"
        }
        Invoke-Step "Unity smoke" { uv run pytest -m unity }
    }

    Write-Host "`nLocal validation completed successfully." -ForegroundColor Green
}
finally {
    Restore-HarnessEnvironment
}
