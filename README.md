<div align="center">

# SuperSexySteam 🎮

*A modern, powerful GUI application for managing Steam games with GreenLuma integration*

</div>

---

## ⚠️ **IMPORTANT: Disable Antivirus**
> **Add an exclusion for `%AppData%\Roaming\SuperSexySteam` before installation**

---

![SuperSexySteam](header.png)

## ✨ Features

### 🎯 Core Functionality
- **Modern GUI**: Beautiful PySide6 interface with dark theme, gradients, and smooth animations
- **Game Management**: Install, uninstall, and manage Steam games with ease
- **Database Tracking**: SQLite database for tracking installed games, depots, and manifests
- **Steam Integration**: Direct Steam client management and process control
- **GreenLuma Support**: Full integration with GreenLuma 2025 for DLL injection

### 🛠️ Planned Features
- **Auto Updater**: Automatic application updates
- **Denuvo Token Integration**: Advanced DRM handling
- **Auto Game Installer & Updater**: Automated game management

## 🚀 Installation

### 📋 Prerequisites
| Requirement | Version | Status |
|-------------|---------|--------|
| **Python** | 3.8+ (recommended: 3.10+) | Required |
| **Windows OS** | Primary support | Required |
| **Steam Client** | Latest | Required |
| **GreenLuma 2025** | Included in project | Included |

### ⚡ Quick Install
1. 📥 **Download** the latest release (`SuperSexySteam.zip`)
2. 📂 **Extract** the zip file to any location
3. 🚀 **Run the installer**: `install.bat` (requires administrator privileges)

### 💻 Running From Source

<details>
<summary>Click to expand development setup instructions</summary>

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

</details>

## 🎮 Usage

### 🔧 First Run Configuration
1. 🚀 **Launch SuperSexySteam**
2. ⚙️ **Configure paths** in the settings:
   - 📁 Steam installation directory
   - 🔧 GreenLuma path (pre-configured if using included version)

### 📦 Installing Games
1. 🔍 **Search for games** using the built-in Steam search
2. 📋 **Get your Manifest and Lua files** *(You need to own the game to get these files)*
3. 🖱️ **Drag and Drop them** to begin the automated process:
   - 📊 Parses depot information from .lua files
   - 📁 Copies manifest files to Steam depot cache
   - 🔑 Updates Steam config.vdf with decryption keys
   - 📄 Generates ACF files for Steam recognition
   - 🔧 Configures GreenLuma AppList
   - 💾 Updates database tracking

### 🎯 Managing Installed Games
- 👀 **View installed games** in the main interface
- 🗑️ **Uninstall games** with comprehensive cleanup

### 🧹 System Maintenance
- 🔄 **Clear all data**: Complete system reset functionality
- 🎯 **Selective uninstall**: Remove specific games with full cleanup


## 🔧 Build & Distribution

### 🔨 Automated Build Process
SuperSexySteam includes a comprehensive PowerShell build script located in the `buildtools` directory:

```powershell
# Run the automated build script from project root
.\buildtools\build.ps1
```

**The build script automatically:**
- ✨ Creates a clean virtual environment
- 📦 Installs all dependencies from requirements.txt
- 🏗️ Builds the executable using PyInstaller
- 📁 Creates a release.zip in the buildtools folder
- 🎁 Packages everything into a distribution-ready SuperSexySteam.zip
- 🧹 Cleans up temporary files

### 📦 Distribution Package Structure
The build process creates `buildtools\SuperSexySteam.zip` containing:
| File | Description |
|------|-------------|
| `release.zip` | The main application files |
| `install.ps1` | PowerShell installation script |
| `install.bat` | Batch wrapper for installation with admin privileges |

### 🚀 Installation from Build
After building, users can install by:
1. 📂 Extracting the `SuperSexySteam.zip` file
2. 🚀 Running `install.bat` (which launches `install.ps1` with admin privileges)

The installer will:
- 🛡️ Add Windows Defender exclusions
- 📁 Extract files to `%AppData%\Roaming\SuperSexySteam`
- 🖥️ Create desktop shortcuts
- ⚙️ Set up the application for immediate use

## 🐛 Troubleshooting

### ⚠️ Common Issues

<details>
<summary><strong>🔍 Steam Not Detected</strong></summary>

- ✅ Verify Steam installation path in configuration
- ✅ Ensure Steam.exe is in the specified directory
- ✅ Check for Steam process conflicts

</details>

<details>
<summary><strong>🛡️ Antivirus Issues</strong></summary>

- ✅ Add an exclusion for your antivirus to `%AppData%\Roaming\SuperSexySteam`

</details>

## 🤝 Contributing

> **Free to contribute for any features you want to add!**

We welcome contributions from the community. Feel free to:
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📚 Improve documentation

---

## ⚠️ Disclaimer

> **Educational and Research Purpose Only**

This software is provided for educational and research purposes. Users are responsible for:

| Responsibility | Description |
|----------------|-------------|
| **Compliance** | Steam Terms of Service |
| **Respect** | Software licensing agreements |
| **Legal Use** | In their jurisdiction |
| **Understanding** | Of the tools they use |

*The developers are not responsible for any misuse of this software.*

---

## 📞 Support

| Resource | Link |
|----------|------|
| 🐛 **Issues** | [GitHub Issues](https://github.com/PSSGAMER/SuperSexySteam/issues) |
| 💬 **Discussions** | [GitHub Discussions](https://github.com/PSSGAMER/SuperSexySteam/discussions) |
| 📚 **Documentation** | [Project Wiki](https://github.com/PSSGAMER/SuperSexySteam/wiki) *(WIP)* |

---

<div align="center">

**Made with ❤️ for the gaming community**

</div>
