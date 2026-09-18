param(
    [string]$Model
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptRoot "lib\native.ps1")

function Test-StoredDeepSeekCredential {
    $auth = Invoke-NativeCommandCapture -FilePath "opencode" -Arguments @("auth", "list")
    if ($auth.ExitCode -ne 0) {
        return $false
    }

    $clean = [regex]::Replace($auth.Output, "`e\[[0-9;?]*[ -/]*[@-~]", "")
    $credentialsSection = ($clean -split "(?i)Environment", 2)[0]

    return (
        $credentialsSection -match "(?i)DeepSeek" -and
        $credentialsSection -notmatch "(?i)\b0 credentials\b"
    )
}

function Ensure-DeepSeekAuth {
    if (Test-StoredDeepSeekCredential) {
        Write-Host "[ok] DeepSeek credential is stored in OpenCode auth.json."
        return
    }

    Write-Host "DeepSeek is available only through environment credentials or is not configured."
    Write-Host "For migration cutover, the API key must be stored in OpenCode auth.json."
    Write-Host "Starting interactive DeepSeek login..."
    Write-Host ""

    & opencode auth login --provider deepseek
    if ($LASTEXITCODE -ne 0) {
        throw "opencode auth login --provider deepseek failed."
    }

    if (-not (Test-StoredDeepSeekCredential)) {
        throw "DeepSeek credential is still not stored in OpenCode auth.json after login."
    }

    Write-Host "[ok] DeepSeek credential stored in OpenCode auth.json."
}

function Resolve-DeepSeekModel {
    param([string]$Requested)

    $result = Invoke-NativeCommandCapture -FilePath "opencode" -Arguments @(
        "models", "deepseek", "--refresh"
    )
    if ($result.ExitCode -ne 0) {
        $result.Output | Write-Host
        throw "Could not list DeepSeek models from OpenCode."
    }

    $models = @(
        $result.Output -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -match "^deepseek/" } |
            Sort-Object -Unique
    )

    if ($Requested) {
        if ($models -notcontains $Requested) {
            Write-Host "Available DeepSeek models:"
            $models | ForEach-Object { Write-Host "  $_" }
            throw "Requested model is not in the OpenCode DeepSeek model list: $Requested"
        }
        return $Requested
    }

    if ($models.Count -eq 0) {
        $result.Output | Write-Host
        throw "No DeepSeek models were returned by OpenCode."
    }

    if ($models.Count -eq 1) {
        Write-Host "[ok] Using the only available DeepSeek model: $($models[0])"
        return $models[0]
    }

    Write-Host ""
    Write-Host "Available DeepSeek models:"
    for ($i = 0; $i -lt $models.Count; $i++) {
        Write-Host ("  [{0}] {1}" -f ($i + 1), $models[$i])
    }

    while ($true) {
        $selection = Read-Host "Choose a model number"
        $index = 0
        if ([int]::TryParse($selection, [ref]$index) -and $index -ge 1 -and $index -le $models.Count) {
            return $models[$index - 1]
        }
        Write-Host "Invalid selection."
    }
}

Write-Host "=== OpenCode migration Stage 2: real provider + security + browser ==="
Write-Host ""

Ensure-DeepSeekAuth
$selectedModel = Resolve-DeepSeekModel -Requested $Model

Write-Host ""
Write-Host "Selected model: $selectedModel"
Write-Host ""

$previousDeepSeekApiKey = $env:DEEPSEEK_API_KEY

try {
    # Prove runtime auth comes from OpenCode credential storage, not inherited provider env vars.
    Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue

    & (Join-Path $scriptRoot "validate-opencode-local.ps1") -Model $selectedModel -Security -Browser

    if ($LASTEXITCODE -ne 0) {
        throw "OpenCode Stage 2 acceptance failed."
    }
}
finally {
    if ($null -eq $previousDeepSeekApiKey) {
        Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:DEEPSEEK_API_KEY = $previousDeepSeekApiKey
    }
}

Write-Host ""
Write-Host "[ok] OpenCode Stage 2 passed."
Write-Host "Generic runtime cutover evidence markers should now exist under workspace\opencode-evidence."
