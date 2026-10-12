@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -m recovery.preflight
if errorlevel 1 exit /b 1

echo Starting AI recovery coordinator. Press Ctrl+C to stop it.
"%PYTHON_EXE%" -m recovery.service serve
exit /b %errorlevel%
