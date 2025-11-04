# Green-Ampt Notebook Quick Start Guide

This guide will help you get started with the interactive Green-Ampt parameter estimation notebook.

## Prerequisites

1. **Environment Setup**: Make sure you have installed all required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **PySDA Module**: Ensure the PySDA module is available in `external/pysda/`

## Launching the Notebook

1. Start Jupyter:
   ```bash
   jupyter notebook
   ```

2. Open `green_ampt_notebook.ipynb`

3. Run the cells in order from top to bottom

## Workflow Overview

### Step 1: Import Libraries
Run the first code cell to import all necessary libraries. You should see:
```
✓ Libraries imported successfully
```

### Step 2: Define Your AOI

You have two options:

#### Option A: Draw AOI on Map
1. An interactive map will appear
2. Use the polygon or rectangle drawing tools on the left side of the map
3. Draw your area of interest
4. You'll see a confirmation message when the AOI is created

#### Option B: Upload Shapefile
1. Click "Choose Files" to select your shapefile components (.shp, .shx, .dbf, .prj)
   - Or upload a zipped shapefile
   - Or upload a GeoPackage (.gpkg) or GeoJSON (.geojson)
2. Click "Load Shapefile"
3. The AOI will be displayed on the map

### Step 3: Configure Pipeline Settings

Adjust the settings as needed:

- **Data Source**: 
  - `pysda`: Fetch SSURGO data from NRCS online (requires internet)
  - `local`: Use previously downloaded SSURGO files (requires file paths)

- **Output Directory**: Where results will be saved (default: `./outputs`)

- **Output CRS**: Coordinate system for output rasters (default: EPSG:32617 - UTM Zone 17N)
  - Change this to match your study area
  - Common options:
    - EPSG:32617 - UTM Zone 17N (Eastern US)
    - EPSG:32618 - UTM Zone 18N (Eastern US)
    - EPSG:32613 - UTM Zone 13N (Western US)
    - EPSG:5070 - NAD83 / Conus Albers

- **Resolution**: Pixel size in meters (default: 30m)

- **Depth Limit**: Soil depth to consider in cm (default: 30cm)

- **Export Raw SSURGO Data**: Check to save raw SSURGO files

### Step 4: Run the Pipeline

1. Click the "Generate Green-Ampt Parameters" button
2. Watch the progress output
3. Wait for completion (may take several minutes depending on AOI size and data source)

### Step 5: View Results

After successful completion, you'll find:

- **Rasters**: `outputs/rasters/`
  - `ksat_green_ampt.tif` - Saturated hydraulic conductivity (cm/hr)
  - `theta_s_green_ampt.tif` - Saturated water content (fraction)
  - `psi_green_ampt.tif` - Wetting front suction head (cm)
  - `theta_i_green_ampt.tif` - Initial water content (fraction)

- **Vectors**: `outputs/vectors/`
  - `green_ampt_params.shp` - Shapefile with all parameters

- **Raw Data** (if enabled): `outputs/raw_data/`
  - Original SSURGO spatial and tabular data

## Visualization (Optional)

Uncomment and run the visualization cell to preview the generated rasters:

```python
visualize_results(output_dir_widget.value)
```

This will create a 2x2 grid showing all four Green-Ampt parameters.

## Common Issues

### "No AOI defined"
- Make sure you've either drawn an area on the map or uploaded a shapefile
- Check that you see a confirmation message before running the pipeline

### "All local SSURGO file paths are required"
- If using `data_source='local'`, you must provide all four file paths:
  - mupolygon.shp
  - mapunit.txt
  - component.txt
  - chorizon.txt

### "PySDA returned no spatial records"
- Your AOI may be outside the SSURGO coverage area
- Try a different location or use local SSURGO files
- Check your internet connection if using PySDA

### Empty or all-NaN rasters
- The AOI may not overlap with valid SSURGO data
- Try expanding your AOI
- Check the log messages for warnings about missing data

## Tips

1. **Start Small**: Test with a small AOI first to ensure everything works
2. **Check CRS**: Make sure your output CRS matches your study area
3. **Save Often**: The notebook auto-saves, but you can manually save with Ctrl+S
4. **Rerun Cells**: You can modify settings and rerun the pipeline without restarting
5. **View Logs**: The output messages provide valuable information about the process

## Next Steps

After generating the parameters, you can:

1. Load the GeoTIFFs in QGIS, ArcGIS, or other GIS software
2. Use the parameters in hydrologic models (HEC-HMS, SWMM, etc.)
3. Perform further analysis or post-processing
4. Generate multiple parameter sets with different configurations

## Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review the `docs/user_guide.md` for step-by-step instructions
- Submit an issue on GitHub
