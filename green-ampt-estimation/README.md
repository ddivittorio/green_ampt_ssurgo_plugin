1# Green-Ampt Estimation Toolkit

Generate spatially distributed Green-Ampt infiltration parameters from SSURGO soil data, either from local extracts or directly from NRCS Soil Data Access (SDA) via PySDA.

## 🚀 Overview

- **NEW**: Configuration file support (YAML/JSON) for reproducible workflows
- **NEW**: Enhanced AOI file format support - Shapefile, GeoPackage, Geodatabase, KML/KMZ, GeoJSON
- **NEW**: Multi-layer format support with layer selection (e.g., `file.gpkg:layer_name`)
- `green_ampt_notebook.ipynb` provides an interactive Jupyter notebook interface with map-based AOI drawing or file import
- `green_ampt.py` provides a command-line interface that wires into the modular package under `green_ampt_tool/`
- The workflow: read the AOI → acquire SSURGO (`local` files or live `pysda`) → compute weighted soil properties → derive Green-Ampt parameters → rasterize (`ksat`, `theta_s`, `psi`, `theta_i`)

## 🧱 Requirements

- Python 3.10+ (tested with 3.10, 3.12)
- Geospatial stack: `geopandas`, `rasterio`, `pandas`, `numpy`, `requests`, `pyyaml` (listed in `requirements.txt`)
- Either:
   - Local SSURGO extracts (`mupolygon.shp`, `mapunit.txt`, `component.txt`, `chorizon.txt`), or
   - Internet access to SDA when using the PySDA data source

### Acknowledging PySDA

This project incorporates the `pysda` library as a Git submodule to fetch data from the NRCS Soil Data Access service. We gratefully acknowledge the work of the `pysda` developers.

