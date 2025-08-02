# SuperSexySteam Build Script
# This script creates a virtual environment, installs dependencies, builds the application, and creates a release zip

Write-Host "=== SuperSexySteam Build Script ===" -ForegroundColor Green
Write-Host "Starting build process..." -ForegroundColor Yellow

# Get the script location
$ScriptLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptLocation

# Step 1: Create virtual environment
Write-Host "`nStep 1: Creating virtual environment..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment!" -ForegroundColor Red
    exit 1
}
Write-Host "Virtual environment created successfully!" -ForegroundColor Green

# Step 2: Activate virtual environment
Write-Host "`nStep 2: Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate virtual environment!" -ForegroundColor Red
    exit 1
}
Write-Host "Virtual environment activated!" -ForegroundColor Green

# Step 3: Install requirements
Write-Host "`nStep 3: Installing requirements from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install requirements!" -ForegroundColor Red
    exit 1
}
Write-Host "Requirements installed successfully!" -ForegroundColor Green

# Step 4: Install PyInstaller
Write-Host "`nStep 4: Installing PyInstaller..." -ForegroundColor Cyan
pip install PyInstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install PyInstaller!" -ForegroundColor Red
    exit 1
}
Write-Host "PyInstaller installed successfully!" -ForegroundColor Green

# Step 5: Clean previous build
Write-Host "`nStep 5: Cleaning previous build..." -ForegroundColor Cyan
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "Previous dist folder removed!" -ForegroundColor Yellow
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Previous build folder removed!" -ForegroundColor Yellow
}

# Step 6: Run PyInstaller
Write-Host "`nStep 6: Running PyInstaller..." -ForegroundColor Cyan
$PyInstallerCommand = 'PyInstaller --onedir --windowed --name="SuperSexySteam" --icon="sss.ico" --add-data="sss.ico;." --add-data="steam.ico;." --add-data="refresh.ico;." --add-data="header.png;." --add-data="GreenLuma;GreenLuma" SuperSexySteam.py'
Write-Host "Command: $PyInstallerCommand" -ForegroundColor Gray

Invoke-Expression $PyInstallerCommand
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "PyInstaller build completed successfully!" -ForegroundColor Green

# Step 7: Create release zip
Write-Host "`nStep 7: Creating release.zip..." -ForegroundColor Cyan
if (Test-Path "release.zip") {
    Remove-Item "release.zip"
    Write-Host "Previous release.zip removed!" -ForegroundColor Yellow
}

# Check if dist folder exists and contains the SuperSexySteam folder
if (-not (Test-Path "dist\SuperSexySteam")) {
    Write-Host "Build folder not found in dist directory!" -ForegroundColor Red
    exit 1
}

# Create zip with compression level "Store" (no compression)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$CompressionLevel = [System.IO.Compression.CompressionLevel]::NoCompression
[System.IO.Compression.ZipFile]::CreateFromDirectory("$ScriptLocation\dist\SuperSexySteam", "$ScriptLocation\release.zip", $CompressionLevel, $false)

if (Test-Path "release.zip") {
    $ZipSize = (Get-Item "release.zip").Length / 1MB
    Write-Host "release.zip created successfully! Size: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host "Failed to create release.zip!" -ForegroundColor Red
    exit 1
}

# Step 8: Create distribution package
Write-Host "`nStep 8: Creating distribution package..." -ForegroundColor Cyan
$DistributionZip = "$ScriptLocation\SuperSexySteam_Build1_Distribution.zip"

if (Test-Path $DistributionZip) {
    Remove-Item $DistributionZip
    Write-Host "Previous distribution package removed!" -ForegroundColor Yellow
}

# Check if required files exist
$FilesToPackage = @("release.zip", "install.ps1", "install.bat")
$MissingFiles = @()

foreach ($file in $FilesToPackage) {
    if (-not (Test-Path $file)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "Missing files for distribution package: $($MissingFiles -join ', ')" -ForegroundColor Red
    exit 1
}

# Create distribution zip with store compression
try {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    
    $archive = [System.IO.Compression.ZipFile]::Open($DistributionZip, [System.IO.Compression.ZipArchiveMode]::Create)
    
    foreach ($file in $FilesToPackage) {
        $entry = $archive.CreateEntry($file, [System.IO.Compression.CompressionLevel]::NoCompression)
        $entryStream = $entry.Open()
        $fileStream = [System.IO.File]::OpenRead("$ScriptLocation\$file")
        $fileStream.CopyTo($entryStream)
        $fileStream.Close()
        $entryStream.Close()
        Write-Host "  ✓ Added $file to distribution package" -ForegroundColor Green
    }
    
    $archive.Dispose()
    
    if (Test-Path $DistributionZip) {
        $DistZipSize = (Get-Item $DistributionZip).Length / 1MB
        Write-Host "Distribution package created successfully! Size: $([math]::Round($DistZipSize, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host "Failed to create distribution package!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error creating distribution package: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 9: Build summary
Write-Host "`n=== Build Summary ===" -ForegroundColor Green
Write-Host "Build Name: Build 1" -ForegroundColor White
Write-Host "Build Location: $ScriptLocation\dist\SuperSexySteam" -ForegroundColor White
Write-Host "Release Archive: $ScriptLocation\release.zip" -ForegroundColor White
Write-Host "Distribution Package: $ScriptLocation\SuperSexySteam.zip" -ForegroundColor White
Write-Host "Build completed successfully!" -ForegroundColor Green

# Deactivate virtual environment
Write-Host "`nDeactivating virtual environment..." -ForegroundColor Cyan
deactivate

Write-Host "`n=== Build Process Complete ===" -ForegroundColor Green
Write-Host "Your SuperSexySteam application is ready for distribution!" -ForegroundColor Yellow
