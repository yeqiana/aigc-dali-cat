$ErrorActionPreference = 'Continue'

$runtimeTask = 'StoryOSRuntime'
$restartTask = 'StoryOSRuntimeRestart'

# Give the caller/worker time to persist its auto-recovery evidence before cleanup.
Start-Sleep -Seconds 3

# Stopping a scheduled task does not reliably terminate launcher child processes,
# so explicitly terminate all Story OS Phase9 runtime carrier processes.
Stop-ScheduledTask -TaskName $runtimeTask -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -match 'phase9_runtime_launcher\.py|phase9_runtime_worker\.py|phase9_metrics_exporter\.py'
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 1
Start-ScheduledTask -TaskName $runtimeTask

# Best-effort self cleanup. Failure here must not affect the restarted runtime.
Unregister-ScheduledTask -TaskName $restartTask -Confirm:$false -ErrorAction SilentlyContinue
