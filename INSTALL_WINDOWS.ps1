# DEPRECATED_STORY_OS_INSTALLER
param(
  [Parameter(Mandatory=$false, Position=0)]
  [string]$RepoPath
)
$ErrorActionPreference = 'Stop'
Write-Error @"
INSTALL_WINDOWS.ps1 is retired and must not be used to copy Story OS files.
Story OS is repository-native now.
Run from the repository root:
  python episodes/_system/story_os.py doctor
  python episodes/_system/contract_sync.py
See START_HERE.md for the canonical execution path.
"@
exit 2
