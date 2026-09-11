@echo off
if /I "%~1"=="restart" goto :restart
if /I "%~1"=="status" goto :status
echo Story OS CLI
echo   story restart  restart StoryOSRuntime scheduled task
echo   story status   show task state
exit /b 2

:restart
start "" powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0story_restart.ps1"
exit /b 0

:status
powershell -NoProfile -NonInteractive -Command "Get-ScheduledTask -TaskName 'StoryOSRuntime' | Format-List TaskName,State"
exit /b %errorlevel%
