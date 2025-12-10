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

# 2. Remove HTML Symlink
if [ -L "${FLUIDD_DIR}/camera_settings.html" ]; then
    echo "Removing web interface symlink..."
    rm "${FLUIDD_DIR}/camera_settings.html"
else
    echo "Web interface symlink not found."
fi

echo "-------------------------------------------------------"
echo "Uninstall Complete!"
echo "Please manually remove '[include camera_ctrl.cfg]' from your printer.cfg"
echo "and restart Klipper."
echo "-------------------------------------------------------"
