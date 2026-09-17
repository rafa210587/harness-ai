param(
    [switch]$SkipCore,
    [switch]$SkipReliability
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path "pyproject.toml")) {
    throw "Run this script from the harness-ai repository root."
}

$results = [System.Collections.Generic.List[object]]::new()

function Invoke-AcceptanceGate {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkGray
    Write-Host "FULL ACCEPTANCE: $Name" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkGray

    $started = Get-Date
    $ok = $true
    $errorText = $null

    try {
        & $Command
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            throw "$Name returned exit code $LASTEXITCODE"
        }
    }
    catch {
        $ok = $false
        $errorText = $_.Exception.Message
        Write-Host "FAILED: $errorText" -ForegroundColor Red
    }

    $duration = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
    $results.Add([pscustomobject]@{
        name = $Name
        passed = $ok
        duration_seconds = $duration
        error = $errorText
    })

    return $ok
}

if (-not $SkipCore) {
    Invoke-AcceptanceGate "Core + DeepSeek + Chrome + Blender + Unity" {
        & ".\scripts\validate-local.ps1" -All
    } | Out-Null
}

Invoke-AcceptanceGate "Level 6A Blender -> Unity" {
    & ".\scripts\validate-level6a.ps1"
} | Out-Null

if (-not $SkipReliability) {
    Invoke-AcceptanceGate "Real-agent reliability + recovery + context compaction" {
        $previousMax = $env:CONTEXT_MAX_MESSAGES
        $previousKeep = $env:CONTEXT_KEEP_RECENT
        try {
            $env:CONTEXT_MAX_MESSAGES = "8"
            $env:CONTEXT_KEEP_RECENT = "4"
            uv run harness eval evals/full-local-reliability.yaml --json-out data/full-local-reliability-report.json
            if ($LASTEXITCODE -ne 0) {
                throw "Reliability eval failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            if ($null -eq $previousMax) {
                Remove-Item Env:CONTEXT_MAX_MESSAGES -ErrorAction SilentlyContinue
            }
            else {
                $env:CONTEXT_MAX_MESSAGES = $previousMax
            }
            if ($null -eq $previousKeep) {
                Remove-Item Env:CONTEXT_KEEP_RECENT -ErrorAction SilentlyContinue
            }
            else {
                $env:CONTEXT_KEEP_RECENT = $previousKeep
            }
        }
    } | Out-Null
}

$evalReports = @()
foreach ($path in @(
    "data\smoke-report.json",
    "data\blender-unity-smoke-report.json",
    "data\full-local-reliability-report.json"
)) {
    if (Test-Path $path) {
        $report = Get-Content $path -Raw | ConvertFrom-Json
        $evalReports += [pscustomobject]@{
            path = $path
            total = $report.total
            passed = $report.passed
            success_rate = $report.success_rate
            average_steps = $report.average_steps
            total_tool_errors = $report.total_tool_errors
            total_verification_failures = $report.total_verification_failures
            total_tokens = $report.total_tokens
            cases = $report.cases
        }
    }
}

$requiredArtifacts = @(
    "workspace\artifacts\level6_cube.blend",
    "workspace\artifacts\level6_cube.fbx",
    "workspace\unity-level6\Assets\Harness\level6_cube.fbx",
    "workspace\unity-level6\Assets\HarnessLevel6.unity",
    "workspace\artifacts\full_acceptance_cube.blend",
    "workspace\artifacts\full_acceptance_cube.png",
    "workspace\unity-level6\Assets\HarnessFullAcceptance.unity"
)

$artifactResults = foreach ($path in $requiredArtifacts) {
    [pscustomobject]@{
        path = $path
        exists = Test-Path $path -PathType Leaf
    }
}

$failedGates = @($results | Where-Object { -not $_.passed })
$missingArtifacts = @($artifactResults | Where-Object { -not $_.exists })

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("o")
    passed = ($failedGates.Count -eq 0 -and $missingArtifacts.Count -eq 0)
    gates = $results
    eval_reports = $evalReports
    artifacts = $artifactResults
    known_remaining_gate = "Level 6B requires a concrete real VisionProvider and visual correction loop."
}

New-Item -ItemType Directory -Force -Path "data" | Out-Null
$summary | ConvertTo-Json -Depth 12 | Set-Content "data\full-local-acceptance-report.json" -Encoding utf8

Write-Host ""
Write-Host "================ FULL LOCAL ACCEPTANCE SUMMARY ================" -ForegroundColor Cyan
$results | Format-Table name, passed, duration_seconds -AutoSize

foreach ($report in $evalReports) {
    Write-Host ("{0}: {1}/{2} passed, tokens={3}, tool_errors={4}, verification_failures={5}" -f $report.path, $report.passed, $report.total, $report.total_tokens, $report.total_tool_errors, $report.total_verification_failures)
}

Write-Host ""
Write-Host "Artifacts:"
$artifactResults | Format-Table path, exists -AutoSize

Write-Host "Report: data\full-local-acceptance-report.json" -ForegroundColor Yellow
Write-Host "Remaining product gate: Level 6B real vision + visual correction." -ForegroundColor Yellow

if ($failedGates.Count -gt 0 -or $missingArtifacts.Count -gt 0) {
    exit 1
}

Write-Host ""
Write-Host "FULL LOCAL ACCEPTANCE PASSED." -ForegroundColor Green
