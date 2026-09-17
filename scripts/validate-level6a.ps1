param()

$ErrorActionPreference = "Stop"

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
        [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
    }
}

function Test-UnityProject {
    param([string]$Path)

    return (Test-Path (Join-Path $Path "Assets") -PathType Container) -and
        (Test-Path (Join-Path $Path "ProjectSettings") -PathType Container)
}

if (-not (Test-Path "pyproject.toml")) {
    throw "Run this script from the harness-ai repository root."
}

Import-DotEnv

foreach ($name in @("DEEPSEEK_API_KEY", "BLENDER_PATH", "UNITY_PATH")) {
    if (-not (Get-Item "Env:$name" -ErrorAction SilentlyContinue).Value) {
        throw "$name is required for Level 6A validation."
    }
}

$project = Join-Path (Get-Location).Path "workspace\unity-level6"
$createLog = Join-Path (Get-Location).Path "data\unity-level6-create.log"

if (Test-Path $project) {
    if (-not (Test-UnityProject $project)) {
        $items = @(Get-ChildItem -LiteralPath $project -Force -ErrorAction Stop)
        if ($items.Count -eq 0) {
            Remove-Item -LiteralPath $project -Force
        }
        else {
            throw "Level 6A Unity path exists but is not a valid project: $project"
        }
    }
}

if (-not (Test-UnityProject $project)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $createLog -Parent) | Out-Null
    Write-Host "`n==> Create Level 6A Unity project" -ForegroundColor Cyan
    & $env:UNITY_PATH -batchmode -nographics -quit -createProject $project -logFile $createLog
    if ($LASTEXITCODE -ne 0) {
        throw "Unity project creation failed with exit code $LASTEXITCODE. See $createLog"
    }
    if (-not (Test-UnityProject $project)) {
        throw "Unity exited successfully but did not create a valid project. See $createLog"
    }
}
else {
    Write-Host "Reusing Unity Level 6A project: $project"
}

Write-Host "`n==> Run Blender -> Unity Level 6A eval" -ForegroundColor Cyan
uv run harness eval evals/blender-unity-smoke.yaml --json-out data/blender-unity-smoke-report.json
if ($LASTEXITCODE -ne 0) {
    throw "Level 6A eval failed with exit code $LASTEXITCODE"
}

$requiredArtifacts = @(
    "workspace\artifacts\level6_cube.blend",
    "workspace\artifacts\level6_cube.fbx",
    "workspace\unity-level6\Assets\Harness\level6_cube.fbx",
    "workspace\unity-level6\Assets\HarnessLevel6.unity"
)

$missing = @($requiredArtifacts | Where-Object { -not (Test-Path $_ -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "Level 6A eval completed but required artifacts are missing: $($missing -join ', ')"
}

Write-Host "`nLevel 6A validation completed successfully." -ForegroundColor Green
$requiredArtifacts | ForEach-Object { Write-Host "  OK $_" }
