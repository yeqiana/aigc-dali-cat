$ErrorActionPreference = 'Stop'
$t = Get-ScheduledTask -TaskName 'StoryOSRuntime'
$lines = @(
  ("State=" + $t.State),
  ("PrincipalUserId=" + $t.Principal.UserId),
  ("LogonType=" + $t.Principal.LogonType),
  ("RunLevel=" + $t.Principal.RunLevel),
  ("Trigger=" + (($t.Triggers | Out-String).Trim()))
)
foreach ($a in $t.Actions) {
  $lines += ("Execute=" + $a.Execute)
  $lines += ("Arguments=" + $a.Arguments)
}
$outFile = Join-Path $PSScriptRoot 'task_dump.txt'
$lines | Set-Content -Path $outFile -Encoding UTF8
Write-Output 'OK: task_dump.txt written'
