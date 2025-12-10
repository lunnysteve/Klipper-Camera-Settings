#!/bin/bash

USER_HOME=$HOME
CONFIG_DIR="${USER_HOME}/printer_data/config"
FLUIDD_DIR="${USER_HOME}/fluidd"

echo "Uninstalling Camera Settings Plugin..."

# 1. Remove Config Symlink
if [ -L "${CONFIG_DIR}/camera_ctrl.cfg" ]; then
    echo "Removing config symlink..."
    rm "${CONFIG_DIR}/camera_ctrl.cfg"
else
    echo "Config symlink not found."
fi

# 2. Remove HTML Symlinks
echo "Removing web interface symlink..."
REMOVED=false

if [ -L "${FLUIDD_DIR}/camera_settings.html" ]; then
    rm "${FLUIDD_DIR}/camera_settings.html"
    echo "  - Removed from Fluidd"
    REMOVED=true
fi

MAINSAIL_DIR="${USER_HOME}/mainsail"
if [ -L "${MAINSAIL_DIR}/camera_settings.html" ]; then
    rm "${MAINSAIL_DIR}/camera_settings.html"
    echo "  - Removed from Mainsail"
    REMOVED=true
fi

if [ "$REMOVED" = false ]; then
    echo "Web interface symlinks not found."
fi

echo "-------------------------------------------------------"
echo "Uninstall Complete!"
echo "Please manually remove '[include camera_ctrl.cfg]' from your printer.cfg"
echo "and restart Klipper."
echo "-------------------------------------------------------"
