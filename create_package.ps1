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
Write-Host "To distribute SuperSexySteam:" -ForegroundColor Yellow
Write-Host "1. Copy SuperSexySteam.zip and the installer files to the same folder" -ForegroundColor White
Write-Host "2. Users can then run install_launcher.bat to install" -ForegroundColor White
Write-Host "3. If users have shortcut issues, provide fix_shortcuts.ps1" -ForegroundColor White
Write-Host ""
