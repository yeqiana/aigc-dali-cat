@echo off
setlocal
chcp 65001 >nul 2>nul
set "ROOT=%~dp0"
if exist "%ROOT%.story-os-venv\Scripts\python.exe" (
  "%ROOT%.story-os-venv\Scripts\python.exe" "%ROOT%episodes\_system\auto_production.py" run %*
  exit /b %errorlevel%
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%ROOT%episodes\_system\auto_production.py" run %*
  exit /b %errorlevel%
)
python "%ROOT%episodes\_system\auto_production.py" run %*
exit /b %errorlevel%
