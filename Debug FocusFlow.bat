@echo off
title FocusFlow Debug Launcher
cd /d "%~dp0"
echo Starting FocusFlow...
python main.py
if errorlevel 1 (
    echo.
    echo FocusFlow exited with an error.
    pause
)
