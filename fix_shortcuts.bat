@echo off
REM SuperSexySteam Shortcut Fix Launcher
REM This runs the PowerShell shortcut fix script

echo ==========================================
echo SuperSexySteam Shortcut Fix Tool
echo ==========================================
echo.

echo This tool will:
echo - Check your SuperSexySteam installation
echo - Convert PNG icons to ICO format  
echo - Recreate desktop shortcuts
echo - Fix icon display issues
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell detected'" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell or use Windows 10/11.
    echo.
    pause
    exit /b 1
)

echo Running PowerShell fix script...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0fix_shortcuts.ps1"

echo.
echo Fix process completed.
pause
