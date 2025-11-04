#!/bin/bash
# Installation script for Green-Ampt Parameter Generator QGIS Plugin

set -e

echo "==================================="
echo "Green-Ampt Plugin Installation"
echo "==================================="
echo

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    QGIS_PLUGINS_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    QGIS_PLUGINS_DIR="$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins"
else
    echo "Error: Unsupported operating system"
    echo "For Windows, please use install_plugin.bat"
    exit 1
fi

echo "Target directory: $QGIS_PLUGINS_DIR"
echo

# Check if directory exists
if [ ! -d "$QGIS_PLUGINS_DIR" ]; then
    echo "Creating plugins directory..."
    mkdir -p "$QGIS_PLUGINS_DIR"
fi

# Initialize submodules (commented out - using vendored dependencies)
# echo "Initializing git submodules..."
# git submodule update --init --recursive

# Copy plugin
echo "Installing plugin..."
PLUGIN_NAME="green_ampt_plugin"
TARGET_DIR="$QGIS_PLUGINS_DIR/$PLUGIN_NAME"

if [ -d "$TARGET_DIR" ]; then
    echo "Warning: Plugin already exists at $TARGET_DIR"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r || {
        echo
        echo "Error: Failed to read input"
        exit 1
    }
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    rm -rf "$TARGET_DIR"
fi

cp -r "$PLUGIN_NAME" "$QGIS_PLUGINS_DIR/"

# Create symlink to green_ampt_tool for imports
echo "Creating symlink to green_ampt_tool..."
# Get the absolute path to the current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Remove existing symlink if it exists
rm -f "$TARGET_DIR/green_ampt_tool"
ln -sf "$SCRIPT_DIR/green-ampt-estimation/green_ampt_tool" "$TARGET_DIR/green_ampt_tool"

echo
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo
echo "Next steps:"
echo "1. Start or restart QGIS"
echo "2. Go to Plugins → Manage and Install Plugins"
echo "3. Enable 'Green-Ampt Parameter Generator'"
echo "4. Find the algorithm in Processing Toolbox"
echo
