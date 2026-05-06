@echo off
setlocal EnableExtensions
title HXSS MaintenanceKit - Apply Report
cd /d "%~dp0"

echo [HXSS] Apply report started.
echo [HXSS] Working directory: %CD%
echo.

call :run_python tools\apply_report.py
set "exitcode=%ERRORLEVEL%"

echo.
if "%exitcode%"=="0" (
  echo [HXSS] Apply report completed.
) else (
  echo [HXSS] Apply report failed. Exit code: %exitcode%
)
echo.
pause
exit /b %exitcode%

:run_python
where py >nul 2>nul
if "%ERRORLEVEL%"=="0" (
  echo [HXSS] Python launcher found. Running: py -3 -X utf8 -u %*
  py -3 -X utf8 -u %*
  exit /b %ERRORLEVEL%
) else (
  where python >nul 2>nul
  if "%ERRORLEVEL%"=="0" (
    echo [HXSS] Python found. Running: python -X utf8 -u %*
    python -X utf8 -u %*
    exit /b %ERRORLEVEL%
  )
)

echo [HXSS] Python was not found. Install Python 3 or add it to PATH.
exit /b 9009
