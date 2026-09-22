param([switch]$NoTunnel)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRuntime = Join-Path $taskRoot '.runtime'
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskPidPath = Join-Path $taskRuntime 'processes.json'
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
if (!(Test-Path -LiteralPath $taskPython)) { throw 'Run the README setup commands first.' }
$taskPids = @{}
if (Test-Path -LiteralPath $taskPidPath) {
    $saved = Get-Content -LiteralPath $taskPidPath -Raw | ConvertFrom-Json
    foreach ($property in $saved.PSObject.Properties) { $taskPids[$property.Name] = $property.Value }
}
function Start-Component($name, $executable, $arguments, $marker) {
    if ($taskPids.ContainsKey($name)) {
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskPids[$name])" -ErrorAction SilentlyContinue
        if ($existing -and $existing.CommandLine.Contains($marker) -and $existing.ExecutablePath -eq $executable) {
            Write-Output "$name already running (PID $($existing.ProcessId))"
            return
        }
    }
    $process = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRuntime "$name.out.log") -RedirectStandardError (Join-Path $taskRuntime "$name.err.log")
    $taskPids[$name] = $process.Id
    $taskPids | ConvertTo-Json | Set-Content -LiteralPath $taskPidPath
    Write-Output "$name started (PID $($process.Id))"
}
Start-Component 'collector' $taskPython @('-m','sc_jail','schedule') 'sc_jail schedule'
Start-Component 'dashboard' $taskPython @('-m','sc_jail','dashboard','--port','8050') 'sc_jail dashboard'
$taskTunnel = Join-Path $taskRuntime 'cloudflared.exe'
if (!$NoTunnel -and (Test-Path -LiteralPath $taskTunnel)) {
    Start-Component 'tunnel' $taskTunnel @('tunnel','--url','http://127.0.0.1:8050','--no-autoupdate') '127.0.0.1:8050'
}
Write-Output 'Dashboard: http://127.0.0.1:8050'
