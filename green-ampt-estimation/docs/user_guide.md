# Green-Ampt Toolkit — Step-by-Step User Guide

This guide walks you from a clean machine to raster outputs using the modular Green-Ampt pipeline. Follow the sections in order; each builds on the previous step.

## 1. Verify prerequisites

1. **Operating system**: Linux or macOS (Windows WSL works, too).
2. **Conda**: Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Mambaforge](https://github.com/conda-forge/miniforge). These bundles ship GDAL/GEOS/PROJ, avoiding manual compilation.
3. **Git**: Required to clone this repository and the PySDA dependency.
4. **Disk space**: Plan for several GB if you download full SSURGO datasets.

## 2. Clone the repository

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/<your-account>/Green_Ampt_Estimation.git
cd Green_Ampt_Estimation
```

If you cloned without the `external/pysda` directory, fetch it now:

```bash
git clone https://github.com/ncss-tech/pysda external/pysda
```

## 3. Create and activate the conda environment

```bash
conda create -n green-ampt -c conda-forge python=3.10 geopandas rasterio pandas numpy requests
conda activate green-ampt
pip install -r requirements.txt
```

Why conda? It provides pre-built binary wheels for geospatial libraries so you can avoid compiling GDAL/PROJ.

## 4. Prepare input data

Choose one of two data sources:

- **Local SSURGO extracts**: Download `mupolygon.shp`, `mapunit.txt`, `component.txt`, and `chorizon.txt` that cover your AOI. Web Soil Survey exports meet the requirements.
- **Live SDA (PySDA)**: Ensure the AOI is modest in size—SDA rejects very large polygons—and that outbound HTTPS access is permitted.

Store all inputs in a predictable folder, for example:

```text
data/
  aoi.shp
  ssurgo/
    mupolygon.shp
    mapunit.txt
    component.txt
    chorizon.txt
```

## 5. Inspect and, if needed, reproject the AOI

The workflow expects the AOI to have a defined CRS; it reprojects to WGS84 internally. To check:

```bash
python - <<'PY'
import geopandas as gpd
print(gpd.read_file('data/aoi.shp').crs)
PY
```

If the CRS is missing, fix it using GIS software (QGIS/ArcGIS) or GeoPandas.

## 6. Run the pipeline with local SSURGO files

The toolkit now defaults to the **texture lookup** method (Rawls/SWMM parameters), which is recommended for most users. You can also use **HSG-based lookup** or **pedotransfer functions**.

### Using default settings (texture lookup with live PySDA)

```bash
python green_ampt.py \
  --aoi data/aoi.shp \
  --output-dir outputs/
```

This uses the new defaults:
- `--data-source pysda` (live SSURGO queries)
- `--output-resolution 10.0` (10-meter pixels)
- `--output-crs` (inherits from AOI)
- `--depth-limit-cm 10.0` (0-10 cm surface window, suitable for runoff modeling)
- `--export-raw-data` (saves fetched data)
- `--use-lookup-table` (texture-based parameters)

### Using local SSURGO files

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

### Parameter estimation methods

The toolkit offers three methods for estimating Green-Ampt parameters:

**1. Texture lookup (default)**: Uses USDA texture classes and the Rawls/SWMM lookup table
```bash
python green_ampt.py --aoi data/aoi.shp --output-dir outputs/ --use-lookup-table
```

**2. HSG lookup**: Uses NRCS Hydrologic Soil Groups (A=high infiltration, B=moderate, C=slow, D=very slow) with Ksat ranges from the Green-Ampt SWMM Parameters reference
```bash
python green_ampt.py --aoi data/aoi.shp --output-dir outputs/ --use-hsg-lookup
```

**3. Pedotransfer functions**: Calculates parameters from sand/clay percentages
```bash
python green_ampt.py --aoi data/aoi.shp --output-dir outputs/ --use-pedotransfer
```

Key tips:

- The default `output-crs` now inherits from your AOI, eliminating the need to specify it manually
- Use `--output-resolution 30` for coarser output if needed
- Adjust `depth-limit-cm` to 30 if you need deeper soil horizons (default is now 10 cm for infiltration-excess modeling)
- Add `--no-export-raw-data` to skip saving raw SSURGO data

## 7. Run the pipeline with live PySDA queries

Live PySDA queries are now the **default** data source. Simply omit the `--data-source` flag:

```bash
python green_ampt.py \
  --aoi data/aoi.shp \
  --output-dir outputs/
```

Or explicitly specify PySDA with custom options:

```bash
python green_ampt.py \
  --aoi data/aoi.shp \
  --output-dir outputs/ \
  --data-source pysda \
  --pysda-timeout 300
```

Guidelines when using SDA:

- Keep the AOI small; SDA truncates requests that span multiple states.
- Retry with a lower timeout if your connection is slow or the service is busy.
- The default timeout is 300 seconds (5 minutes).

## 8. Understand the outputs

The command writes GeoTIFF rasters to `outputs/rasters/` (or your chosen directory). The output files depend on the parameter estimation method used:

### Texture Lookup (default) or HSG Lookup outputs:

| File | Description |
| --- | --- |
| `Ks_inhr_green_ampt.tif` | Saturated hydraulic conductivity (in/hr). |
| `psi_in_green_ampt.tif` | Wetting front suction head (inches). |
| `theta_s_green_ampt.tif` | Saturated volumetric water content (fraction). |
| `theta_fc_green_ampt.tif` | Field capacity (fraction). |
| `theta_wp_green_ampt.tif` | Wilting point (fraction). |
| `theta_i_green_ampt.tif` | Initial volumetric water content (fraction, design or continuous mode). |

### Pedotransfer Function outputs:

| File | Description |
| --- | --- |
| `ksat_green_ampt.tif` | Hydraulic conductivity (cm/hr). |
| `theta_s_green_ampt.tif` | Saturated volumetric water content (fraction). |
| `psi_green_ampt.tif` | Wetting front suction head (cm). |
| `theta_i_green_ampt.tif` | Initial volumetric water content (constant default 0.2). |

**Raw data exports** (enabled by default): The `raw_data/` folder contains the original datasets:

- `mupolygon_raw.shp` — shapefile copy of the fetched polygons.
- `mapunit_raw.txt`, `component_raw.txt`, `chorizon_raw.txt` — pipe-delimited tables mirroring the SSURGO extracts.

A companion shapefile at `outputs/vectors/green_ampt_params.shp` stores the vector geometries with all parameter fields. All rasters share the same CRS, resolution, and extent.

## 9. Validate results

1. Open the rasters in QGIS or ArcGIS.
2. Confirm the extent matches the AOI.
3. Spot-check attribute values by comparing raster pixels against original SSURGO horizon data.
4. Inspect NoData regions; they should align with areas outside the AOI or with missing soil information.

## 10. Automate or batch process (optional)

For multiple AOIs, script calls to `green_ampt.py` from a shell or Python loop. Example using GNU Parallel:

```bash
parallel "python green_ampt.py --aoi {} --output-dir outputs/{/} --data-source local --mupolygon data/ssurgo/mupolygon.shp --mapunit data/ssurgo/mapunit.txt --component data/ssurgo/component.txt --chorizon data/ssurgo/chorizon.txt" ::: data/aois/*.shp
```

## 11. Troubleshooting checklist

- **ImportError: geopandas** — run `conda install geopandas` inside the `green-ampt` environment.
- **ValueError: AOI geometry is empty** — ensure the AOI layer contains at least one polygon.
- **RuntimeError: No soil properties** — verify the SSURGO tables include the AOI `mukey` values; expand the spatial extent if needed.
- **PySDA returns empty results** — shrink the AOI or switch to local extracts; SDA limits query sizes.
- **Raster resolution too coarse/fine** — tweak `--output-resolution` to match your modeling requirements.

## 12. Next steps and customization

- Edit `green_ampt_tool/parameters.py` to introduce alternative pedotransfer functions.
- Modify `green_ampt_tool/rasterization.py` to change the output file naming or pixel alignments.
- Add tests or sample datasets under `tests/` or `examples/` (not yet bundled) to support continuous integration.

You now have end-to-end rasters ready for infiltration modeling. Happy hydrologizing!
