#Requires -Version 5.1
<#
.SYNOPSIS
    Optional: register the Story OS Codex user-mode runner as an at-logon task.

.DESCRIPTION
    This script never registers anything unless -Register is passed, so a plain
    run only prints the plan. The task runs as the current interactive user with
    LogonType Interactive, which means Windows stores no password and the task
    only starts while that user is logged on.

    If you would rather not use Task Scheduler, run
    scripts/start_codex_user_runner.ps1 manually after each logon instead.

.PARAMETER Register
    Actually create or update the scheduled task.

.PARAMETER Unregister
    Remove the scheduled task.

.PARAMETER TaskName
    Task name. Defaults to StoryOS-Codex-User-Runner.
#>
[CmdletBinding()]
param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$TaskName = 'StoryOS-Codex-User-Runner'
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $RepoRoot 'scripts/start_codex_user_runner.ps1'

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$account = $identity.Split([char]92)[-1].ToUpperInvariant()
if ($account -in @('SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE')) {
    Write-Host 'CODEX_USER_RUNNER_REQUIRES_INTERACTIVE_USER' -ForegroundColor Red
    Write-Host ('current identity: ' + $identity)
    Write-Host 'The Codex runner belongs to the interactive user session; register the'
    Write-Host 'at-logon task from that user, not from a service account.'
    exit 2
}

if (-not (Test-Path -LiteralPath $StartScript)) {
    Write-Host ('missing launcher: ' + $StartScript) -ForegroundColor Red
    exit 3
}

if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host ('unregistered scheduled task: ' + $TaskName)
        exit 0
    } catch {
        Write-Host ('nothing to unregister (' + $TaskName + '): ' + $_.Exception.Message) -ForegroundColor Yellow
        exit 0
    }
}

$powershellExe = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$argument = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $StartScript + '"'

Write-Host ('task name   : ' + $TaskName)
Write-Host ('runs as     : ' + $identity + ' (interactive logon, no stored password)')
Write-Host ('trigger     : at logon of ' + $identity)
Write-Host ('action      : ' + $powershellExe + ' ' + $argument)
Write-Host ('stay loaded : while the user is logged on (no password is written anywhere)')

if (-not $Register) {
    Write-Host ''
    Write-Host 'dry run: no scheduled task was created.'
    Write-Host ('re-run with -Register to create it, e.g.:')
    Write-Host ('  pwsh -File scripts/install_codex_user_runner_task.ps1 -Register')
    exit 0
}

$action = New-ScheduledTaskAction -Execute $powershellExe -Argument $argument -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force -Description 'Story OS V2.7 Codex user-mode runner (loopback bridge for DevSpace/SYSTEM).' | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
Write-Host ''
Write-Host ('registered: ' + $task.TaskName + ' state=' + $task.State)
Write-Host ('principal : ' + $task.Principal.UserId + ' logon=' + $task.Principal.LogonType)
Write-Host 'the task starts at the next logon of this user; to start it now:'
Write-Host ('  Start-ScheduledTask -TaskName ' + $TaskName)
exit 0
