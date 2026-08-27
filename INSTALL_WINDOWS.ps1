param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$RepoPath,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = (Resolve-Path $RepoPath).Path

if (-not (Test-Path (Join-Path $Repo 'standards\制作规范_正式版.md'))) {
  throw "目标目录不像 aigc-dali-cat/story：缺少 standards/制作规范_正式版.md"
}
if (-not (Test-Path (Join-Path $Repo 'episodes'))) {
  throw "目标目录不像当前 story 分支：缺少 episodes/"
}

$Items = @(
  'SKILL.md',
  'skills',
  '.agents',
  '.codex\skills\dali-cat-story',
  '.github\workflows\story-gates.yml',
  'standards\templates\episode.template.yaml',
  'standards\templates\subtitles.template.yaml',
  'README_UPGRADE.md'
)

foreach ($Rel in $Items) {
  $Src = Join-Path $PackRoot $Rel
  if (-not (Test-Path $Src)) { continue }
  $Dst = Join-Path $Repo $Rel
  Write-Host "COPY $Rel"
  if ($DryRun) { continue }
  $Parent = Split-Path -Parent $Dst
  if ($Parent) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
  if ((Get-Item $Src).PSIsContainer) {
    Copy-Item $Src $Dst -Recurse -Force
  } else {
    Copy-Item $Src $Dst -Force
  }
}

Write-Host "Done. Next: python -m pip install -r skills/dali-cat-story/requirements.txt"
