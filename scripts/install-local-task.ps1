$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskScript = Join-Path $taskRoot 'scripts\start-local.ps1'
$existing = Get-ScheduledTask -TaskName 'SC-Jail-Local' -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Arguments -notlike "*$taskRoot*")) {
    throw 'A different SC-Jail-Local task exists. It was not changed.'
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -File "' + $taskScript + '"') -WorkingDirectory $taskRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
Register-ScheduledTask -TaskName 'SC-Jail-Local' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Keep the local Shelby County collector and dashboard running while signed in.' -Force | Select-Object TaskName,State
