@echo off
setlocal
cd /d "%~dp0"

call app.bat %*
exit /b %errorlevel%
