# Create Distribution Package Script
# This script creates a SuperSexySteam.zip file for distribution

param(
    [string]$OutputDir = ".",
    [switch]$IncludeInstallers = $false
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipPath = Join-Path $OutputDir "SuperSexySteam.zip"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "SuperSexySteam Package Creator" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Files to include in the zip
$FilesToInclude = @(
    "SuperSexySteam.py",
    "refresh.py", 
    "acfgen.py",
    "requirements.txt",
    "README.md",
    "header.png",
    "*.ico",
    "GreenLuma"
)

# Files to exclude (installer files)
$FilesToExclude = @(
    "install.ps1", 
    "install_launcher.bat",
    "install_config.ps1",
    "create_package.ps1",
    "fix_shortcuts.ps1",
    "INSTALLER_README.md",
    "__pycache__",
    "*.zip"
)

Write-Host "Creating SuperSexySteam.zip package..." -ForegroundColor Yellow
Write-Host "Output location: $ZipPath" -ForegroundColor Cyan
Write-Host ""

# Remove existing zip if it exists
if (Test-Path $ZipPath) {
    Write-Host "Removing existing SuperSexySteam.zip..." -ForegroundColor Yellow
    Remove-Item $ZipPath -Force
}

# Create temporary directory for packaging
$TempDir = Join-Path $env:TEMP "SuperSexySteam_Package"
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "Copying files to temporary directory..." -ForegroundColor Yellow

# Copy all files except excluded ones
Get-ChildItem -Path $ProjectDir | ForEach-Object {
    $shouldExclude = $false
    
    # Check if file should be excluded
    foreach ($exclude in $FilesToExclude) {
        if ($_.Name -like $exclude) {
            $shouldExclude = $true
            break
        }
    }
    
    if (-not $shouldExclude) {
        if ($_.PSIsContainer) {
            # Copy directory
            Copy-Item -Path $_.FullName -Destination $TempDir -Recurse -Force
            Write-Host "  + Copied directory: $($_.Name)" -ForegroundColor Green
        } else {
            # Copy file
            Copy-Item -Path $_.FullName -Destination $TempDir -Force
            Write-Host "  + Copied file: $($_.Name)" -ForegroundColor Green
        }
    } else {
        Write-Host "  - Excluded: $($_.Name)" -ForegroundColor DarkGray
    }
}

# Create the zip file
Write-Host ""
Write-Host "Creating zip archive..." -ForegroundColor Yellow
try {
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force -CompressionLevel Fastest
    Write-Host "Package created successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create zip package." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    # Clean up temporary directory
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
    }
}

# Show package info
$ZipInfo = Get-Item $ZipPath
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Package Information:" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "File: $($ZipInfo.Name)" -ForegroundColor Cyan
Write-Host "Size: $([math]::Round($ZipInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host "Location: $($ZipInfo.FullName)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Distribution package ready!" -ForegroundColor Green
Write-Host ""

# Create release.zip with package and installer files
Write-Host "Creating release.zip with installer files..." -ForegroundColor Yellow
$ReleasePath = Join-Path $OutputDir "release.zip"

# Remove existing release.zip if it exists
if (Test-Path $ReleasePath) {
    Write-Host "Removing existing release.zip..." -ForegroundColor Yellow
    Remove-Item $ReleasePath -Force
}

# Create temporary directory for release
$ReleaseTempDir = Join-Path $env:TEMP "SuperSexySteam_Release"
if (Test-Path $ReleaseTempDir) {
    Remove-Item $ReleaseTempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $ReleaseTempDir -Force | Out-Null

# Copy the SuperSexySteam.zip package
Copy-Item -Path $ZipPath -Destination $ReleaseTempDir -Force
Write-Host "  + Added: SuperSexySteam.zip" -ForegroundColor Green

# Copy installer files
$InstallerFiles = @(
    "install.ps1", 
    "install_launcher.bat",
    "install_config.ps1",
    "fix_shortcuts.ps1",
    "fix_shortcuts.bat",
    "INSTALLER_README.md"
)

foreach ($file in $InstallerFiles) {
    $filePath = Join-Path $ProjectDir $file
    if (Test-Path $filePath) {
        Copy-Item -Path $filePath -Destination $ReleaseTempDir -Force
        Write-Host "  + Added: $file" -ForegroundColor Green
    }
}

# Create the release zip file
try {
    Compress-Archive -Path "$ReleaseTempDir\*" -DestinationPath $ReleasePath -Force -CompressionLevel Fastest
    Write-Host "Release package created successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create release package." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    # Clean up release temporary directory
    if (Test-Path $ReleaseTempDir) {
        Remove-Item $ReleaseTempDir -Recurse -Force
    }
}

# Show release package info
if (Test-Path $ReleasePath) {
    $ReleaseInfo = Get-Item $ReleasePath
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Release Package Information:" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "File: $($ReleaseInfo.Name)" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($ReleaseInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "Location: $($ReleaseInfo.FullName)" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "To distribute SuperSexySteam:" -ForegroundColor Yellow
Write-Host "1. Share the release.zip file - it contains everything needed" -ForegroundColor White
Write-Host "2. Users extract release.zip and run install_launcher.bat" -ForegroundColor White
Write-Host "3. If users have shortcut issues, they can run fix_shortcuts.ps1" -ForegroundColor White
Write-Host ""
