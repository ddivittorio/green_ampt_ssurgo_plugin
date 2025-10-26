# Green-Ampt Parameter Generator - QGIS Plugin

A QGIS plugin that generates spatially distributed Green-Ampt infiltration parameters from SSURGO soil data.

## 🚀 Overview

This plugin provides a QGIS Processing toolbox algorithm that wraps the [green-ampt-estimation](green-ampt-estimation/) command-line tool, making it easy to generate Green-Ampt infiltration parameters directly within QGIS.

**Key Features:**
- 🗺️ **Seamless QGIS Integration**: Access via Processing Toolbox
- 📊 **Multiple Parameter Methods**: Texture lookup (Rawls/SWMM), HSG lookup, or pedotransfer functions
- 🌐 **Flexible Data Sources**: Live SSURGO queries via PySDA or local SSURGO extracts
- 📦 **Complete Outputs**: Raster GeoTIFFs and vector parameters with optional raw data export
- 🔄 **Easy Maintenance**: Core logic maintained in separate CLI repository

## 📦 Installation

### Method 1: Install from ZIP (Recommended for Users)

1. **Download the Plugin Package:**
   - Download the latest `green_ampt_plugin_v{VERSION}.zip` from the [Releases page](https://github.com/ddivittorio/qgis_green_ampt_plugin_jules/releases)
   - Or create it yourself: run `./package_plugin.sh` (Linux/Mac) or `package_plugin.bat` (Windows)

2. **Install in QGIS:**
   - Open QGIS
   - Go to `Plugins` → `Manage and Install Plugins`
   - Click `Install from ZIP`
   - Select the downloaded `green_ampt_plugin_v{VERSION}.zip` file
   - Click `Install Plugin`

3. **Enable the Plugin:**
   - In the Plugin Manager, go to the `Installed` tab
   - Check the box next to "Green-Ampt Parameter Generator"

### Method 2: Manual Installation (For Developers)

### Prerequisites

- QGIS 3.18 or later
- Python packages (typically included with QGIS):
  - `geopandas`
  - `rasterio`
  - `pandas`
  - `numpy`
  - `requests`
  - `pyyaml`

### Install the Plugin

1. **Download or Clone this Repository:**
   ```bash
   git clone --recursive https://github.com/ddivittorio/qgis_green_ampt_plugin_jules.git
   cd qgis_green_ampt_plugin_jules
   ```

2. **Initialize the green-ampt-estimation submodule (if not already done):**
   ```bash
   git submodule update --init --recursive
   ```

3. **Copy the Plugin to QGIS:**
   
   **Linux/Mac:**
   ```bash
   cp -r green_ampt_plugin ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   ```
   
   **Windows:**
   ```powershell
   xcopy /E /I green_ampt_plugin %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\green_ampt_plugin
   ```

4. **Enable the Plugin in QGIS:**
   - Open QGIS
   - Go to `Plugins` → `Manage and Install Plugins`
   - Click on `Installed` tab
   - Check the box next to "Green-Ampt Parameter Generator"

## 🎯 Usage

### Accessing the Algorithm

1. Open the **Processing Toolbox** (`Processing` → `Toolbox`)
2. Expand the **Green-Ampt Parameter Generator** provider
3. Double-click **"Generate Green-Ampt Parameters from SSURGO"**

### Input Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| **Area of Interest (AOI)** | Polygon vector layer defining your study area | Yes |
| **Output Directory** | Folder where results will be saved | Yes |
| **Data Source** | Choose "PySDA" for live queries or "Local SSURGO files" | Yes |
| **Parameter Method** | Texture Lookup (default), HSG Lookup, or Pedotransfer Functions | Yes |
| **Output Resolution** | Raster pixel size in CRS units (default: 10.0) | No |
| **Output CRS** | EPSG code (e.g., "EPSG:4326") or leave empty to use AOI CRS | No |
| **Output Prefix** | Optional prefix for output filenames | No |
| **Depth Limit** | Soil horizon depth limit in cm (default: 10.0) | No |
| **PySDA Timeout** | Timeout for live queries in seconds (default: 300) | No |
| **Export Raw Data** | Save fetched SSURGO data for QA/reproducibility | No |

### Parameter Estimation Methods

1. **Texture Lookup (Rawls/SWMM)** - Default method
   - Uses USDA texture classes
   - Based on Rawls and SWMM lookup tables
   - Best for general hydrologic modeling

2. **HSG Lookup (Hydrologic Soil Groups)**
   - Uses NRCS Hydrologic Soil Groups (A, B, C, D)
   - Based on infiltration rate ranges
   - Useful for simplified modeling

3. **Pedotransfer Functions**
   - Calculates parameters from sand/clay percentages
   - Most detailed but requires complete soil data
   - Best for research applications

### Output Files

The algorithm generates the following outputs in your specified directory:

```
output_dir/
├── rasters/
│   ├── Ks_inhr.tif        # Hydraulic conductivity (in/hr) - for Texture/HSG methods
│   ├── psi_in.tif         # Suction head (inches) - for Texture/HSG methods
│   ├── theta_s.tif        # Saturated moisture content (fraction)
│   ├── theta_i.tif        # Initial moisture content (fraction)
│   ├── theta_fc.tif       # Field capacity (fraction) - for Texture/HSG methods
│   ├── theta_wp.tif       # Wilting point (fraction) - for Texture/HSG methods
│   ├── ksat.tif           # Hydraulic conductivity (cm/hr) - for Pedotransfer method
│   └── psi.tif            # Suction head (cm) - for Pedotransfer method
├── vectors/
│   └── green_ampt_params.shp  # Vector layer with all parameters
└── raw_data/              # Optional: raw SSURGO data
    ├── mupolygon_raw.shp
    ├── mapunit_raw.txt
    ├── component_raw.txt
    └── chorizon_raw.txt
```

### Example Workflow

1. **Load your study area** polygon layer into QGIS
2. **Open the algorithm** from the Processing Toolbox
3. **Select your AOI layer** as input
4. **Choose an output directory**
5. **Select "PySDA"** as data source (requires internet)
6. **Choose "Texture Lookup"** as parameter method
7. **Click Run** and wait for processing to complete
8. **Generated rasters** will be automatically added to your map canvas

## 🔄 Updating the Core Tool

The plugin architecture is designed to make updates easy:

1. The core Green-Ampt logic lives in `green-ampt-estimation/`
2. The plugin wraps this functionality via the Processing framework
3. To update the core tool:
   ```bash
   cd green-ampt-estimation
   git pull origin main
   ```
4. No plugin reinstallation needed - changes take effect immediately

## 🐛 Troubleshooting

### "Failed to import green_ampt_tool modules"
- Ensure the `green-ampt-estimation` submodule is initialized
- Run: `git submodule update --init --recursive`

### "PySDA timeout" or empty results
- Increase the timeout parameter
- Check internet connectivity
- Verify your AOI overlaps SSURGO coverage area (primarily CONUS)
- Try reducing AOI size for testing

### Missing Python dependencies
- QGIS should include most required packages
- If needed, install to QGIS Python environment:
  ```bash
  # Linux/Mac
  pip3 install --target ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins geopandas rasterio
  
  # Windows (use OSGeo4W Shell)
  python -m pip install geopandas rasterio
  ```

## 📚 Documentation

- **Plugin Documentation**: This README
- **Core Tool Documentation**: See [green-ampt-estimation/README.md](green-ampt-estimation/README.md)
- **API Reference**: [green-ampt-estimation/docs/](green-ampt-estimation/docs/)
- **Configuration Guide**: [green-ampt-estimation/docs/CONFIGURATION_GUIDE.md](green-ampt-estimation/docs/CONFIGURATION_GUIDE.md)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For core functionality changes, contribute to the [green-ampt-estimation](https://github.com/ddivittorio/green-ampt-estimation) repository.

## 📖 Citation

If you use this plugin in your research, please cite:

```bibtex
@software{divittorio2024greenampt,
  author = {DiVittorio, Daniel},
  title = {Green-Ampt Parameter Generator QGIS Plugin},
  year = {2024},
  url = {https://github.com/ddivittorio/qgis_green_ampt_plugin_jules},
  note = {QGIS plugin for generating spatially distributed Green-Ampt infiltration parameters from SSURGO soil data}
}
```

Also cite the underlying SSURGO data:
```
Soil Survey Staff, Natural Resources Conservation Service, United States Department 
of Agriculture. Soil Survey Geographic (SSURGO) Database. Available online. 
Accessed [date].
```

## 📄 License

This project is licensed under the GNU General Public License v2.0 or later - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PySDA**: This plugin incorporates [PySDA](https://github.com/ncss-tech/pysda) for accessing USDA-NRCS Soil Data Access
- **USDA-NRCS**: For providing the SSURGO database and Soil Data Access service
- **QGIS Community**: For the excellent QGIS Processing framework
- **Curve Number Generator Plugin**: Architecture inspiration from [ar-siddiqui/curve_number_generator](https://github.com/ar-siddiqui/curve_number_generator)

## 📧 Contact

- **Author**: Daniel DiVittorio
- **Email**: ddivittorio@gmail.com
- **Issues**: [GitHub Issues](https://github.com/ddivittorio/qgis_green_ampt_plugin_jules/issues)

Happy infiltration modeling! 💧🌍
