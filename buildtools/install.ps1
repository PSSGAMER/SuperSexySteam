# SuperSexySteam Install Script
# This script extracts the release.zip to AppData/Roaming and creates desktop shortcuts

Write-Host "=== SuperSexySteam Install Script ===" -ForegroundColor Green
Write-Host "Starting installation process..." -ForegroundColor Yellow

# Check if running with administrator privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges to add Windows Defender exclusions." -ForegroundColor Red
    Write-Host "Please run install.bat to restart with administrator privileges." -ForegroundColor Yellow
    exit 1
}

Write-Host "Running with administrator privileges." -ForegroundColor Green

# Get the script location (where the user extracted the distribution package)
$ScriptLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptLocation

# Define paths
$AppDataRoaming = [Environment]::GetFolderPath("ApplicationData")
$InstallPath = Join-Path $AppDataRoaming "SuperSexySteam"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ReleaseZip = Join-Path $ScriptLocation "release.zip"

# Step 1: Add Windows Defender exclusion for installation path
Write-Host "`nStep 1: Adding Windows Defender exclusion..." -ForegroundColor Cyan
try {
    Write-Host "Adding exclusion for: $InstallPath" -ForegroundColor Yellow
    
    # Check if Windows Defender is available
    if (Get-Command "Add-MpPreference" -ErrorAction SilentlyContinue) {
        # Add path exclusion for the installation directory
        Add-MpPreference -ExclusionPath $InstallPath -Force
        Write-Host "✓ Windows Defender exclusion added successfully!" -ForegroundColor Green
        
        # Also add exclusion for GreenLuma files specifically
        $GreenLumaPath = Join-Path $InstallPath "_internal\GreenLuma"
        Add-MpPreference -ExclusionPath $GreenLumaPath -Force
        Write-Host "✓ GreenLuma directory exclusion added!" -ForegroundColor Green
        
        # Add process exclusions for main executables
        $MainExePath = Join-Path $InstallPath "SuperSexySteam.exe"
        $DLLInjectorPath = Join-Path $InstallPath "_internal\GreenLuma\NormalMode\DLLInjector.exe"
        
        Add-MpPreference -ExclusionProcess $MainExePath -Force
        Add-MpPreference -ExclusionProcess $DLLInjectorPath -Force
        Write-Host "✓ Process exclusions added for main executables!" -ForegroundColor Green
        
    } else {
        Write-Host "⚠ Windows Defender PowerShell module not available. Skipping exclusions." -ForegroundColor Yellow
        Write-Host "  You may need to manually add exclusions for: $InstallPath" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Failed to add Windows Defender exclusion: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  Installation will continue, but you may need to manually add exclusions." -ForegroundColor Yellow
}

# Step 2: Check if release.zip exists
Write-Host "`nStep 2: Checking for release.zip..." -ForegroundColor Cyan
if (-not (Test-Path $ReleaseZip)) {
    Write-Host "release.zip not found in script directory!" -ForegroundColor Red
    Write-Host "Please make sure release.zip exists in: $ScriptLocation" -ForegroundColor Yellow
    exit 1
}
Write-Host "release.zip found!" -ForegroundColor Green

# Step 3: Prepare installation directory
Write-Host "`nStep 3: Preparing installation directory..." -ForegroundColor Cyan
if (Test-Path $InstallPath) {
    Write-Host "Previous installation found. Removing old files..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $InstallPath
}

New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Write-Host "Installation directory prepared: $InstallPath" -ForegroundColor Green

# Step 4: Extract release.zip
Write-Host "`nStep 4: Extracting release.zip to AppData/Roaming..." -ForegroundColor Cyan
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ReleaseZip, $InstallPath)
    Write-Host "Extraction completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to extract release.zip: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Verify extracted files and define paths
Write-Host "`nStep 5: Verifying extracted files..." -ForegroundColor Cyan

# Define paths for executable and icon files
$MainExe = Join-Path $InstallPath "SuperSexySteam.exe"
$MainIcon = Join-Path $InstallPath "_internal\sss.ico"
$SteamIcon = Join-Path $InstallPath "_internal\steam.ico"
$DLLInjector = Join-Path $InstallPath "_internal\GreenLuma\NormalMode\DLLInjector.exe"

# Verify critical files exist
$CriticalFiles = @($MainExe, $MainIcon, $SteamIcon, $DLLInjector)
$MissingFiles = @()

foreach ($file in $CriticalFiles) {
    if (-not (Test-Path $file)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "⚠ Some files are missing after extraction:" -ForegroundColor Yellow
    foreach ($missing in $MissingFiles) {
        Write-Host "  - $missing" -ForegroundColor Red
    }
    Write-Host "Installation will continue, but some shortcuts may not work properly." -ForegroundColor Yellow
} else {
    Write-Host "✓ All critical files verified successfully!" -ForegroundColor Green
}


# Step 6: Create desktop shortcuts
Write-Host "`nStep 6: Creating desktop shortcuts..." -ForegroundColor Cyan

# Create WScript.Shell object for shortcuts
$WScriptShell = New-Object -ComObject WScript.Shell

# Create SuperSexySteam shortcut
$SuperSexySteamShortcut = $WScriptShell.CreateShortcut((Join-Path $DesktopPath "SuperSexySteam.lnk"))
$SuperSexySteamShortcut.TargetPath = $MainExe
$SuperSexySteamShortcut.WorkingDirectory = $InstallPath
$SuperSexySteamShortcut.IconLocation = "$MainIcon,0"
$SuperSexySteamShortcut.Description = "SuperSexySteam - Steam Game Manager"
$SuperSexySteamShortcut.Save()

if (Test-Path (Join-Path $DesktopPath "SuperSexySteam.lnk")) {
    Write-Host "✓ SuperSexySteam shortcut created successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create SuperSexySteam shortcut!" -ForegroundColor Red
}

# Create Steam (DLLInjector) shortcut
$SteamShortcut = $WScriptShell.CreateShortcut((Join-Path $DesktopPath "Steam (GreenLuma).lnk"))
$SteamShortcut.TargetPath = $DLLInjector
$SteamShortcut.WorkingDirectory = (Split-Path $DLLInjector)
$SteamShortcut.IconLocation = "$SteamIcon,0"
$SteamShortcut.Description = "Steam with GreenLuma - DLL Injector"
$SteamShortcut.Save()

if (Test-Path (Join-Path $DesktopPath "Steam (GreenLuma).lnk")) {
    Write-Host "✓ Steam (GreenLuma) shortcut created successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create Steam (GreenLuma) shortcut!" -ForegroundColor Red
}

# Step 7: Installation summary
Write-Host "`n=== Installation Summary ===" -ForegroundColor Green
Write-Host "Installation Location: $InstallPath" -ForegroundColor White
Write-Host "Desktop Shortcuts:" -ForegroundColor White
Write-Host "  • SuperSexySteam.lnk" -ForegroundColor White
Write-Host "  • Steam (GreenLuma).lnk" -ForegroundColor White

# Calculate installation size
$InstallSize = (Get-ChildItem -Recurse $InstallPath | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Installation Size: $([math]::Round($InstallSize, 2)) MB" -ForegroundColor White

Write-Host "`nInstallation completed successfully!" -ForegroundColor Green

Write-Host "`n=== Installation Complete ===" -ForegroundColor Green
Write-Host "SuperSexySteam has been installed to your system!" -ForegroundColor Yellow
Write-Host "You can now run the application from the desktop shortcuts." -ForegroundColor Yellow
