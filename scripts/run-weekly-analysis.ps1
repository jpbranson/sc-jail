$ErrorActionPreference = 'Stop'
$weeklyRoot = Split-Path -Parent $PSScriptRoot
$weeklyRuntime = Join-Path $weeklyRoot '.runtime'
$weeklyPython = Join-Path $weeklyRoot '.venv\Scripts\python.exe'
$weeklyScript = Join-Path $weeklyRoot 'scripts\weekly_analysis.py'
$weeklyLog = Join-Path $weeklyRuntime 'weekly-analysis.log'
New-Item -ItemType Directory -Force -Path $weeklyRuntime | Out-Null

function Write-WeeklyLog($message) {
    Add-Content -LiteralPath $weeklyLog -Value ([DateTimeOffset]::UtcNow.ToString('o') + ' ' + $message)
}

try {
    if (!(Test-Path -LiteralPath $weeklyPython)) { throw 'Run the README setup commands first.' }
    # The bundled Google Cloud CLI is used when gcloud is not already on PATH.
    $weeklySdk = Join-Path $weeklyRuntime 'google-cloud-sdk\bin'
    if (Test-Path -LiteralPath $weeklySdk) { $env:PATH = $weeklySdk + [IO.Path]::PathSeparator + $env:PATH }
    Write-WeeklyLog 'Weekly analysis started.'
    $weeklyArguments = @('"' + $weeklyScript + '"') + $args
    $weeklyProcess = Start-Process -FilePath $weeklyPython -ArgumentList $weeklyArguments -WorkingDirectory $weeklyRoot -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $weeklyRuntime 'weekly-analysis.out.log') -RedirectStandardError (Join-Path $weeklyRuntime 'weekly-analysis.err.log')
    $weeklySummary = Get-Content -LiteralPath (Join-Path $weeklyRuntime 'weekly-analysis.out.log') -Tail 1 -ErrorAction SilentlyContinue
    Write-WeeklyLog ("Weekly analysis exited with code {0}. {1}" -f $weeklyProcess.ExitCode, $weeklySummary)
    exit $weeklyProcess.ExitCode
} catch {
    Write-WeeklyLog ('ERROR: ' + $_.Exception.Message)
    exit 1
}
