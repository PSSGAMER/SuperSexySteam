# BuildTools Directory

This directory contains the build and installation scripts for SuperSexySteam.

## Files

- **build.ps1** - Main build script that creates the application package
- **install.ps1** - PowerShell installation script that installs the application to AppData
- **install.bat** - Batch file wrapper that runs install.ps1 with administrator privileges
- **README.md** - This documentation file

## Usage

### Building the Application

From the project root directory, run:
```powershell
.\buildtools\build.ps1
```

This will:
1. Create a virtual environment
2. Install dependencies
3. Build the application with PyInstaller
4. Create a release.zip in the buildtools folder
5. Create a SuperSexySteam.zip distribution package in the buildtools folder
6. Clean up the temporary release.zip file

### Installing the Application

The build process creates a `SuperSexySteam.zip` file that contains:
- release.zip (the main application files)
- install.ps1 (PowerShell installation script)
- install.bat (batch wrapper for install.ps1)

Users can extract this zip file and run `install.bat` to install the application with administrator privileges.

## Directory Structure After Build

```
buildtools/
├── build.ps1
├── install.ps1
├── install.bat
├── README.md
└── SuperSexySteam.zip (distribution package)
```

The distribution package contains all files needed for installation and can be shared with users.
