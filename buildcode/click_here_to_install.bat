@echo off
:: SuperSexySteam Installer Launcher
:: This batch file runs the PowerShell installer with proper execution policy

echo ==========================================
echo SuperSexySteam Installer Launcher
echo ==========================================
echo.

:: Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell detected'" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell or use Windows 10/11.
    echo.
    pause
    exit /b 1
)

:: Run PowerShell installer
echo Running PowerShell installer...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

echo.
echo Installation process completed.
pause
