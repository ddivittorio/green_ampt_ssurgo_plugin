# Quick Start Guide

Get up and running with the Green-Ampt Parameter Generator plugin in just a few minutes!

## ⚡ Installation (5 minutes)

### Step 1: Clone the Repository

```bash
git clone --recursive https://github.com/ddivittorio/qgis_green_ampt_plugin_jules.git
cd qgis_green_ampt_plugin_jules
```

**Note:** The `--recursive` flag is important! It includes the green-ampt-estimation submodule.

### Step 2: Verify Everything is Ready

```bash
python3 verify_plugin.py
```

You should see ✓ marks for Plugin Structure, Metadata, and Green-Ampt Estimation. Don't worry about Dependencies - QGIS includes them.

### Step 3: Install the Plugin

**Linux/Mac:**
```bash
./install_plugin.sh
```

**Windows:**
```cmd
install_plugin.bat
```

### Step 4: Enable in QGIS

1. Open QGIS
2. Go to `Plugins` → `Manage and Install Plugins`
3. Click the `Installed` tab
4. Check the box next to **"Green-Ampt Parameter Generator"**
5. Click `Close`

✅ Installation complete!

## 🎯 First Run (10 minutes)

### Open the Algorithm

1. Open the **Processing Toolbox**: `Processing` → `Toolbox` (or press `Ctrl+Alt+T`)
2. In the search box, type "green"
3. Expand **Green-Ampt Parameter Generator**
4. Double-click **"Generate Green-Ampt Parameters from SSURGO"**

### Prepare Your Data

You need a polygon layer defining your Area of Interest (AOI). You can:
- Use an existing shapefile
- Create a new polygon layer (`Layer` → `Create Layer` → `New Shapefile Layer`)
- Use the test AOI: `green-ampt-estimation/test_aoi/test_aoi.shp`

### Run the Algorithm

**Example with Test Data:**

1. **Area of Interest**: Browse to `green-ampt-estimation/test_aoi/test_aoi.shp`
2. **Output Directory**: Choose a folder (e.g., `C:\Temp\green_ampt_output`)
3. **Data Source**: Select "PySDA (live SSURGO queries)" *(requires internet)*
4. **Parameter Method**: Leave as "Texture Lookup (Rawls/SWMM)"
5. **Output Resolution**: Keep default 10.0
6. **Other options**: Leave as defaults
7. Click **Run**

### Processing Time

- Small AOI (< 1 km²): 2-5 minutes
- Medium AOI (1-10 km²): 5-15 minutes
- Large AOI (> 10 km²): 15+ minutes

*Processing time varies with internet speed and SSURGO server load*

### View Results

After processing completes, you'll find:

```
your_output_dir/
├── rasters/          ← Six parameter rasters (auto-loaded to map)
├── vectors/          ← Vector parameters
└── raw_data/         ← Raw SSURGO data (for QA)
```

The rasters are automatically added to your QGIS map canvas!

## 📊 Understanding Your Outputs

### Generated Rasters (US customary units)

| File | Parameter | Units | Description |
|------|-----------|-------|-------------|
| `Ks_inhr.tif` | Hydraulic Conductivity | in/hr | How fast water infiltrates |
| `psi_in.tif` | Suction Head | inches | Soil water retention |
| `theta_s.tif` | Porosity | fraction | Maximum water content |
| `theta_i.tif` | Initial Moisture | fraction | Starting soil wetness |
| `theta_fc.tif` | Field Capacity | fraction | Water held after drainage |
| `theta_wp.tif` | Wilting Point | fraction | Minimum plant-available water |

### Typical Values

- **High infiltration soils** (sandy): Ks > 2 in/hr, low psi
- **Moderate infiltration** (loam): Ks 0.5-2 in/hr, medium psi
- **Low infiltration** (clay): Ks < 0.5 in/hr, high psi

## 🎨 Visualization Tips

### Apply a Color Ramp

1. Right-click a raster layer → `Properties`
2. Go to `Symbology` tab
3. Select `Singleband pseudocolor`
4. Choose a color ramp (e.g., "RdYlGn" for Ks)
5. Click `Classify` then `OK`

### Suggested Color Schemes

- **Hydraulic Conductivity (Ks)**: Green (high) → Red (low)
- **Porosity (theta_s)**: Blue gradient
- **Suction Head (psi)**: Yellow (low) → Red (high)

## 🔧 Troubleshooting

### "Connection timeout" or "PySDA error"

**Solution:** Check internet connection or increase timeout:
- Set `PySDA Timeout` to 600 seconds
- Or use local SSURGO files instead

### "Empty rasters" or "All NoData"

**Possible causes:**
1. AOI outside SSURGO coverage (mainly CONUS only)
2. Invalid CRS transformation
3. AOI too small

**Solutions:**
- Verify AOI is within contiguous United States
- Ensure AOI CRS is correct (check in Layer Properties)
- Try a larger test area

### "Failed to import green_ampt_tool"

**Solution:**
```bash
cd qgis_green_ampt_plugin_jules
git submodule update --init --recursive
```

## 📚 Next Steps

### Try Different Methods

Experiment with the three parameter estimation methods:

1. **Texture Lookup** - Fast, based on soil texture class
2. **HSG Lookup** - Uses NRCS hydrologic soil groups
3. **Pedotransfer** - Most detailed, calculated from soil properties

### Use Your Own Data

Replace the test AOI with your study area:
- Create a polygon layer in QGIS
- Draw your area of interest
- Save as shapefile
- Use it as the AOI input

### Batch Processing

Process multiple AOIs using the Processing Batch interface:
1. Right-click the algorithm → `Execute as Batch Process`
2. Add multiple rows with different AOIs
3. Click `Run`

### Integration with Models

Use the algorithm in Processing models for automated workflows:
1. `Processing` → `Graphical Modeler`
2. Add "Generate Green-Ampt Parameters" as a step
3. Connect to other processing algorithms

## 💡 Tips for Best Results

1. **Start Small**: Test with a small AOI before processing large areas
2. **Check Coverage**: Ensure your AOI overlaps SSURGO data (mainly CONUS)
3. **Choose Appropriate Resolution**: 10m is good for catchment scale; use 30m+ for large regions
4. **Save Raw Data**: Keep `Export Raw SSURGO Data` checked for reproducibility
5. **Document Settings**: Take note of which parameter method works best for your application

## 🆘 Getting Help

- **Documentation**: See [README.md](README.md) for detailed documentation
- **Issues**: Report bugs at [GitHub Issues](https://github.com/ddivittorio/qgis_green_ampt_plugin_jules/issues)
- **Questions**: Open a [Discussion](https://github.com/ddivittorio/qgis_green_ampt_plugin_jules/discussions)
- **Email**: ddivittorio@gmail.com

Happy infiltration modeling! 💧🌍
