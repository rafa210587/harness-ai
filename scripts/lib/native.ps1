function Invoke-NativeCommandCapture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [int]$TimeoutSeconds = 0
    )

    if ($TimeoutSeconds -gt 0) {
        $payload = [pscustomobject]@{
            FilePath = $FilePath
            Arguments = @($Arguments)
            WorkingDirectory = (Get-Location).Path
        }

        $job = Start-Job -ArgumentList $payload -ScriptBlock {
            param($Payload)

            Set-Location $Payload.WorkingDirectory
            $previousErrorActionPreference = $ErrorActionPreference
            $nativePreferenceExists = Test-Path Variable:PSNativeCommandUseErrorActionPreference
            if ($nativePreferenceExists) {
                $previousNativePreference = $PSNativeCommandUseErrorActionPreference
            }

            try {
                $ErrorActionPreference = "Continue"
                if ($nativePreferenceExists) {
                    $PSNativeCommandUseErrorActionPreference = $false
                }

                $lines = & $Payload.FilePath @($Payload.Arguments) 2>&1 |
                    ForEach-Object { $_.ToString() }
                $exitCode = $LASTEXITCODE

                [pscustomobject]@{
                    Output = ($lines -join [Environment]::NewLine)
                    ExitCode = $exitCode
                    TimedOut = $false
                }
            }
            finally {
                $ErrorActionPreference = $previousErrorActionPreference
                if ($nativePreferenceExists) {
                    $PSNativeCommandUseErrorActionPreference = $previousNativePreference
                }
            }
        }

        try {
            $completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
            if ($null -eq $completed) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                return [pscustomobject]@{
                    Output = "Command timed out after $TimeoutSeconds seconds: $FilePath"
                    ExitCode = 124
                    TimedOut = $true
                }
            }

            $result = Receive-Job -Job $job
            if ($result -is [array]) {
                $result = $result | Select-Object -Last 1
            }
            return $result
        }
        finally {
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        }
    }

    $previousErrorActionPreference = $ErrorActionPreference
    $nativePreferenceExists = Test-Path Variable:PSNativeCommandUseErrorActionPreference
    if ($nativePreferenceExists) {
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        # Native CLIs frequently write progress/warnings to stderr even on success.
        # Treat only the process exit code as success/failure and capture both streams.
        $ErrorActionPreference = "Continue"
        if ($nativePreferenceExists) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $lines = & $FilePath @Arguments 2>&1 | ForEach-Object { $_.ToString() }
        $exitCode = $LASTEXITCODE

        [pscustomobject]@{
            Output = ($lines -join [Environment]::NewLine)
            ExitCode = $exitCode
            TimedOut = $false
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        if ($nativePreferenceExists) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }
}
