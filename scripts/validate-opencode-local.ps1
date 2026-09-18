param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [switch]$Browser,
    [switch]$Unity,
    [switch]$Blender,
    [switch]$All
)

$ErrorActionPreference = "Stop"

Write-Host "=== OpenCode migration local acceptance ==="
Write-Host ""

& .\scripts\validate-opencode.ps1
if ($LASTEXITCODE -ne 0) { throw "OpenCode foundation gate failed." }

& .\scripts\validate-opencode-mcp-candidates.ps1
if ($LASTEXITCODE -ne 0) { throw "MCP candidate package gate failed." }

& .\scripts\validate-opencode-deepseek.ps1 -Model $Model
if ($LASTEXITCODE -ne 0) { throw "OpenCode DeepSeek gate failed." }

if ($All -or $Browser) {
    & .\scripts\validate-opencode-browser.ps1 -Model $Model
    if ($LASTEXITCODE -ne 0) { throw "OpenCode browser gate failed." }
}

if ($All -or $Unity) {
    & .\scripts\validate-opencode-unity.ps1 -Model $Model
    if ($LASTEXITCODE -ne 0) { throw "OpenCode Unity gate failed." }
}

if ($All -or $Blender) {
    & .\scripts\validate-opencode-blender.ps1 -Model $Model
    if ($LASTEXITCODE -ne 0) { throw "OpenCode Blender gate failed." }
}

Write-Host ""
Write-Host "[ok] Requested OpenCode migration gates passed."
