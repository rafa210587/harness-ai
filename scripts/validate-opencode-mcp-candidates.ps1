param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

$UnityPackage = "mcpforunityserver==10.2.0"
$UnityCommand = "mcp-for-unity"
$BlenderPackage = "mcp-for-blender==2.0.0"
$BlenderCommand = "mcp-for-blender"

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found on PATH."
    }

    Write-Host "[ok] $Name -> $($command.Source)"
}

function Test-UvxEntrypoint {
    param(
        [Parameter(Mandatory = $true)][string]$Package,
        [Parameter(Mandatory = $true)][string]$Command
    )

    Write-Host "Resolving $Package -> $Command ..."
    $result = Invoke-NativeCommandCapture -FilePath "uvx" -Arguments @(
        "--python", "3.12",
        "--from", $Package,
        $Command,
        "--help"
    )

    if ($result.ExitCode -ne 0) {
        $result.Output | Write-Host
        throw "Failed to resolve/run '$Command' from '$Package'."
    }

    if ([string]::IsNullOrWhiteSpace($result.Output)) {
        throw "'$Command --help' returned no output."
    }

    Write-Host "[ok] $Package exposes $Command"
}

Require-Command "uv"
Require-Command "uvx"

Test-UvxEntrypoint -Package $UnityPackage -Command $UnityCommand
Test-UvxEntrypoint -Package $BlenderPackage -Command $BlenderCommand

Write-Host ""
Write-Host "[ok] Pinned Unity/Blender MCP packages and entrypoints resolve."
Write-Host "This gate does not claim a live Unity or Blender connection."
