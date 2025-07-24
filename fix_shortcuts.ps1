# SuperSexySteam Shortcut Fix Script
# Run this script if your desktop shortcuts are not working or showing icons

param(
    [string]$InstallDir = "C:\Program Files (x86)\SuperSexySteam"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "SuperSexySteam Shortcut Fix Tool" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Check if installation directory exists
if (-not (Test-Path $InstallDir)) {
    Write-Host "ERROR: Installation directory not found: $InstallDir" -ForegroundColor Red
    Write-Host "Please specify the correct installation path." -ForegroundColor Yellow
    $CustomPath = Read-Host "Enter the SuperSexySteam installation path (or press Enter to exit)"
    if ($CustomPath) {
        $InstallDir = $CustomPath
    } else {
        exit 1
    }
}

$DesktopDir = [Environment]::GetFolderPath("Desktop")

Write-Host "Checking installation at: $InstallDir" -ForegroundColor Cyan
Write-Host "Desktop location: $DesktopDir" -ForegroundColor Cyan
Write-Host ""

# Check required files
$RequiredFiles = @{
    "SuperSexySteam.py" = "$InstallDir\SuperSexySteam.py"
    "refresh.py" = "$InstallDir\refresh.py"
    "Python executable" = "$InstallDir\venv\Scripts\pythonw.exe"
    "DLL Injector" = "$InstallDir\GreenLuma\NormalMode\DLLInjector.exe"
    "Main icon" = "$InstallDir\icon.ico"
    "Refresher icon" = "$InstallDir\refreshericon.ico"
    "DLL Injector icon" = "$InstallDir\icondllinjector.ico"
}

$MissingFiles = @()
Write-Host "Checking required files..." -ForegroundColor Yellow
foreach ($FileDesc in $RequiredFiles.Keys) {
    $FilePath = $RequiredFiles[$FileDesc]
    if (Test-Path $FilePath) {
        Write-Host "  ✓ $FileDesc" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $FileDesc (missing: $FilePath)" -ForegroundColor Red
        $MissingFiles += $FileDesc
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Missing required files. Installation may be incomplete." -ForegroundColor Red
    Write-Host "Please reinstall SuperSexySteam or ensure ICO files are present." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "All required files found. Recreating shortcuts..." -ForegroundColor Yellow

$WshShell = New-Object -comObject WScript.Shell

# Remove existing shortcuts
$ShortcutNames = @("SuperSexySteam.lnk", "SuperSexySteam Refresher.lnk", "DLL Injector.lnk")
foreach ($ShortcutName in $ShortcutNames) {
    $ShortcutPath = "$DesktopDir\$ShortcutName"
    if (Test-Path $ShortcutPath) {
        Remove-Item $ShortcutPath -Force
        Write-Host "  Removed existing $ShortcutName" -ForegroundColor Yellow
    }
}

# Create SuperSexySteam shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\SuperSexySteam.lnk")
$Shortcut.TargetPath = "$InstallDir\venv\Scripts\pythonw.exe"
$Shortcut.Arguments = "`"$InstallDir\SuperSexySteam.py`""
$Shortcut.WorkingDirectory = $InstallDir
if (Test-Path "$InstallDir\icon.ico") {
    $Shortcut.IconLocation = "$InstallDir\icon.ico"
}
$Shortcut.Description = "SuperSexySteam - Steam Depot Management Tool"
$Shortcut.Save()
Write-Host "  ✓ Created SuperSexySteam shortcut" -ForegroundColor Green

# Create Refresher shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\SuperSexySteam Refresher.lnk")
$Shortcut.TargetPath = "$InstallDir\venv\Scripts\pythonw.exe"
$Shortcut.Arguments = "`"$InstallDir\refresh.py`""
$Shortcut.WorkingDirectory = $InstallDir
if (Test-Path "$InstallDir\refreshericon.ico") {
    $Shortcut.IconLocation = "$InstallDir\refreshericon.ico"
}
$Shortcut.Description = "SuperSexySteam Refresher - Database Refresh Tool"
$Shortcut.Save()
Write-Host "  ✓ Created SuperSexySteam Refresher shortcut" -ForegroundColor Green

# Create DLL Injector shortcut
$Shortcut = $WshShell.CreateShortcut("$DesktopDir\DLL Injector.lnk")
$Shortcut.TargetPath = "$InstallDir\GreenLuma\NormalMode\DLLInjector.exe"
$Shortcut.WorkingDirectory = "$InstallDir\GreenLuma\NormalMode"
if (Test-Path "$InstallDir\icondllinjector.ico") {
    $Shortcut.IconLocation = "$InstallDir\icondllinjector.ico"
}
$Shortcut.Description = "DLL Injector - GreenLuma DLL Injection Tool"
$Shortcut.Save()
Write-Host "  ✓ Created DLL Injector shortcut" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Shortcut fix completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "If icons still don't appear:" -ForegroundColor Yellow
Write-Host "1. Press F5 to refresh your desktop" -ForegroundColor White
Write-Host "2. Restart Windows Explorer (Ctrl+Shift+Esc > Restart explorer.exe)" -ForegroundColor White
Write-Host "3. Log out and log back in to Windows" -ForegroundColor White
Write-Host ""
Write-Host "If shortcuts still don't work:" -ForegroundColor Yellow
Write-Host "1. Try running them as Administrator" -ForegroundColor White
Write-Host "2. Check that Python is in your system PATH" -ForegroundColor White
Write-Host "3. Manually navigate to: $InstallDir" -ForegroundColor White
Write-Host "   and run: venv\Scripts\pythonw.exe SuperSexySteam.py" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
