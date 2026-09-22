$targets = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'incremental_frame_review|episodes/_system' -and $_.Name -match 'python' }
$targets | Select-Object ProcessId, ParentProcessId, CommandLine | Format-List
$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Output '--- leftover check ---'
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' } | Select-Object ProcessId, ParentProcessId, CommandLine | Format-List
