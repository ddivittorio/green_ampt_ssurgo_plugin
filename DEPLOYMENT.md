# QGIS Plugin Deployment

This directory contains scripts to create a deployable QGIS plugin package.

## Creating the Plugin Package

### Linux/Mac

```bash
./package_plugin.sh
```

### Windows

```cmd
package_plugin.bat
```

## What Gets Packaged

The packaging script creates a standard QGIS plugin zip file containing:

1. **Plugin files** (`green_ampt_plugin/`)
   - All Python modules and UI files
   - Plugin metadata and icon
   - Documentation

2. **Core functionality** (`green_ampt_estimation/`)
   - The `green_ampt_tool` package (parameter estimation logic)
   - Required configuration files
   - Dependencies (requirements.txt)
   - License and README

3. **Cleanup**
   - Removes test files, documentation, examples
   - Removes Python cache files (`__pycache__`, `.pyc`)
   - Removes development-only files

## Output

- **Filename**: `green_ampt_plugin_v{VERSION}.zip`
- **Size**: ~50-60 KB
- **Structure**: Standard QGIS plugin layout

## Installation

Users can install the packaged plugin in QGIS:

1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Click **Install from ZIP**
4. Select the `green_ampt_plugin_v{VERSION}.zip` file
5. Click **Install Plugin**
6. Enable **Green-Ampt Parameter Generator** in the installed plugins list

## Distribution

The generated zip file can be:

- Shared directly with users
- Uploaded to the QGIS Plugin Repository
- Hosted on GitHub releases
- Distributed via file sharing

## Technical Notes

### Path Resolution

The plugin uses smart path resolution to find the core `green_ampt_tool`:

1. **Deployed package**: Looks in `green_ampt_plugin/green_ampt_estimation/`
2. **Development mode**: Falls back to sibling directory `../green-ampt-estimation/`

This allows the same code to work in both development and deployed environments.

### Dependencies

The plugin requires Python packages that are typically included with QGIS:
- `geopandas`
- `rasterio`
- `pandas`
- `numpy`
- `requests`
- `pyyaml`

If any are missing, users should install them to their QGIS Python environment.

### Version Management

The version is read from `green_ampt_plugin/metadata.txt`:

```ini
version=1.0
```

Update this file to change the package version.

## Verification

After packaging, you can inspect the contents:

```bash
# List contents
unzip -l green_ampt_plugin_v1.0.0.zip

# Extract to test
unzip green_ampt_plugin_v1.0.0.zip -d test_extract/
```

## Troubleshooting

### Package too large

If the package exceeds 100 KB, check for:
- Leftover test data
- Documentation files
- Example datasets
- Log files

The packaging script should remove these automatically.

### Missing files in package

Ensure all necessary files are in the correct locations:
- Plugin files in `green_ampt_plugin/`
- Core tool in `green-ampt-estimation/green_ampt_tool/`

### Import errors after installation

Verify the path resolution logic in `green_ampt_ssurgo.py` is working correctly. The plugin should find `green_ampt_tool` in the embedded location.
