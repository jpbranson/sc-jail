$ErrorActionPreference = 'Stop'
$collectionRoot = Split-Path -Parent $PSScriptRoot
$collectionRuntime = Join-Path $collectionRoot '.runtime'
$collectionLog = Join-Path $collectionRuntime 'collection-stop.log'
New-Item -ItemType Directory -Force -Path $collectionRuntime | Out-Null

function Write-CollectionStopLog($message) {
    $entry = [DateTimeOffset]::UtcNow.ToString('o') + ' ' + $message
    Add-Content -LiteralPath $collectionLog -Value $entry
    Write-Output $entry
}

try {
    $collectionLauncher = Join-Path $collectionRoot 'scripts\start-local.ps1'
    $collectionTask = Get-ScheduledTask -TaskName 'SC-Jail-Local' -ErrorAction SilentlyContinue
    if ($collectionTask) {
        $ownedActions = @($collectionTask.Actions | Where-Object {
            $_.Arguments -and $_.Arguments.Contains($collectionLauncher)
        })
        if (!$ownedActions.Count) { throw 'The restart task does not belong to this workspace.' }
        Disable-ScheduledTask -TaskName $collectionTask.TaskName -TaskPath $collectionTask.TaskPath | Out-Null
        Stop-ScheduledTask -TaskName $collectionTask.TaskName -TaskPath $collectionTask.TaskPath
        Write-CollectionStopLog 'Project automatic restart disabled.'
    }

    $collectionPython = Join-Path $collectionRoot '.venv\Scripts\python.exe'
    $collectionPattern = '^\s*"?' + [regex]::Escape($collectionPython) + '"?\s+-m\s+sc_jail\s+(schedule|collect|collector)(\s|$)'
    $collectionProcesses = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object {
        $_.CommandLine -match $collectionPattern
    })
    foreach ($collectionProcess in ($collectionProcesses | Sort-Object ParentProcessId -Descending)) {
        $collectionCurrent = Get-CimInstance Win32_Process -Filter "ProcessId = $($collectionProcess.ProcessId)" -ErrorAction SilentlyContinue
        if ($collectionCurrent -and $collectionCurrent.CommandLine -match $collectionPattern) {
            Get-Process -Id $collectionCurrent.ProcessId -ErrorAction SilentlyContinue | Stop-Process -ErrorAction Stop
            Write-CollectionStopLog "Stopped collector process $($collectionCurrent.ProcessId)."
        }
    }
    $collectionRemaining = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object {
        $_.CommandLine -match $collectionPattern
    })
    if ($collectionRemaining.Count) { throw 'A project collector process is still running.' }

    $collectionPidFile = Join-Path $collectionRuntime 'processes.json'
    if (Test-Path -LiteralPath $collectionPidFile) {
        $collectionSaved = Get-Content -LiteralPath $collectionPidFile -Raw | ConvertFrom-Json
        $collectionSaved.PSObject.Properties.Remove('collector')
        $collectionSaved | ConvertTo-Json | Set-Content -LiteralPath $collectionPidFile
    }
    Write-CollectionStopLog 'Collection paused. Active collector processes: 0. Dashboard and tunnel retained.'
} catch {
    Write-CollectionStopLog ('ERROR: ' + $_.Exception.Message)
    throw
}
