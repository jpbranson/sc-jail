param(
    [ValidateSet('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')]
    [string]$Day = 'Wednesday',
    [string]$At = '09:00'
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskScript = Join-Path $taskRoot 'scripts\run-weekly-analysis.ps1'
$taskName = 'SC-Jail-Weekly-Analysis'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Arguments -notlike "*$taskRoot*")) {
    throw "A different $taskName task exists. It was not changed."
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $taskScript + '"') -WorkingDirectory $taskRoot
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $At
# Runs as the signed-in user so it can use that user's gcloud sign-in; no password is stored.
# A start missed while the computer was off or signed out runs at the next opportunity.
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Weekly private SC-Jail analysis: sync the cloud archive to data/snapshots/current and rebuild the reports in data/analysis/weekly.' -Force | Select-Object TaskName, State