- **PySDA GitHub Repository:** [https://github.com/ncss-tech/pysda](https://github.com/ncss-tech/pysda)
- **License:** `pysda` is distributed under the Creative Commons Zero v1.0 Universal license.

For more details, see the [PYSDA_CITATION.md](docs/PYSDA_CITATION.md) file.

> **Heads-up on GDAL/GEOS/PROJ:** Prefer the conda-forge binaries to avoid compiling native dependencies yourself.

## 🛠️ Environment setup

```bash
conda create -n green-ampt -c conda-forge python=3.10 geopandas rasterio pandas numpy requests
conda activate green-ampt

# Optional: install additional utilities
pip install -r requirements.txt
```

For the Jupyter notebook interface, you'll need additional packages:

```bash
```bash
pip install jupyter ipywidgets ipyleaflet matplotlib
```

## 🐳 Docker Usage (Alternative to Local Setup)

For users who prefer containerized deployment or want to avoid environment setup, Docker images are provided.

### Prerequisites

- Docker installed and running
- At least 4GB RAM available for the container

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ddivittorio/green-ampt-estimation.git
   cd green-ampt-estimation
   ```

2. **Build and run:**
   ```bash
   # Build the Docker image
   ./run_docker.sh build

   # Run CLI command
   ./run_docker.sh cli --aoi test_aoi/test_aoi.shp --output-dir outputs --data-source pysda

   # Or start Jupyter notebook
   ./run_docker.sh notebook
   ```

### Docker Commands

```bash
# Build the image
./run_docker.sh build

# Run CLI with arguments
./run_docker.sh cli [your arguments here]

# Start Jupyter notebook (available at http://localhost:8889)
./run_docker.sh notebook

# Show help
./run_docker.sh help
```

### Using Docker Compose Directly

```bash
# Run CLI command
docker-compose run --rm green-ampt --aoi test_aoi/test_aoi.shp --output-dir outputs --data-source pysda

# Start Jupyter notebook
docker-compose --profile notebook up notebook
```

### Docker Image Details

- Based on `condaforge/miniconda3` for reliable geospatial library support
- Includes all required dependencies (GDAL, PROJ, GEOS)
- Mounts `./outputs` and `./test_aoi` directories for data persistence
- Exposes port 8888 for Jupyter notebook access

## 📋 Usage
```

The PySDA modules are imported directly from `external/pysda`. If you checked out the repository without that folder, fetch it now:

```bash
git submodule update --init --recursive  # if tracked as a submodule
# or
git clone https://github.com/ncss-tech/pysda external/pysda
```

## ⚙️ Usage

### Interactive Jupyter Notebook (Recommended for New Users)

The Jupyter notebook provides an interactive interface with map-based AOI selection:

```bash
jupyter notebook green_ampt_notebook.ipynb
```

**Features:**
- 🗺️ **Draw AOI**: Use interactive map tools to draw your study area as a polygon or rectangle
- 📁 **Upload Shapefile**: Import existing shapefiles, GeoPackages, or GeoJSON files
- ⚙️ **Configure Settings**: Adjust output resolution, CRS, depth limits, and data sources
- 🚀 **Run Pipeline**: Execute the workflow with a single button click
- 📊 **Visualize Results**: Preview generated parameter rasters within the notebook

### CLI usage

The CLI supports multiple input formats and configuration methods.

#### Quick Start with Configuration File

```bash
# Create a config file (YAML or JSON)
cat > config.yaml << EOF
aoi: "path/to/aoi.shp"
output_dir: "outputs"
output_resolution: 10.0
EOF

# Run with config file
python green_ampt.py --config config.yaml
```

See [Configuration Guide](docs/CONFIGURATION_GUIDE.md) for detailed examples.

#### Direct CLI Usage

The simplest command using all defaults:

```bash
python green_ampt.py --aoi path/to/aoi.shp --output-dir outputs/
```

This uses:
- `--data-source pysda` (live SSURGO queries)
- `--output-resolution 10.0` (10-meter pixels)
- `--output-crs` (inherits from AOI CRS)
- `--depth-limit-cm 10.0` (0-10 cm surface window, suitable for runoff modeling)
- `--export-raw-data` (saves fetched SSURGO data)
- `--use-lookup-table` (texture-based Rawls/SWMM parameters)

#### Supported AOI Formats

The toolkit supports various geospatial file formats:

- **Shapefile** (`.shp`) - Traditional format
- **GeoPackage** (`.gpkg`) - Modern SQLite-based format with layer support
- **File Geodatabase** (`.gdb`) - ESRI geodatabase with feature class support
- **KML/KMZ** (`.kml`, `.kmz`) - Google Earth format
- **GeoJSON** (`.geojson`, `.json`) - Web-friendly format

For multi-layer formats (GeoPackage, Geodatabase), specify the layer:

```bash
# Method 1: Colon syntax
python green_ampt.py --aoi "data.gpkg:layer_name" --output-dir outputs/

# Method 2: Separate parameter
python green_ampt.py --aoi data.gpkg --aoi-layer layer_name --output-dir outputs/
```

### Parameter Estimation Methods

The toolkit provides three methods for estimating Green-Ampt infiltration parameters:

**1. Texture Lookup (default)** — Uses USDA texture classes with Rawls/SWMM lookup table:
```bash
python green_ampt.py --aoi path/to/aoi.shp --output-dir outputs/ --use-lookup-table
```

**2. HSG Lookup** — Uses NRCS Hydrologic Soil Groups (A=high infiltration, B=moderate, C=slow, D=very slow) with Ksat ranges:
```bash
python green_ampt.py --aoi path/to/aoi.shp --output-dir outputs/ --use-hsg-lookup
```

**3. Pedotransfer Functions** — Calculates parameters from sand/clay percentages:
```bash
python green_ampt.py --aoi path/to/aoi.shp --output-dir outputs/ --use-pedotransfer
```

Key options:

| Option | Description | Default |
| --- | --- | --- |
| `--output-resolution` | Raster pixel size in output CRS units | `10.0` |
| `--output-crs` | Output CRS (omit to inherit from AOI) | `AOI CRS` |
| `--output-prefix` | Prefix for output filenames | `` |
| `--depth-limit-cm` | Depth limit for horizon weighting | `10.0` |
| `--data-source` | SSURGO source: `local` or `pysda` | `pysda` |
| `--export-raw-data` | Save the fetched SSURGO datasets | `True` |
| `--no-export-raw-data` | Skip saving raw SSURGO data | `False` |
| `--raw-data-dir` | Optional location for raw SSURGO exports | `output_dir/raw_data` |
| `--log-level` | Logging verbosity (`INFO`, `DEBUG`, ...) | `INFO` |

### Local SSURGO files

When using local SSURGO extracts:

```bash
python green_ampt.py \
   --aoi data/aoi.shp \
   --output-dir outputs/ \
   --data-source local \
   --mupolygon data/ssurgo/mupolygon.shp \
   --mapunit data/ssurgo/mapunit.txt \
   --component data/ssurgo/component.txt \
   --chorizon data/ssurgo/chorizon.txt
```

### Direct SDA (PySDA)

Live queries are now the default. Simply omit `--data-source`:

```bash
python green_ampt.py \
   --aoi data/aoi.shp \
   --output-dir outputs/
```

Or specify explicitly with custom timeout:

```bash
python green_ampt.py \
   --aoi data/aoi.shp \
   --output-dir outputs/ \
   --data-source pysda \
   --pysda-timeout 300
```

The PySDA path is added automatically from `external/pysda` if the package import fails.

To ensure the submodule is cloned, run:
```bash
git submodule update --init --recursive
```

## 📦 Outputs

Output files depend on the parameter estimation method:

### Texture Lookup (default) or HSG Lookup
- Raster GeoTIFFs in `<output-dir>/rasters/`: `Ks_inhr`, `psi_in`, `theta_s`, `theta_fc`, `theta_wp`, `theta_i`
- Units: Ks in in/hr, psi in inches, moisture contents as fractions

### Pedotransfer Functions
- Raster GeoTIFFs in `<output-dir>/rasters/`: `ksat`, `theta_s`, `psi`, `theta_i`
- Units: ksat in cm/hr, psi in cm, moisture contents as fractions

### Additional Outputs
- Vector parameters: `<output-dir>/vectors/{prefix_}green_ampt_params.shp` with all derived fields
- Raw SSURGO data (when `--export-raw-data` is enabled, **default**): `<output-dir>/raw_data/` contains:
  - `mupolygon_raw.shp` — spatial data
  - `mapunit_raw.txt`, `component_raw.txt`, `chorizon_raw.txt` — tabular data

Each raster uses the requested CRS/resolution and writes `NaN` as NoData.

## 🔍 Troubleshooting

- **Missing PySDA modules:** Ensure `external/pysda` exists or adjust `PYTHONPATH` to point at your clone.
- **Empty rasters:** Confirm the AOI overlaps SSURGO polygons and that SDA returns mukeys.
- **GDAL errors:** Recreate the environment with conda-forge packages; compiling via pip without system headers typically fails.
- **Slow SDA responses:** Trim the AOI extent; SDA limits request sizes and may return empty results if the area is huge.

## 🧪 Testing

### Unit Tests

The project includes a comprehensive unit test suite with **117 tests** covering all core modules:

```bash
# Run all unit tests
python -m pytest green_ampt_tool/tests/ -v

# Or use the test runner script
./scripts/run_tests.sh

# Save results to a log file
./scripts/run_tests.sh --log-file test_results.log
```

The unit test suite covers:
- **Config module:** Configuration validation, path handling, error cases (17 tests)
- **Data access:** AOI loading, SSURGO data structures, CRS handling (7 tests)
- **Processing:** Spatial operations, aggregations, HSG parsing (43 tests)
- **Parameters:** Pedotransfer functions, parameter enrichment (28 tests)
- **Export:** Vector and raw data export functionality (9 tests)
- **Rasterization:** Grid preparation, rasterization operations (13 tests)

See `docs/TESTING.md` for detailed test documentation.

### End-to-End Tests

Run the comprehensive end-to-end test suite:

```bash
# Quick test (CLI only, uses synthetic data)
SKIP_DOCKER=1 SKIP_NOTEBOOK=1 bash scripts/run_all_tests.sh

# Full test suite (includes Docker and notebooks)
bash scripts/run_all_tests.sh
```

The end-to-end test suite validates all three parameter estimation methods (pedotransfer, texture lookup, HSG lookup) across CLI, Docker, and notebook interfaces. When PySDA is unavailable, it automatically falls back to synthetic test data. See `scripts/README.md` for details.

## 📖 Citation and Acknowledgments

### Citing this software

If you use this toolkit in your research or publications, please cite it as:

```
DiVittorio, D. (2024). Green-Ampt Estimation Toolkit. 
GitHub repository: https://github.com/ddivittorio/green-ampt-estimation
```

For BibTeX:
```bibtex
@software{divittorio2024greenampt,
  author = {DiVittorio, Daniel},
  title = {Green-Ampt Estimation Toolkit},
  year = {2024},
  url = {https://github.com/ddivittorio/green-ampt-estimation},
  note = {Software for generating spatially distributed Green-Ampt infiltration parameters from SSURGO soil data}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.

### Third-party software acknowledgments

This project builds upon [PySDA](https://github.com/ncss-tech/pysda) by Charles Ferguson, which is vendored in `external/pysda/` to provide access to USDA-NRCS Soil Data Access. PySDA is licensed under GPL-3.0 and copyright remains with its original author.

When using the PySDA data source, please acknowledge:
```
This analysis used the Green-Ampt Estimation Toolkit 
(https://github.com/ddivittorio/green-ampt-estimation), which incorporates 
PySDA (https://github.com/ncss-tech/pysda) for accessing USDA-NRCS Soil Data Access.
```

See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md) for complete third-party software attributions and license information.

### Data attribution

SSURGO data should be cited as:
```
Soil Survey Staff, Natural Resources Conservation Service, United States Department 
of Agriculture. Soil Survey Geographic (SSURGO) Database. Available online. 
Accessed [date].
```

## 📚 Project structure

- `green_ampt.py` – CLI entry point.
- `green_ampt_notebook.ipynb` – Interactive Jupyter notebook with map-based AOI selection.
- `green_ampt_tool/` – reusable modules (`data_access`, `processing`, `parameters`, `rasterization`, `workflow`).
- `external/` – vendored third-party libraries.
  - `pysda/` – [PySDA library](https://github.com/ncss-tech/pysda) (GPL-3.0) for NRCS Soil Data Access queries. Includes complete source with LICENSE and README.
- `scripts/` – testing and utility scripts.
  - `run_all_tests.sh` – comprehensive end-to-end test suite.
  - `create_test_data.py` – synthetic SSURGO data generator.
- `docs/` – documentation files.
  - `user_guide.md` – step-by-step instructions from environment setup to raster outputs.
  - `notebook_guide.md` – quick start guide for the Jupyter notebook.
  - `notebook_interface.md` – detailed notebook interface documentation.
- `CITATION.cff` – machine-readable citation metadata (Citation File Format standard).
- `ACKNOWLEDGMENTS.md` – third-party software attributions and license information.

Happy infiltration modelling! 💧
