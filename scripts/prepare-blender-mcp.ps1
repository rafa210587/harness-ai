param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

$Package = "mcp-for-blender"
$Version = "2.0.0"

$uvx = Get-Command uvx -ErrorAction SilentlyContinue
if (-not $uvx) {
    throw "uvx was not found. Install/sync uv first."
}

Write-Host "Installing the pinned Blender MCP addon candidate..."
$result = Invoke-NativeCommandCapture -FilePath "uvx" -TimeoutSeconds 180 -Arguments @(
    "--from", "$Package==$Version",
    "mcp-for-blender",
    "install-addon"
)
$result.Output | Write-Host
if ($result.ExitCode -ne 0) {
    throw "Pinned Blender MCP addon installation failed."
}

Write-Host ""
Write-Host "[ok] $Package $Version addon installer completed."
Write-Host "Next local gate:"
Write-Host "  1. Open Blender."
Write-Host "  2. Enable 'Interface: MCP for Blender' if it is not enabled."
Write-Host "  3. In the 3D Viewport press N -> MCP for Blender -> Start MCP Server."
Write-Host "  4. Enable the committed blenderMCP candidate in opencode.jsonc for the benchmark."
Write-Host ""
Write-Host "Telemetry is disabled and BLENDER_MCP_SAFE_MODE=1 is enabled in the committed OpenCode MCP environment."
