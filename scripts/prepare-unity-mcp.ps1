param(
    [string]$ProjectPath = $env:HARNESS_UNITY_SMOKE_PROJECT,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$PackageName = "com.coplaydev.unity-mcp"
$PackageVersion = "10.2.0"
$PackageSource = "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v$PackageVersion"

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    throw "Pass -ProjectPath or set HARNESS_UNITY_SMOKE_PROJECT to a disposable Unity project."
}

$resolvedProject = (Resolve-Path $ProjectPath).Path
$manifestPath = Join-Path $resolvedProject "Packages\manifest.json"

if (-not (Test-Path $manifestPath)) {
    throw "Unity Packages\manifest.json not found under '$resolvedProject'."
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($null -eq $manifest.dependencies) {
    throw "Unity manifest does not contain a dependencies object."
}

$currentProperty = $manifest.dependencies.PSObject.Properties[$PackageName]
if ($null -ne $currentProperty) {
    if ($currentProperty.Value -eq $PackageSource) {
        Write-Host "[ok] $PackageName is already pinned to $PackageVersion"
        exit 0
    }

    if (-not $Force) {
        throw "$PackageName already exists with '$($currentProperty.Value)'. Re-run with -Force only if replacing that source is intentional."
    }
}

$backupPath = "$manifestPath.pre-opencode-migration.bak"
if (-not (Test-Path $backupPath)) {
    Copy-Item $manifestPath $backupPath
    Write-Host "[ok] Backup created: $backupPath"
}

$manifest.dependencies | Add-Member -NotePropertyName $PackageName -NotePropertyValue $PackageSource -Force
$manifest | ConvertTo-Json -Depth 100 | Set-Content $manifestPath -Encoding utf8

Write-Host "[ok] Pinned $PackageName $PackageVersion in:"
Write-Host "     $manifestPath"
Write-Host ""
Write-Host "Next local gate:"
Write-Host "  1. Open the disposable project in Unity."
Write-Host "  2. Wait for Package Manager resolution and compilation."
Write-Host "  3. Open Window -> MCP for Unity and verify the package reports healthy."
Write-Host "  4. Do not overwrite project OpenCode config with a global client config."
Write-Host "  5. Enable the committed unityMCP candidate in opencode.jsonc for the benchmark."
