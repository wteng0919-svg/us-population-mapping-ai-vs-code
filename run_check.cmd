@echo off
rem Double-click helper for Windows: run the join-quality check.
rem Requires the GADM .dbf in data\ (see data\README.md).
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 code\verify_join_quality.py %*
) else (
    python code\verify_join_quality.py %*
)

echo.
pause
