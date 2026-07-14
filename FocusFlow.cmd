@echo off
setlocal
cd /d "%~dp0"

REM Prefer project virtual environment
if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\pythonw.exe" "%~dp0FocusFlow.pyw"
    exit /b %ERRORLEVEL%
)

REM Fall back to pythonw on PATH
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "delims=" %%P in ('where pythonw') do (
        "%%P" "%~dp0FocusFlow.pyw"
        exit /b %ERRORLEVEL%
    )
)

REM Last resort: python.exe (may show a brief console)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "delims=" %%P in ('where python') do (
        "%%P" "%~dp0FocusFlow.pyw"
        exit /b %ERRORLEVEL%
    )
)

echo FocusFlow could not find Python. Install Python 3.13+ or run: pip install -r requirements.txt
pause
exit /b 1
