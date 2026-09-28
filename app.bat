@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" app.py %*
) else (
  echo The project virtual environment was not found.
  echo Create it with: python -m venv .venv
  echo Then install dependencies: .venv\Scripts\python.exe -m pip install -e ".[app]"
  pause
  exit /b 1
)
if errorlevel 1 (
  pause
  exit /b 1
)
