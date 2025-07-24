# SuperSexySteam Installer Configuration
# Edit this file to customize installation settings

# Installation directory (default: User AppData Roaming)
$INSTALL_LOCATION = "$env:APPDATA\SuperSexySteam"

# Alternative installation locations (uncomment to use):
# $INSTALL_LOCATION = "C:\Program Files (x86)\SuperSexySteam"
# $INSTALL_LOCATION = "C:\SuperSexySteam"
# $INSTALL_LOCATION = "D:\Games\SuperSexySteam" 
# $INSTALL_LOCATION = "$env:USERPROFILE\SuperSexySteam"

# You can also specify a custom path:
# $INSTALL_LOCATION = "YOUR_CUSTOM_PATH_HERE"

# Run the installer with the configured path
& "$PSScriptRoot\install.ps1" -InstallDir $INSTALL_LOCATION
