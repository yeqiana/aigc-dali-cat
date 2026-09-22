$ErrorActionPreference = 'Continue'
$restartTask = 'StoryOSRuntimeRestart'
$applyScript = Join-Path $PSScriptRoot 'story_restart_apply.ps1'

# Use a detached one-shot scheduled task so restart can also be initiated by the
# Runtime worker itself. Execute a real .ps1 file instead of embedding a long
# PowerShell -Command string; Task Scheduler quoting previously collapsed that
# command to `-Command ""` and made restart a no-op.
$arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $applyScript + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(1)
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $restartTask -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName $restartTask
Write-Output ("story restart dispatched via one-shot task: " + $restartTask)
