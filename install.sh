#!/bin/bash

USER_HOME=$HOME
CONFIG_DIR="${USER_HOME}/printer_data/config"
FLUIDD_DIR="${USER_HOME}/fluidd"
MAINSAIL_DIR="${USER_HOME}/mainsail"
PLUGIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing Camera Settings Plugin..."

# 1. Install Dependencies
if ! command -v v4l2-ctl &> /dev/null; then
    echo "Installing v4l2-utils..."
    sudo apt-get update && sudo apt-get install -y v4l2-utils
else
    echo "v4l2-utils is already installed."
fi

# 2. Set Permissions
echo "Setting executable permissions..."
chmod +x "${PLUGIN_DIR}/scripts/camera_control.py"

# 3. Symlink Config
echo "Linking configuration..."
ln -sf "${PLUGIN_DIR}/conf/camera_ctrl.cfg" "${CONFIG_DIR}/camera_ctrl.cfg"

# 4. Symlink HTML
echo "Linking web interface..."
# Check for Fluidd
if [ -d "$FLUIDD_DIR" ]; then
    ln -sf "${PLUGIN_DIR}/web/camera_settings.html" "${FLUIDD_DIR}/camera_settings.html"
    echo "  [OK] Installed to Fluidd"
else
    echo "  [SKIP] Fluidd directory not found"
fi

# Check for Mainsail
if [ -d "$MAINSAIL_DIR" ]; then
    ln -sf "${PLUGIN_DIR}/web/camera_settings.html" "${MAINSAIL_DIR}/camera_settings.html"
    echo "  [OK] Installed to Mainsail"
else
    echo "  [SKIP] Mainsail directory not found"
fi
if [ ! -d "$FLUIDD_DIR" ] && [ ! -d "$MAINSAIL_DIR" ]; then
    echo "Warning: Neither Fluidd nor Mainsail directories found. You may need to manually link the HTML file."
fi

# 5. Instructions
echo "-------------------------------------------------------"
echo "Installation Complete!"
echo "1. Ensure '[include camera_ctrl.cfg]' is in your printer.cfg"
echo "2. Restart Klipper"
echo "3. Access settings at http://<your_printer_ip>/camera_settings.html"
echo "-------------------------------------------------------"
