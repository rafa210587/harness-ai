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

function Test-UnityProject {
    param([string]$Path)

    return (Test-Path (Join-Path $Path "Assets") -PathType Container) -and
        (Test-Path (Join-Path $Path "ProjectSettings") -PathType Container)
}

function Resolve-UnitySmokeProject {
    if ($env:HARNESS_UNITY_SMOKE_PROJECT) {
        $configured = [System.IO.Path]::GetFullPath($env:HARNESS_UNITY_SMOKE_PROJECT)
        if (-not (Test-UnityProject $configured)) {
            throw "HARNESS_UNITY_SMOKE_PROJECT is not a valid Unity project: $configured"
        }
        return $configured
    }

    $project = Join-Path (Get-Location).Path "data\unity-smoke-project"
    $logPath = Join-Path (Get-Location).Path "data\unity-smoke-create.log"

    if (Test-Path $project) {
        if (Test-UnityProject $project) {
            Write-Host "Reusing disposable Unity smoke project: $project"
            return $project
        }

        $items = @(Get-ChildItem -LiteralPath $project -Force -ErrorAction Stop)
        if ($items.Count -eq 0) {
            Remove-Item -LiteralPath $project -Force
        }
        else {
            throw "Automatic Unity smoke path exists but is not a valid Unity project: $project"
        }
    }

    New-Item -ItemType Directory -Force -Path (Split-Path $logPath -Parent) | Out-Null

    Invoke-Step "Create disposable Unity smoke project" {
        & $env:UNITY_PATH `
            -batchmode `
            -nographics `
            -quit `
            -createProject $project `
            -logFile $logPath
    }

    if (-not (Test-UnityProject $project)) {
        $logHint = if (Test-Path $logPath) { " See Unity log: $logPath" } else { "" }
        throw "Unity exited successfully but did not create a valid project: $project.$logHint"
    }

    Write-Host "Created disposable Unity smoke project: $project"
    return $project
}

# The deterministic core gate does not import .env. Unit tests that assert defaults or
# missing configuration explicitly isolate themselves from inherited developer variables.
Invoke-Step "Sync dependencies" { uv sync --all-groups }
Invoke-Step "Ruff format" { uv run ruff format --check src tests .claude/hooks }
Invoke-Step "Ruff lint" { uv run ruff check src tests .claude/hooks }
Invoke-Step "Mypy" { uv run mypy src }
Invoke-Step "Core tests" {
    uv run pytest -m "not blender and not unity and not browser_runtime and not browser_external"
}
Invoke-Step "Build distribution" { uv build }
Invoke-Step "Offline doctor" { uv run harness doctor }

# Capability gates intentionally use the real local configuration.
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
    Invoke-Step "Browser runtime smoke" { uv run pytest -m browser_runtime }
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

    $unitySmokeProject = Resolve-UnitySmokeProject
    [Environment]::SetEnvironmentVariable(
        "HARNESS_UNITY_SMOKE_PROJECT",
        $unitySmokeProject,
        "Process"
    )
    Invoke-Step "Unity smoke" { uv run pytest -m unity }
}

Write-Host "`nLocal validation completed successfully."
