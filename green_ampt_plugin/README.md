# Green-Ampt Parameter Generator - QGIS Plugin

## Plugin Structure

This plugin follows the QGIS Processing framework architecture, similar to the Curve Number Generator plugin.

### Directory Structure

```
green_ampt_plugin/
├── __init__.py                    # Plugin entry point (classFactory)
├── green_ampt_plugin.py           # Main plugin class
├── metadata.txt                   # Plugin metadata (version, description, etc.)
├── icon.png                       # Plugin icon (64x64)
├── icon.svg                       # Source SVG icon
└── processing/                    # Processing framework components
    ├── __init__.py
    ├── green_ampt_provider.py     # Processing provider
    ├── green_ampt_algorithm.py    # Base algorithm class
    └── algorithms/                # Algorithm implementations
        ├── __init__.py
        └── green_ampt_ssurgo.py   # Main SSURGO algorithm
```

### How It Works

1. **Plugin Initialization** (`__init__.py`):
   - Exports `classFactory()` function that QGIS calls to create plugin instance
   - Returns `GreenAmptPlugin` object

2. **Plugin Class** (`green_ampt_plugin.py`):
   - Implements `initGui()` to register the Processing provider
   - Implements `unload()` to clean up when plugin is disabled

3. **Processing Provider** (`green_ampt_provider.py`):
   - Registers with QGIS Processing framework
   - Auto-discovers and loads algorithms from `algorithms/` module
   - Provides plugin identity (name, icon, description)

4. **Base Algorithm** (`green_ampt_algorithm.py`):
   - Common base class for all Green-Ampt algorithms
   - Provides shared functionality (icon, translations, etc.)

5. **Algorithm Implementation** (`green_ampt_ssurgo.py`):
   - Wraps the `green_ampt_tool` package functionality
   - Defines input parameters (AOI, output dir, method, etc.)
   - Executes pipeline and reports progress to QGIS
   - Converts QGIS vector layers to files for processing

### Integration with green_ampt_tool

The plugin uses `sys.path` manipulation to import the `green_ampt_tool` package from the `green-ampt-estimation/` directory:

```python
green_ampt_estimation_path = os.path.join(
    os.path.dirname(os.path.dirname(plugin_folder)), "green-ampt-estimation"
)
sys.path.insert(0, green_ampt_estimation_path)

from green_ampt_tool.config import PipelineConfig
from green_ampt_tool.workflow import run_pipeline
```

This allows the plugin to use the core functionality without duplicating code, making updates easy.

### Key Design Decisions

1. **No Code Duplication**: The plugin wraps existing `green_ampt_tool` functionality rather than reimplementing it
2. **Standard Processing Framework**: Uses QGIS Processing for consistency with other plugins
3. **Flexible Parameter Methods**: All three estimation methods exposed as algorithm options
4. **Temporary File Handling**: Exports QGIS layers to temporary files for CLI tool compatibility
5. **Progress Reporting**: Uses QgsProcessingFeedback for user feedback during long operations

### Adding New Features

To add new algorithms:

1. Create new class in `processing/algorithms/` inheriting from `GreenAmptAlgorithm`
2. Implement required methods:
   - `initAlgorithm()`: Define parameters
   - `processAlgorithm()`: Execute algorithm
   - `name()`, `displayName()`: Identity
   - `shortHelpString()`: Documentation
3. Add to `algorithms/__init__.py` exports
4. Provider auto-discovers and registers it

### Testing the Plugin

For manual testing in QGIS:

1. Copy plugin to QGIS plugins directory
2. Enable in Plugin Manager
3. Open Processing Toolbox
4. Look for "Green-Ampt Parameter Generator" provider
5. Run algorithm with test data

### Dependencies

The plugin requires:
- QGIS 3.18+
- Python 3.7+
- All dependencies from `green-ampt-estimation/requirements.txt`

### Maintenance

To update core functionality:

1. Pull latest changes in `green-ampt-estimation/`:
   ```bash
   cd ../green-ampt-estimation
   git pull origin main
   ```

2. Test with QGIS (no reinstall needed)

3. Update plugin metadata version if needed

To release a new plugin version:

1. Update version in `metadata.txt`
2. Update changelog in `metadata.txt`
3. Test thoroughly
4. Create release/tag

## Development Tips

### QGIS Plugin Development

- **Plugin Reloader**: Install the "Plugin Reloader" plugin for quick testing iterations
- **Python Console**: Use QGIS Python console for debugging: `View` → `Panels` → `Python Console`
- **Processing Log**: Check `Processing` → `History` for detailed algorithm logs

### Common Issues

1. **Import Errors**: Ensure `green-ampt-estimation` path is correct and submodule initialized
2. **Parameter Validation**: QGIS validates parameters before calling `processAlgorithm()`
3. **File Paths**: Always use absolute paths, handle temp files properly
4. **CRS Handling**: Be careful with CRS conversions and reprojections

### Useful QGIS API Classes

- `QgsProcessingAlgorithm`: Base class for algorithms
- `QgsProcessingParameter*`: Various parameter types (vector, raster, number, etc.)
- `QgsVectorFileWriter`: Export vector layers to files
- `QgsProcessingFeedback`: Progress reporting and logging
- `QgsVectorLayer`: Vector layer representation

## Resources

- **QGIS Plugin Development**: https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/
- **Processing Framework**: https://docs.qgis.org/latest/en/docs/user_manual/processing/console.html
- **PyQGIS API**: https://qgis.org/pyqgis/latest/
- **Example Plugin**: https://github.com/ar-siddiqui/curve_number_generator
