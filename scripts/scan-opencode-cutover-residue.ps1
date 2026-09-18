param(
    [switch]$Enforce
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path

$patterns = @(
    @{ Name = "custom AgentLoop"; Regex = "\bAgentLoop\b"; Roots = @("src", "tests") },
    @{ Name = "custom ToolRegistry"; Regex = "\bToolRegistry\b"; Roots = @("src", "tests") },
    @{ Name = "custom LLMProvider"; Regex = "\bLLMProvider\b"; Roots = @("src", "tests") },
    @{ Name = "custom DeepSeekProvider"; Regex = "\bDeepSeekProvider\b"; Roots = @("src", "tests") },
    @{ Name = "runtime skill_list"; Regex = "\bskill_list\b"; Roots = @("src", "tests") },
    @{ Name = "runtime skill_load"; Regex = "\bskill_load\b"; Roots = @("src", "tests") },
    @{ Name = "runtime package imports"; Regex = "harness\.runtime|from harness import runtime"; Roots = @("src", "tests") },
    @{ Name = "LLM package imports"; Regex = "harness\.llm|from harness import llm"; Roots = @("src", "tests") },
    @{ Name = "legacy harness database"; Regex = "harness\.db"; Roots = @("src", "tests", "config", "scripts") },
    @{ Name = "legacy model config"; Regex = "config[/\\]models(\.example)?\.yaml"; Roots = @(".") },
    @{ Name = "legacy permission config"; Regex = "config[/\\]permissions(\.example)?\.yaml"; Roots = @(".") }
)

$ignoreDirs = @(".git", ".venv", ".work", "workspace", "data", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")

function Get-SearchFiles {
    param([string[]]$Roots)

    foreach ($root in $Roots) {
        $full = if ($root -eq ".") { $repoRoot } else { Join-Path $repoRoot $root }
        if (-not (Test-Path $full)) { continue }

        Get-ChildItem -LiteralPath $full -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $path = $_.FullName
                -not ($ignoreDirs | Where-Object {
                    $separator = [IO.Path]::DirectorySeparatorChar
                    $path -like "*$separator$_$separator*"
                })
            }
    }
}

$findings = @()

foreach ($item in $patterns) {
    $hits = @()

    foreach ($file in (Get-SearchFiles -Roots $item.Roots | Sort-Object FullName -Unique)) {
        if ($file.Extension -notin @(".py", ".ps1", ".json", ".jsonc", ".yaml", ".yml", ".toml", ".md", ".js", ".mjs", ".ts")) {
            continue
        }

        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue)) {
            $lineNumber++
            if ($line -match $item.Regex) {
                $relative = [IO.Path]::GetRelativePath($repoRoot, $file.FullName)
                $hits += "$($relative):$lineNumber"
            }
        }
    }

    if ($hits.Count -gt 0) {
        $findings += [pscustomobject]@{
            Name = $item.Name
            Count = $hits.Count
            Examples = ($hits | Select-Object -First 8) -join ", "
        }
    }
}

if ($findings.Count -eq 0) {
    Write-Host "[ok] No legacy runtime residue detected."
    exit 0
}

Write-Host "Legacy runtime residue still present:"
$findings | Format-Table -AutoSize | Out-Host

if ($Enforce) {
    throw "OpenCode cutover residue gate failed: legacy runtime references remain."
}

Write-Host ""
Write-Host "[info] Report-only mode: expected during parity migration."
Write-Host "       Re-run with -Enforce only after replacement gates pass."
