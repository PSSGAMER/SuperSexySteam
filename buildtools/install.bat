@echo off
echo SuperSexySteam Installer
echo Requesting administrator privileges...

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Running with administrator privileges.
    goto :run_installer
) else (
    echo Requesting administrator privileges...
    :: Re-run as administrator
    powershell.exe -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

:run_installer
echo Starting PowerShell installation script with admin privileges...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
