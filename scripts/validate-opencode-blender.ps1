param(
    [Parameter(Mandatory = $true)]
    [string]$Model
)

$ErrorActionPreference = "Stop"

$artifactDir = Join-Path (Resolve-Path ".").Path "workspace\opencode-migration"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
$renderPath = Join-Path $artifactDir "blender-mcp-smoke.png"

if (Test-Path $renderPath) {
    Remove-Item $renderPath -Force
}

$override = @{
    mcp = @{
        blenderMCP = @{
            enabled = $true
        }
    }
} | ConvertTo-Json -Depth 10 -Compress

$previousOverride = $env:OPENCODE_CONFIG_CONTENT
$env:OPENCODE_CONFIG_CONTENT = $override

try {
    Write-Host "Checking Blender MCP connection..."
    $mcpOutput = (& opencode mcp list 2>&1 | Out-String)
    $mcpOutput | Write-Host

    if ($LASTEXITCODE -ne 0 -or $mcpOutput -notmatch "(?i)blenderMCP.*connected") {
        throw @"
Blender MCP is not connected.

Prerequisites:
  1. Run .\scripts\prepare-blender-mcp.ps1
  2. Open Blender.
  3. Enable Interface: MCP for Blender.
  4. Press N in the 3D Viewport -> MCP for Blender -> Start MCP Server.
"@
    }

    $marker = "BLENDER_MCP_SMOKE_OK"
    $normalizedRenderPath = $renderPath.Replace("\", "/")

    $prompt = @"
Use Blender MCP only.

Create a bounded smoke-test scene without saving a .blend file:
1. Clear the current scene.
2. Create a cube at the origin.
3. Create a camera positioned to see the cube.
4. Create a light sufficient to illuminate it.
5. Render one PNG image exactly to:
$normalizedRenderPath
6. Verify the render completed.
7. If successful, output exactly this marker on its own line:
$marker

Do not access the network, launch processes, install anything, or write any file other than the requested PNG.
"@

    Write-Host "Running OpenCode -> model -> Blender MCP smoke..."
    $response = (& opencode run --model $Model --agent blender-smoke --format json $prompt 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) {
        $response | Write-Host
        throw "Blender MCP smoke run failed."
    }

    $response | Write-Host

    if ($response -notmatch [regex]::Escape($marker)) {
        throw "Blender MCP smoke did not produce expected marker '$marker'."
    }

    if (-not (Test-Path $renderPath)) {
        throw "Blender MCP reported success but render artifact was not created at '$renderPath'."
    }

    $artifact = Get-Item $renderPath
    if ($artifact.Length -le 0) {
        throw "Blender render artifact is empty."
    }

    Write-Host "[ok] OpenCode -> model -> Blender MCP -> PNG artifact gate passed."
    Write-Host "     $renderPath"
}
finally {
    if ($null -eq $previousOverride) {
        Remove-Item Env:OPENCODE_CONFIG_CONTENT -ErrorAction SilentlyContinue
    }
    else {
        $env:OPENCODE_CONFIG_CONTENT = $previousOverride
    }
}
