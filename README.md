# SuperSexySteam

A powerful tool for Steam depot management that works in conjunction with GreenLuma. This tool helps you manage Steam depot files and provides an intuitive interface for processing .lua and .manifest files.

**Note:** GreenLuma by Steam006 is included for convenience. If Steam006 has any concerns, please contact me and I will remove it. The eventual plan is to implement a custom emulator solution.

---

## 📋 Table of Contents

- [🎯 Quick Start (Recommended)](#-quick-start-recommended)
- [🔧 Common Workflow](#-common-workflow)
- [🔧 Run from Source](#-run-from-source) 
- [📦 Build Distribution Package](#-build-distribution-package)
- [🎮 How to Use SuperSexySteam](#-how-to-use-supersexystemsteam)
- [⚙️ Prerequisites](#️-prerequisites)
- [🚀 Planned Features](#-planned-features)
- [🤝 Contributing](#-contributing)

---

## 🎯 Quick Start (Recommended)

### For End Users - Download Release

The easiest way to install SuperSexySteam is using the automated installer:

1. **Download the latest release** from the [Releases page](https://github.com/PSSGAMER/SuperSexySteam/releases)
2. **Extract the installer package** to any folder
3. **Run the installer** by double-clicking `install_launcher.bat`
4. **Follow the installation prompts** - the installer will:
   - Extract SuperSexySteam to `C:\Program Files (x86)\SuperSexySteam`
   - Create a Python virtual environment
   - Install all required dependencies
   - Create desktop shortcuts for easy access

**Requirements:** Windows 10/11, Python 3.8+, Administrator privileges

📖 **Need help?** See the included `INSTALLER_README.md` for detailed installation instructions and troubleshooting.

---

## 🔧 Common Workflow

Here's the typical workflow for using SuperSexySteam:

1. **Setup** (one-time)
   - Install SuperSexySteam using the installer
   - Or set up development environment from source

2. **Add Content**
   - Launch SuperSexySteam
   - Drag `.lua` and `.manifest` files into the interface
   - Click "Apply" to process

3. **Refresh Database**
   - Run "SuperSexySteam Refresher" before each Steam session
   - This ensures your configuration is up-to-date

4. **Start Steam**
   - Launch "DLL Injector" to start Steam with GreenLuma
   - Your configured depots will be available

5. **Troubleshooting**
   - Re-run the refresher if you encounter download issues
   - Check that all files are properly configured

---

## 🔧 Run from Source

### For Developers and Advanced Users

If you want to run SuperSexySteam directly from source code:

#### Prerequisites
- **Python 3.8 or newer** - Download from [python.org](https://www.python.org/downloads/)
- **Git** - Download from [git-scm.com](https://git-scm.com/downloads)

#### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/PSSGAMER/SuperSexySteam.git
   cd SuperSexySteam
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate Virtual Environment**
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**
   ```bash
   python SuperSexySteam.py
   ```

---

## 📦 Build Distribution Package

### For Contributors and Distributors

To create a distribution package with the installer:

1. **Ensure you have the source code** (see "Run from Source" section)

2. **Create the distribution package**
   ```powershell
   # Run the package creation script
   powershell -ExecutionPolicy Bypass -File create_package.ps1
   ```
   
   Or double-click `create_package.ps1` in Windows Explorer.

3. **Package Contents**
   This creates `SuperSexySteam.zip` containing:
   - All Python source files
   - Required assets (icons, etc.)
   - GreenLuma integration files
   - Requirements file

4. **Create Distribution Folder**
   For release, include these files together:
   ```
   SuperSexySteam_Release/
   ├── SuperSexySteam.zip          (created by package script)
   ├── install_launcher.bat        (main installer)
   ├── install.ps1                 (PowerShell installer)
   ├── install_config.ps1          (customizable installer)
   └── INSTALLER_README.md         (installation guide)
   ```

---

## 🎮 How to Use SuperSexySteam

### First-Time Setup

When you launch SuperSexySteam for the first time:

1. **Steam Path Configuration**
   - You'll be prompted to enter your Steam installation path
   - Default: `C:\Program Files (x86)\Steam`
   - Leave empty to use the default

2. **GreenLuma Path Configuration**
   - Specify your GreenLuma directory
   - Default: `GreenLuma` folder in the project directory
   - Leave empty to use the default

These settings are saved to `config.ini` and won't be asked again.

### Using the Main Application

1. **Launch SuperSexySteam**
   - From desktop shortcut (if installed via installer)
   - Or run: `python SuperSexySteam.py` (if running from source)

2. **Add Depot Files**
   - Drag and drop `.lua` files (named as `<AppID>.lua`)
   - Include any associated `.manifest` files
   - Files are organized into `data/<AppID>/` directories

3. **Apply Changes**
   - Click the "Apply" button when ready
   - The system will categorize new vs. updated AppIDs
   - Data processing script runs automatically

### Database Refresh

**Important:** Always run the refresh script before starting Steam:

1. **Run SuperSexySteam Refresher**
   - From desktop shortcut: "SuperSexySteam Refresher"
   - Or run: `python refresh.py`

2. **What it does:**
   - Updates Steam's depot configuration
   - Refreshes the depot cache
   - Synchronizes all .manifest files

### Starting Steam with GreenLuma

1. **Launch DLL Injector**
   - From desktop shortcut: "DLL Injector"
   - Or navigate to `GreenLuma/NormalMode/` and run `DLLInjector.exe`

2. **Steam Integration**
   - This starts Steam with GreenLuma integration
   - Allows access to configured depots

---

## ⚙️ Prerequisites

### System Requirements
- **Operating System:** Windows 7+ (Windows 10/11 recommended)
- **Python:** Version 3.8 or newer
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 500MB free space (more for game depots)

### Software Dependencies
- **Python Packages:** (automatically installed)
  - `customtkinter` - Modern UI framework
  - `tkinterdnd2` - Drag and drop support
  - `Pillow` - Image processing
  - `steam` - Steam API integration
  - `protobuf==3.20.3` - Protocol buffer support
  - `gevent-eventemitter` - Event handling

### Optional Tools
- **Git** - For cloning the repository (development only)
- **PowerShell** - For running installation scripts (Windows 7+ has this built-in)

---

## 🚀 Planned Features

The following features are planned for future releases:

### 📊 Enhanced Shared Depot Handling

### 🔧 Improved Installer System

### 🔄 Auto-Updater

### 🎯 Additional Enhancements
- **Improved UI/UX:** More intuitive interface with better visual feedback
- **Custom Emulator:** Move away from GreenLuma dependency with a custom solution
- **Enhanced Logging:** Better debugging and troubleshooting capabilities

---

## 🤝 Contributing

Contributions are welcome! If you have improvements or can help with compilation into a standalone executable, please don't hesitate to make a Pull Request.

## 📄 License

This project is provided as-is for educational and research purposes. Please respect game developers and publishers by purchasing games you enjoy.
