param(
    [Parameter(Mandatory = $true)]
    [string]$Model
)

$ErrorActionPreference = "Stop"

$override = @{
    mcp = @{
        unityMCP = @{
            enabled = $true
        }
    }
} | ConvertTo-Json -Depth 10 -Compress

$previousOverride = $env:OPENCODE_CONFIG_CONTENT
$env:OPENCODE_CONFIG_CONTENT = $override

try {
    Write-Host "Checking Unity MCP connection..."
    $mcpOutput = (& opencode mcp list 2>&1 | Out-String)
    $mcpOutput | Write-Host

    if ($LASTEXITCODE -ne 0 -or $mcpOutput -notmatch "(?i)unityMCP.*connected") {
        throw @"
Unity MCP is not connected.

Prerequisites:
  1. Use the disposable Unity smoke project.
  2. Run .\scripts\prepare-unity-mcp.ps1
  3. Open the project in Unity and wait for package import/compilation.
  4. Open Window -> MCP for Unity and start/configure the server.
"@
    }

    $marker = "UNITY_MCP_SMOKE_OK"
    $objectName = "OpenCodeMigrationSmoke"

    $prompt = @"
Use Unity MCP only.

1. Inspect the currently connected Unity editor and current scene.
2. Create one empty GameObject named '$objectName' at the origin.
3. Verify that the GameObject exists.
4. Delete that GameObject.
5. Verify that it no longer exists.
6. Read the Unity console for errors introduced by this smoke test.
7. If all of the above succeeded, output exactly this marker on its own line:
$marker

Do not install packages, change project settings, save unrelated scene changes, build, publish, or touch any other project.
"@

    Write-Host "Running OpenCode -> model -> Unity MCP smoke..."
    $response = (& opencode run --model $Model --agent unity-smoke --format json $prompt 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) {
        $response | Write-Host
        throw "Unity MCP smoke run failed."
    }

    $response | Write-Host

    if ($response -notmatch [regex]::Escape($marker)) {
        throw "Unity MCP smoke did not produce expected marker '$marker'."
    }

    Write-Host "[ok] OpenCode -> model -> Unity MCP gate passed."
}
finally {
    if ($null -eq $previousOverride) {
        Remove-Item Env:OPENCODE_CONFIG_CONTENT -ErrorAction SilentlyContinue
    }
    else {
        $env:OPENCODE_CONFIG_CONTENT = $previousOverride
    }
}
