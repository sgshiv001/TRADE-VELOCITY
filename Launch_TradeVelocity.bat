@echo off
setlocal EnableExtensions DisableDelayedExpansion
title TradeVelocity

rem Use this file's folder, even when launched from another directory.
pushd "%~dp0"
if errorlevel 1 (
    echo Could not open the TradeVelocity project folder.
    pause
    exit /b 1
)

if not exist "app.py" (
    echo app.py was not found. Keep this launcher in the project folder.
    popd
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo The project's Python environment was not found.
    echo Run these commands from this folder first:
    echo.
    echo python -m venv .venv
    echo .venv\Scripts\python.exe -m pip install -e ".[app,test]"
    echo.
    popd
    pause
    exit /b 1
)

echo Starting TradeVelocity. Choose a browser when prompted.
echo Keep this window open while using the app. Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" "app.py" %*
set "TRADEVELOCITY_EXIT_CODE=%ERRORLEVEL%"

if not "%TRADEVELOCITY_EXIT_CODE%"=="0" (
    echo.
    echo TradeVelocity could not start. Review the error above.
    pause
)

popd
endlocal & exit /b %TRADEVELOCITY_EXIT_CODE%
