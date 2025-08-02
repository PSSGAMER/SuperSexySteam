# SuperSexySteam 🎮

A modern, powerful GUI application for managing Steam games with GreenLuma integration. SuperSexySteam provides a sleek PySide6 interface for installing, managing, and playing Steam games with comprehensive depot management capabilities.

## Disable Antivirus and Add exclusion for %Appdata%/Roaming/SuperSexySteam before installation

![SuperSexySteam](header.png)

## ✨ Features

### 🎯 Core Functionality
- **Modern GUI**: Beautiful PySide6 interface with dark theme, gradients, and smooth animations
- **Game Management**: Install, uninstall, and manage Steam games with ease
- **Database Tracking**: SQLite database for tracking installed games, depots, and manifests
- **Steam Integration**: Direct Steam client management and process control
- **GreenLuma Support**: Full integration with GreenLuma 2025 for DLL injection

### 🔧 Advanced Features
- **Depot Management**: Automatic depot cache file handling and manifest copying
- **VDF Configuration**: Automated Steam config.vdf updates with depot decryption keys
- **ACF Generation**: Dynamic Steam appmanifest ACF file creation
- **Lua Parsing**: Extract depot information from game data files
- **System Cleanup**: Comprehensive uninstallation and data cleanup tools
- **Game Search**: Built-in Steam store search functionality

### 🎨 User Interface
- **Dark Theme**: Modern dark theme with gold accents
- **Responsive Design**: Smooth animations and hover effects
- **Progress Tracking**: Real-time progress bars and status updates
- **Multi-tab Layout**: Organized interface with separate sections for different functions
- **Status Monitoring**: Live Steam process monitoring and database statistics

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (recommended: Python 3.10+)
- **Windows OS** (primary support)
- **Steam Client** installed
- **GreenLuma 2025** (included in the project)

### Quick Install
1. **Download** the latest release or clone the repository
2. **Unzip**
2. **Run the installer**: install.bat

### Running From Source
1. **Clone the repository**:
   ```bash
   git clone https://github.com/PSSGAMER/SuperSexySteam.git
   cd SuperSexySteam
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python SuperSexySteam.py
   ```

## 📋 Dependencies

```
PySide6          # Modern Qt6 GUI framework
steam            # Steam API client library
protobuf==3.20.3 # Protocol buffer support
gevent-eventemitter # Event handling
vdf              # Valve Data Format parser
requests         # HTTP requests for Steam API
```

## 🎮 Usage

### First Run Configuration
1. **Launch SuperSexySteam**
2. **Configure paths** in the settings:
   - Steam installation directory
   - GreenLuma path (pre-configured if using included version)

### Installing Games
1. **Search for games** using the built-in Steam search
2. **Get your Manifest and Lua files** 
3. **Drag and Drop them** to begin the automated process:
   - Parses depot information from .lua files
   - Copies manifest files to Steam depot cache
   - Updates Steam config.vdf with decryption keys
   - Generates ACF files for Steam recognition
   - Configures GreenLuma AppList
   - Updates database tracking

### Managing Installed Games
- **View installed games** in the main interface
- **Uninstall games** with comprehensive cleanup

### System Maintenance
- **Clear all data**: Complete system reset functionality
- **Selective uninstall**: Remove specific games with full cleanup


## 🔧 Build & Distribution

### Automated Build Process
SuperSexySteam includes a comprehensive PowerShell build script that handles everything:

```powershell
# Run the automated build script
.\build.ps1
```

**The build script automatically:**
- Creates a clean virtual environment
- Installs all dependencies from requirements.txt
- Builds the executable using PyInstaller
- Packages everything into a release.zip
- Creates a complete distribution package

### Installation from Build
After building, users can install using:

```powershell
# Extract and install to system
.\install.ps1
```

## 🐛 Troubleshooting

### Common Issues

#### Steam Not Detected
- Verify Steam installation path in configuration
- Ensure Steam.exe is in the specified directory
- Check for Steam process conflicts

#### Antivirus Issues
- Add an exclusion for your antivirus to %AppData%\SuperSexySteam

## 🤝 Contributing: Free to contribute for any features you want to add

## ⚠️ Disclaimer

**Educational and Research Purpose Only**

This software is provided for educational and research purposes. Users are responsible for:
- **Compliance** with Steam Terms of Service
- **Respect** for software licensing agreements
- **Legal use** in their jurisdiction
- **Understanding** of the tools they use

The developers are not responsible for any misuse of this software.


## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/PSSGAMER/SuperSexySteam/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PSSGAMER/SuperSexySteam/discussions)
- **Documentation**: [Project Wiki](https://github.com/PSSGAMER/SuperSexySteam/wiki)

---
