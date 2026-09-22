param([switch]$KeepTask, [switch]$KeepTunnel)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPidPath = Join-Path $taskRoot '.runtime\processes.json'
function Stop-OwnedTree($processId) {
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $processId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        if ($child.CommandLine -and $child.CommandLine.Contains($taskRoot) -and ($child.CommandLine -match 'sc_jail|127.0.0.1:8050')) {
            Stop-OwnedTree $child.ProcessId
        }
    }
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
}
if (Test-Path -LiteralPath $taskPidPath) {
    $taskPids = Get-Content -LiteralPath $taskPidPath -Raw | ConvertFrom-Json
    $remaining = @{}
    foreach ($property in $taskPids.PSObject.Properties) {
        if ($KeepTunnel -and $property.Name -eq 'tunnel') { $remaining[$property.Name] = $property.Value; continue }
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($property.Value)" -ErrorAction SilentlyContinue
        if ($process -and $process.ExecutablePath.StartsWith($taskRoot, [StringComparison]::OrdinalIgnoreCase) -and ($process.CommandLine -match 'sc_jail|127.0.0.1:8050')) {
            Stop-OwnedTree $process.ProcessId
            Write-Output "$($property.Name) stopped"
        }
    }
    if ($remaining.Count) { $remaining | ConvertTo-Json | Set-Content -LiteralPath $taskPidPath }
    else { Remove-Item -LiteralPath $taskPidPath }
}
if (!$KeepTask) {
    $task = Get-ScheduledTask -TaskName 'SC-Jail-Local' -ErrorAction SilentlyContinue
    if ($task -and ($task.Actions.Arguments -like "*$taskRoot*")) {
        Unregister-ScheduledTask -TaskName 'SC-Jail-Local' -Confirm:$false
        Write-Output 'Automatic local restart disabled'
    }
}
