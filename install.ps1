# SuperSexySteam Installer Script (PowerShell)
# This script installs SuperSexySteam to Program Files and creates desktop shortcuts

param(
    [string]$InstallDir = "C:\Program Files (x86)\SuperSexySteam"
)

# ==========================================
# CONFIGURATION VARIABLES
# ==========================================
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipFile = Join-Path $CurrentDir "SuperSexySteam.zip"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "SuperSexySteam Installer" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "This installer will:"
Write-Host "- Extract SuperSexySteam.zip to: $InstallDir"
Write-Host "- Create a Python virtual environment"
Write-Host "- Install required dependencies"
Write-Host "- Create desktop shortcuts"
Write-Host ""
Read-Host "Press Enter to continue"

# ==========================================
# ADMINISTRATIVE PRIVILEGES CHECK
# ==========================================
Write-Host "Checking for administrative privileges..." -ForegroundColor Yellow
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host ""
    Write-Host "ERROR: This installer requires administrative privileges." -ForegroundColor Red
    Write-Host "Please run this script as Administrator." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# PYTHON CHECK
# ==========================================
Write-Host "Checking for Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or newer and try again." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# CHECK FOR ZIP FILE
# ==========================================
Write-Host "Checking for SuperSexySteam.zip..." -ForegroundColor Yellow
if (-not (Test-Path $ZipFile)) {
    Write-Host ""
    Write-Host "ERROR: SuperSexySteam.zip not found in the same directory as this installer." -ForegroundColor Red
    Write-Host "Please ensure SuperSexySteam.zip is in the same folder as this installer." -ForegroundColor Red
    Write-Host "Expected location: $ZipFile" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# CREATE INSTALLATION DIRECTORY
# ==========================================
Write-Host ""
Write-Host "Creating installation directory..." -ForegroundColor Yellow
if (Test-Path $InstallDir) {
    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item -Path $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# ==========================================
# EXTRACT ZIP FILE
# ==========================================
Write-Host "Extracting SuperSexySteam.zip..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $ZipFile -DestinationPath $InstallDir -Force
    Write-Host "Project files extracted successfully." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to extract SuperSexySteam.zip." -ForegroundColor Red
    Write-Host "Make sure the zip file is not corrupted." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# CREATE VIRTUAL ENVIRONMENT
# ==========================================
Write-Host ""
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
Set-Location $InstallDir
try {
    & python -m venv venv
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# INSTALL REQUIREMENTS
# ==========================================
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & "$InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\requirements.txt"
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to install Python dependencies." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ==========================================
# CREATE DESKTOP SHORTCUTS
# ==========================================
Write-Host ""
Write-Host "Creating desktop shortcuts..." -ForegroundColor Yellow

# Validate required files exist
$RequiredFiles = @(
    "$InstallDir\SuperSexySteam.py",
    "$InstallDir\refresh.py", 
    "$InstallDir\GreenLuma\NormalMode\DLLInjector.exe",
    "$InstallDir\venv\Scripts\pythonw.exe"
)

$MissingFiles = @()
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "WARNING: Some required files are missing:" -ForegroundColor Yellow
    foreach ($Missing in $MissingFiles) {
        Write-Host "  - $Missing" -ForegroundColor Red
    }
    Write-Host "Shortcuts may not work correctly." -ForegroundColor Yellow
}

$WshShell = New-Object -comObject WScript.Shell

# SuperSexySteam shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\SuperSexySteam.lnk")
$Shortcut.TargetPath = "$InstallDir\venv\Scripts\python.exe"
$Shortcut.Arguments = "`"$InstallDir\SuperSexySteam.py`""
$Shortcut.WorkingDirectory = $InstallDir
# Use ICO file if available
if (Test-Path "$InstallDir\icon.ico") {
    $Shortcut.IconLocation = "$InstallDir\icon.ico"
}
$Shortcut.Description = "SuperSexySteam - Steam Depot Management Tool"
$Shortcut.Save()

# Refresher shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\SuperSexySteam Refresher.lnk")
$Shortcut.TargetPath = "$InstallDir\venv\Scripts\python.exe"
$Shortcut.Arguments = "`"$InstallDir\refresh.py`""
$Shortcut.WorkingDirectory = $InstallDir
# Use ICO file if available
if (Test-Path "$InstallDir\refreshericon.ico") {
    $Shortcut.IconLocation = "$InstallDir\refreshericon.ico"
}
$Shortcut.Description = "SuperSexySteam Refresher - Database Refresh Tool"
$Shortcut.Save()

# DLL Injector shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\DLL Injector.lnk")
$Shortcut.TargetPath = "$InstallDir\GreenLuma\NormalMode\DLLInjector.exe"
$Shortcut.WorkingDirectory = "$InstallDir\GreenLuma\NormalMode"
# Use ICO file if available
if (Test-Path "$InstallDir\icondllinjector.ico") {
    $Shortcut.IconLocation = "$InstallDir\icondllinjector.ico"
}
$Shortcut.Description = "DLL Injector - GreenLuma DLL Injection Tool"
$Shortcut.Save()

Write-Host "Desktop shortcuts created successfully." -ForegroundColor Green

# ==========================================
# INSTALLATION COMPLETE
# ==========================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "SuperSexySteam has been installed to:" -ForegroundColor Cyan
Write-Host $InstallDir -ForegroundColor White
Write-Host ""
Write-Host "The following shortcuts have been created on your desktop:" -ForegroundColor Cyan
Write-Host "- SuperSexySteam.lnk" -ForegroundColor White
Write-Host "- SuperSexySteam Refresher.lnk" -ForegroundColor White
Write-Host "- DLL Injector.lnk" -ForegroundColor White
Write-Host ""
Write-Host "You can now use SuperSexySteam from the desktop shortcuts." -ForegroundColor Green
Write-Host ""
Write-Host "TROUBLESHOOTING:" -ForegroundColor Yellow
Write-Host "If shortcuts don't work or icons don't appear:" -ForegroundColor White
Write-Host "1. Try running shortcuts as Administrator" -ForegroundColor White
Write-Host "2. Check that Python is properly installed" -ForegroundColor White
Write-Host "3. Verify all files exist in: $InstallDir" -ForegroundColor White
Write-Host "4. For icons: Try refreshing desktop (F5) or restarting Explorer" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
