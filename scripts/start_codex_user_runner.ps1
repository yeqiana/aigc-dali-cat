#Requires -Version 5.1
<#
.SYNOPSIS
    Start the Story OS Codex user-mode runner (STORY_OS_V2_7_CODEX_USER_MODE_BRIDGE).

.DESCRIPTION
    The runner must be started by the interactive Codex user. It listens on
    127.0.0.1 only, executes nothing but the Codex CLI, and keeps the Codex
    credential inside this user profile. DevSpace/SYSTEM reaches it through the
    loopback endpoint published at runtime/codex-user-runner/endpoint.json.

.PARAMETER Port
    0 (default) lets the OS pick a free loopback port. A fixed port is only
    useful for manual debugging.

.PARAMETER Foreground
    Run the server in this console instead of a hidden background process.

.PARAMETER CodexExe
    Nominate the Codex CLI for this runner user. Defaults to $env:CODEX_EXE,
    then to the runner's own PATH resolution.

.EXAMPLE
    pwsh -File scripts/start_codex_user_runner.ps1

.NOTES
    Refuses to start as SYSTEM / LOCAL SERVICE / NETWORK SERVICE.
#>
[CmdletBinding()]
param(
    [int]$Port = 0,
    [switch]$Foreground,
    [string]$CodexExe = $env:CODEX_EXE
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $RepoRoot 'episodes/_system/codex_user_runner.py'
$RuntimeDir = Join-Path $RepoRoot 'runtime/codex-user-runner'
$Endpoint = Join-Path $RuntimeDir 'endpoint.json'
$StdoutLog = Join-Path $RuntimeDir 'runner.out.log'
$StderrLog = Join-Path $RuntimeDir 'runner.err.log'

function Write-Step([string]$Message) { Write-Host ('[codex-user-runner] ' + $Message) }

# ---------------------------------------------------------------------------
# 1. Identity guard: a service account cannot own an interactive Codex profile.
# ---------------------------------------------------------------------------
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$account = $identity.Split([char]92)[-1].ToUpperInvariant()
if ($account -in @('SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE')) {
    Write-Host 'CODEX_USER_RUNNER_REQUIRES_INTERACTIVE_USER' -ForegroundColor Red
    Write-Host ('current identity: ' + $identity)
    Write-Host 'Start this runner from the interactive desktop session of the Codex user.'
    Write-Host 'DevSpace should reach it over the loopback bridge instead of'
    Write-Host 'launching Codex from the service account itself.'
    exit 2
}
Write-Step ('identity: ' + $identity)

# ---------------------------------------------------------------------------
# 2. Tooling checks: python for the runner, codex for the model tasks.
# ---------------------------------------------------------------------------
$python = $null
$pythonArgs = @()
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd -and ($pythonCmd.Source -notmatch 'WindowsApps')) {
    $python = $pythonCmd.Source
} else {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { $python = $pyCmd.Source; $pythonArgs = @('-3') }
}
if (-not $python) {
    Write-Host 'CODEX_USER_RUNNER_UNAVAILABLE: python not found on PATH' -ForegroundColor Red
    exit 3
}
if (-not (Test-Path -LiteralPath $Runner)) {
    Write-Host ('CODEX_USER_RUNNER_UNAVAILABLE: missing ' + $Runner) -ForegroundColor Red
    exit 3
}

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME }
             elseif ($env:USERPROFILE) { Join-Path $env:USERPROFILE '.codex' }
             else { Join-Path $HOME '.codex' }
Write-Step ('codex home: ' + $codexHome)
if (Test-Path -LiteralPath $codexHome) {
    $hasAuth = Test-Path -LiteralPath (Join-Path $codexHome 'auth.json')
    Write-Step ('codex home present: yes; signed-in credential present: ' + $hasAuth)
} else {
    Write-Host ('warning: codex home not found at ' + $codexHome) -ForegroundColor Yellow
}

$resolvedCodex = $null
if ($CodexExe) {
    if (Test-Path -LiteralPath $CodexExe) { $resolvedCodex = $CodexExe }
    else { Write-Host ('warning: CODEX_EXE not found: ' + $CodexExe) -ForegroundColor Yellow }
}
if (-not $resolvedCodex) {
    $codexCmd = Get-Command codex -ErrorAction SilentlyContinue
    if ($codexCmd) { $resolvedCodex = $codexCmd.Source }
}
if (-not $resolvedCodex) {
    Write-Host 'CODEX_USER_RUNNER_UNAVAILABLE: codex not found on PATH; set CODEX_EXE' -ForegroundColor Red
    exit 3
}
Write-Step ('codex: ' + $resolvedCodex)
try {
    $codexVersion = & $resolvedCodex --version 2>&1 | Select-Object -First 1
    Write-Step ('codex version: ' + $codexVersion)
} catch {
    Write-Host 'warning: could not query the codex version' -ForegroundColor Yellow
}

if (-not (Test-Path -LiteralPath $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
}

# ---------------------------------------------------------------------------
# 3. Start the loopback runner.
# ---------------------------------------------------------------------------
$serveArgs = @($Runner, 'serve', '--host', '127.0.0.1', '--port', $Port)
if ($Foreground) {
    Write-Step 'starting in the foreground (Ctrl+C stops it)'
    & $python @pythonArgs @serveArgs
    exit $LASTEXITCODE
}

$argLine = (($pythonArgs + $serveArgs) | ForEach-Object { '"' + $_ + '"' }) -join ' '
$proc = Start-Process -FilePath $python -ArgumentList $argLine -WindowStyle Hidden -PassThru -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog
Write-Step ('started pid ' + $proc.Id)

$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $Endpoint)) { Start-Sleep -Milliseconds 500 }
if (-not (Test-Path -LiteralPath $Endpoint)) {
    Write-Host 'CODEX_USER_RUNNER_UNAVAILABLE: the runner did not publish its endpoint' -ForegroundColor Red
    if (Test-Path -LiteralPath $StderrLog) { Get-Content -LiteralPath $StderrLog -Tail 20 }
    exit 4
}
Write-Step ('endpoint: ' + $Endpoint)
Write-Step 'the endpoint token file is a local nonce; it is not a Codex credential.'

# ---------------------------------------------------------------------------
# 4. Report health (health never echoes the token or any credential).
# ---------------------------------------------------------------------------
Write-Step 'health:'
& $python @pythonArgs $Runner health --json
exit $LASTEXITCODE
