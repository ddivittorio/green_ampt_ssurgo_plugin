# Configuration File Guide

The Green-Ampt Estimation Toolkit now supports configuration files in YAML or JSON format, making it easier to manage complex workflows and maintain reproducible analyses.

## Quick Start

### Using a Configuration File

Create a simple YAML configuration file:

```yaml
# config.yaml
aoi: "my_watershed.shp"
output_dir: "outputs"
```

Run the pipeline:

```bash
python green_ampt.py --config config.yaml
```

### CLI Arguments Override Configuration File Values

You can use a config file and override specific values with CLI arguments:

```bash
python green_ampt.py --config config.yaml --output-resolution 5.0
```

## Supported File Formats

The toolkit now supports various AOI file formats through GeoPandas:

### Single-Layer Formats
- **Shapefile** (`.shp`) - Traditional ESRI format
- **GeoJSON** (`.geojson`, `.json`) - Web-friendly format
- **KML/KMZ** (`.kml`, `.kmz`) - Google Earth format

### Multi-Layer Formats
- **GeoPackage** (`.gpkg`) - Modern SQLite-based format
- **File Geodatabase** (`.gdb`) - ESRI geodatabase

## Working with Multi-Layer Formats

### Method 1: Colon Syntax in Path

Append the layer name to the file path with a colon:

```yaml
aoi: "data/watersheds.gpkg:watershed_1"
```

```bash
python green_ampt.py --aoi "data/watersheds.gpkg:watershed_1" --output-dir outputs
```

### Method 2: Separate Layer Parameter

Use the `aoi_layer` parameter:

```yaml
aoi: "data/watersheds.gpkg"
aoi_layer: "watershed_1"
```

```bash
python green_ampt.py --aoi data/watersheds.gpkg --aoi-layer watershed_1 --output-dir outputs
```

## Configuration File Reference

### Minimal Configuration

```yaml
aoi: "study_area.shp"
output_dir: "outputs"
```

All other parameters use sensible defaults.

### Complete Configuration

```yaml
# AOI specification
aoi: "path/to/aoi.gpkg:layer_name"
# Optional: explicit layer specification (overrides colon syntax)
aoi_layer: null

# Output settings
output_dir: "outputs"
output_resolution: 10.0  # meters (for projected CRS)
output_crs: null  # Inherits from AOI if null
output_prefix: ""  # Optional filename prefix

# Data source
data_source: "pysda"  # "pysda" or "local"
pysda_timeout: 300  # seconds

# Local SSURGO (required if data_source is "local")
local_ssurgo:
  mupolygon: "path/to/mupolygon.shp"
  mapunit: "path/to/mapunit.txt"
  component: "path/to/component.txt"
  chorizon: "path/to/chorizon.txt"

# Processing parameters
depth_limit_cm: 10.0  # Soil depth for aggregation

# Data export
export_raw_data: true
raw_data_dir: null  # Defaults to output_dir/raw_data

# Parameter estimation method (only one should be true)
use_lookup_table: true  # Texture lookup (Rawls/SWMM)
use_hsg_lookup: false  # HSG-based Ksat lookup
# If both false, pedotransfer functions are used
```

## Examples

### Example 1: GeoPackage with Multiple Watersheds

```yaml
# config_watershed_1.yaml
aoi: "watersheds.gpkg:ws_001"
output_dir: "outputs/ws_001"
output_resolution: 5.0
output_prefix: "ws1_"
```

```yaml
# config_watershed_2.yaml
aoi: "watersheds.gpkg:ws_002"
output_dir: "outputs/ws_002"
output_resolution: 5.0
output_prefix: "ws2_"
```

### Example 2: High-Resolution Analysis

```yaml
aoi: "site.kml"
output_dir: "outputs/high_res"
output_resolution: 1.0  # 1-meter resolution
output_crs: "EPSG:26910"  # UTM Zone 10N
depth_limit_cm: 5.0  # Shallow surface layer
```

### Example 3: Local SSURGO Data

```yaml
aoi: "county_boundary.shp"
output_dir: "outputs/county"
data_source: "local"
local_ssurgo:
  mupolygon: "ssurgo/spatial/soilmu_a.shp"
  mapunit: "ssurgo/tabular/mapunit.txt"
  component: "ssurgo/tabular/comp.txt"
  chorizon: "ssurgo/tabular/chorizon.txt"
```

### Example 4: HSG-Based Parameters

```yaml
aoi: "study_area.geojson"
output_dir: "outputs/hsg"
use_lookup_table: false
use_hsg_lookup: true
```

## JSON Configuration

The same configurations work in JSON format:

```json
{
  "aoi": "study_area.shp",
  "output_dir": "outputs",
  "output_resolution": 10.0,
  "data_source": "pysda",
  "depth_limit_cm": 10.0,
  "use_lookup_table": true,
  "use_hsg_lookup": false
}
```

## Backward Compatibility

All existing CLI workflows continue to work without modification:

```bash
# Traditional CLI usage still works
python green_ampt.py --aoi study_area.shp --output-dir outputs --data-source pysda
```

## Tips

1. **Use YAML for human-readable configs** - YAML supports comments and is easier to edit
2. **Use JSON for programmatic generation** - JSON is easier to generate from scripts
3. **Version control your configs** - Track configuration files in git for reproducibility
4. **One config per analysis** - Create separate config files for different study areas or parameters
5. **Test with small AOIs first** - Verify your configuration with a small area before processing large regions

## Troubleshooting

### Layer Not Found
```
Error: Layer 'my_layer' not found in 'data.gpkg'
```
**Solution**: Check available layers:
```bash
python -c "import geopandas as gpd; print(gpd.list_layers('data.gpkg'))"
```

### Missing Required Fields
```
Error: Configuration must specify 'aoi_path' or 'aoi'
```
**Solution**: Ensure your config file includes the `aoi` field

### YAML Not Available
```
Error: YAML configuration requires PyYAML
```
**Solution**: Install PyYAML:
```bash
pip install pyyaml
```
