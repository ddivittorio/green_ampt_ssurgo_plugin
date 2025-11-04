#!/bin/bash
# Script to create a deployable QGIS plugin zip package

set -e

echo "================================================"
echo "Creating QGIS Plugin Deployment Package"
echo "================================================"
echo

# Get version from metadata.txt
VERSION=$(grep "^version=" green_ampt_plugin/metadata.txt | cut -d'=' -f2)
echo "Plugin version: $VERSION"

# Define output filename
OUTPUT_FILE="green_ampt_plugin_v${VERSION}.zip"
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/green_ampt_plugin"

echo "Temporary directory: $TEMP_DIR"
echo "Output file: $OUTPUT_FILE"
echo

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Copy plugin files
echo "Copying plugin files..."
cp -r green_ampt_plugin/* "$PACKAGE_DIR/"

# Copy green-ampt-estimation (core functionality)
echo "Copying green-ampt-estimation core tool..."
mkdir -p "$PACKAGE_DIR/green_ampt_estimation"
cp -r green-ampt-estimation/green_ampt_tool "$PACKAGE_DIR/green_ampt_estimation/"
cp green-ampt-estimation/requirements.txt "$PACKAGE_DIR/green_ampt_estimation/"
cp green-ampt-estimation/LICENSE "$PACKAGE_DIR/green_ampt_estimation/LICENSE"
cp green-ampt-estimation/README.md "$PACKAGE_DIR/green_ampt_estimation/README.md"

# Copy external dependencies (PySDA)
if [ -d "green-ampt-estimation/external/pysda" ]; then
    echo "Copying PySDA..."
    mkdir -p "$PACKAGE_DIR/green_ampt_estimation/external"
    cp -r green-ampt-estimation/external/pysda "$PACKAGE_DIR/green_ampt_estimation/external/"
fi

# Remove unnecessary files
echo "Cleaning up unnecessary files..."
find "$PACKAGE_DIR" -name "*.pyc" -delete
find "$PACKAGE_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -name ".coverage" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -name "*.log" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -name ".git*" -delete 2>/dev/null || true
rm -rf "$PACKAGE_DIR/green_ampt_estimation/green_ampt_tool/tests" 2>/dev/null || true
rm -rf "$PACKAGE_DIR/green_ampt_estimation/docs" 2>/dev/null || true
rm -rf "$PACKAGE_DIR/green_ampt_estimation/examples" 2>/dev/null || true
rm -rf "$PACKAGE_DIR/green_ampt_estimation/test_aoi" 2>/dev/null || true
rm -rf "$PACKAGE_DIR/green_ampt_estimation/scripts" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/green_ampt.py" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/green_ampt_notebook.ipynb" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/pytest.ini" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/Dockerfile" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/docker-compose.yml" 2>/dev/null || true
rm -f "$PACKAGE_DIR/green_ampt_estimation/.dockerignore" 2>/dev/null || true
rm -f "$PACKAGE_DIR/icon.svg" 2>/dev/null || true

# Create the zip file
echo "Creating zip archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_FILE" green_ampt_plugin -q

# Move to current directory
mv "$OUTPUT_FILE" "$OLDPWD/"
cd "$OLDPWD"

# Clean up
rm -rf "$TEMP_DIR"

# Show package info
echo
echo "================================================"
echo "Package created successfully!"
echo "================================================"
echo "File: $OUTPUT_FILE"
echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo
echo "Package contents:"
unzip -l "$OUTPUT_FILE" | head -30
echo "..."
echo
echo "Total files: $(unzip -l "$OUTPUT_FILE" | grep -c "green_ampt_plugin/")"
echo
echo "To install:"
echo "  1. Open QGIS"
echo "  2. Go to Plugins → Manage and Install Plugins"
echo "  3. Click 'Install from ZIP'"
echo "  4. Select $OUTPUT_FILE"
echo "  5. Enable 'Green-Ampt Parameter Generator'"
echo
