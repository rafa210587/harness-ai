param()

$ErrorActionPreference = "Stop"

$Package = "mcp-for-blender"
$Version = "1.9.1"

$uvx = Get-Command uvx -ErrorAction SilentlyContinue
if (-not $uvx) {
    throw "uvx was not found. Install/sync uv first."
}

Write-Host "Installing the pinned Blender MCP addon candidate..."
& uvx --from "$Package==$Version" mcp-for-blender install-addon
if ($LASTEXITCODE -ne 0) {
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
Write-Host "Telemetry is disabled in the committed OpenCode MCP environment."
