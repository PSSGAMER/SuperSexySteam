# SuperSexySteam Installer

This installer will automatically set up SuperSexySteam on your Windows system from a zip package.

## What the installer does:

1. **Extracts SuperSexySteam.zip** to `C:\Program Files (x86)\SuperSexySteam`
2. **Creates a Python virtual environment** in the installation directory
3. **Installs all required dependencies** from `requirements.txt`
4. **Creates desktop shortcuts** for:
   - SuperSexySteam (main application)
   - SuperSexySteam Refresher (database refresh tool)
   - DLL Injector (GreenLuma tool)

## Installation Options:

### Option 1: Quick Install (Recommended)
Double-click `install_launcher.bat` - this will run the PowerShell installer with proper execution policy.

### Option 2: Direct PowerShell Install
Right-click `install.ps1` and select "Run with PowerShell" or double-click `install_config.ps1` to use custom settings.

**Important:** Make sure `SuperSexySteam.zip` is in the same folder as the installer files!

## Customizing Installation Location:

### Method 1: Edit Configuration File
1. Open `install_config.ps1` in a text editor
2. Change the `$INSTALL_LOCATION` variable to your preferred path
3. Double-click `install_config.ps1` to run the installer

### Method 2: Edit PowerShell Script Directly
1. Open `install.ps1` in a text editor
2. Change the default value in the `param()` section at the top:
   ```powershell
   param(
       [string]$InstallDir = "YOUR_CUSTOM_PATH_HERE"
   )
   ```

## For Developers - Creating Distribution Package:

To create the `SuperSexySteam.zip` file for distribution:

### Option 1: PowerShell (Recommended)
Double-click `create_package.ps1` or run it from PowerShell.

This will create `SuperSexySteam.zip` containing all necessary project files (excluding installer files and temporary directories).

### Distribution Structure:
```
Distribution Folder/
├── SuperSexySteam.zip          (created by package script)
├── install_launcher.bat        (main installer launcher)
├── install.ps1                 (PowerShell installer)
├── install_config.ps1          (customizable installer)
└── INSTALLER_README.md         (this file)
```

Users only need to download this folder and run `install_launcher.bat`.

## Requirements:

- **Windows 10/11** (or Windows 7+ with PowerShell)
- **Python 3.8 or newer** installed and added to PATH
- **Administrator privileges** (required for Program Files installation)

## Installation Directory Examples:

- `C:\Program Files (x86)\SuperSexySteam` (default)
- `C:\SuperSexySteam`
- `D:\Games\SuperSexySteam`
- `%USERPROFILE%\SuperSexySteam` (user directory)

## Troubleshooting:

### "Python not found" error:
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### "SuperSexySteam.zip not found" error:
- Make sure `SuperSexySteam.zip` is in the same folder as the installer files
- The zip file and installer must be in the same directory

### "Access denied" error:
- Run the installer as Administrator
- Right-click the installer file and select "Run as administrator"

### PowerShell execution policy error:
- Use `install_launcher.bat` instead, which bypasses execution policy
- Or run PowerShell as Administrator and execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Virtual environment creation fails:
- Ensure you have the latest version of Python
- Try running: `python -m pip install --upgrade pip setuptools`

## Uninstalling:

To uninstall SuperSexySteam:
1. Delete the installation directory (e.g., `C:\Program Files (x86)\SuperSexySteam`)
2. Delete the desktop shortcuts
3. No registry entries or system files are modified by this installer

## Files Created:

**Installation Directory:**
- All project files and dependencies
- `venv\` folder containing the Python virtual environment

**Desktop Shortcuts:**
- `SuperSexySteam.lnk`
- `SuperSexySteam Refresher.lnk`
- `DLL Injector.lnk`
