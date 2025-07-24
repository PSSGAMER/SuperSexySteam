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
3. **Run the installer** by double-clicking `click_here_to_install.bat`
4. **Follow the installation prompts** - the installer will:
   - Extract SuperSexySteam to `%APPDATA%\SuperSexySteam`
   - Create a Python virtual environment
   - Install all required dependencies
   - Create desktop shortcuts for easy access

**Requirements:** Windows 10/11, Python 3.8+

---

## 🔧 Common Workflow

Here's the new streamlined workflow for using SuperSexySteam:

1. **Setup** (one-time)
   - Install SuperSexySteam using the installer
   - Or set up development environment from source

2. **Process Content** (simplified drag-and-drop workflow)
   - Launch SuperSexySteam
   - Drag `.lua` files (and any associated `.manifest` files) into the interface
   - Click "Apply" to automatically trigger the complete processing pipeline:
     - ✅ **GreenLuma AppList Management** - Adds AppIDs and DepotIDs to GreenLuma
     - ✅ **Depot Cache Processing** - Copies manifest files to Steam's depot cache
     - ✅ **Steam Config Update** - Updates config.vdf with depot decryption keys
     - ✅ **ACF Generation** - Creates Steam app manifests for game recognition

3. **Start Steam**
   - Launch "DLL Injector" to start Steam with GreenLuma
   - Your configured depots will be available and games recognized

4. **Optional: Manual Refresh**
   - The refresh.py script is available but currently contains no logic
   - All necessary processing is handled automatically in step 2

5. **Troubleshooting**
   - Check the console output for detailed processing information
   - Verify that Steam and GreenLuma paths are correctly configured

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
   ├── click_here_to_install.bat   (main installer)
   ├── install.ps1                 (PowerShell installer)
   └── install_config.ps1          (customizable installer)
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

3. **Apply Changes** (Complete Processing Pipeline)
   - Click the "Apply" button when ready
   - The system automatically processes everything in sequence:
     - **Step 1:** Updates GreenLuma AppList with new AppIDs and DepotIDs
     - **Step 2:** Copies manifest files to Steam's depot cache
     - **Step 3:** Updates Steam's config.vdf with depot decryption keys
     - **Step 4:** Launches ACF generator for Steam app recognition
   - No additional manual steps required!

### Database Refresh (Optional)

The refresh script is available but currently contains no logic:

1. **refresh.py** 
   - Available for future manual refresh operations
   - Currently a placeholder with no active functionality
   - All necessary processing happens automatically when you click "Apply"

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

- [ ] Enhanced Shared Depot Handling
- [ ] Improved Installer System
- [ ] Auto-Updater

### 🎯 Additional Enhancements (Later)
- **Improved UI/UX:** More intuitive interface with better visual feedback
- **Custom Emulator:** Move away from GreenLuma dependency with a custom solution
- **Enhanced Logging:** Better debugging and troubleshooting capabilities

---

## 🤝 Contributing

Contributions are welcome! If you have improvements or can help with compilation into a standalone executable, please don't hesitate to make a Pull Request.

## 📄 License

This project is provided as-is for educational and research purposes. Please respect game developers and publishers by purchasing games you enjoy.
