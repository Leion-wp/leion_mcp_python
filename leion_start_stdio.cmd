@echo off
setlocal
set "REPO=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO%leion_start_stdio.ps1" -Profile core
exit /b %ERRORLEVEL%
