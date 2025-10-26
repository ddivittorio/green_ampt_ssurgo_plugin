# Testing Scripts

## `run_all_tests.sh`

Comprehensive end-to-end testing script for the Green-Ampt Estimation Toolkit.

### Features

- Tests all three parameter estimation modes:
  - Pedotransfer functions (sand/clay percentages)
  - Texture lookup (USDA texture classes with Rawls/SWMM parameters)
  - HSG lookup (NRCS Hydrologic Soil Groups)

- Multiple test levels:
  - **CLI tests** (local with synthetic data)
  - **Docker build and CLI tests** (optional)
  - **Jupyter notebook tests** (optional, headless execution)

- Automatic fallback to synthetic test data when PySDA is unavailable
- Clear logging with color-coded output
- Comprehensive test summary with pass/skip/fail counts

### Usage

Basic usage (CLI tests only):
```bash
cd /path/to/green-ampt-estimation
SKIP_DOCKER=1 SKIP_NOTEBOOK=1 bash scripts/run_all_tests.sh
```

Full test suite (includes Docker and notebook tests):
```bash
bash scripts/run_all_tests.sh
```

**Note**: The full suite includes Docker image building (can take 5-10 minutes) and notebook execution tests. For faster iteration during development, use the quick test above.

### Environment Variables

- `SKIP_DOCKER=1` - Skip Docker build and container tests (recommended for faster testing)
- `SKIP_NOTEBOOK=1` - Skip Jupyter notebook headless execution tests

### Test Data

The script automatically creates synthetic SSURGO test data when:
1. PySDA is unavailable (network restrictions or service issues), OR
2. The synthetic data directory doesn't exist yet

This ensures tests can run reliably in any environment. The synthetic data includes:

- Map unit polygons (spatial data)
- Map unit, component, and horizon tables (tabular data)
- Realistic soil properties for testing all parameter estimation methods

### Output

Test outputs are written to:
- `outputs/cli_local_<mode>/` - CLI test results for each mode
- `outputs/cli_docker_<mode>/` - Docker CLI test results
- `outputs/notebook_<type>_test/` - Notebook test results
- `outputs/test_ssurgo_data/` - Synthetic test data

Each test directory contains:
- `rasters/` - Generated Green-Ampt parameter GeoTIFFs
- `vectors/` - Parameter shapefiles
- `raw_data/` - SSURGO input data
- `*.log` - Execution logs

### Exit Codes

- `0` - All tests passed (some may have been skipped)
- `1` - One or more tests failed

## `create_test_data.py`

Generates synthetic SSURGO test data for offline testing.

### Usage

```bash
python scripts/create_test_data.py <output_directory>
```

Example:
```bash
python scripts/create_test_data.py outputs/my_test_data
```

This creates:
- `mupolygon_raw.shp` - Spatial map unit polygons
- `mapunit_raw.txt` - Map unit metadata
- `component_raw.txt` - Soil component data
- `chorizon_raw.txt` - Soil horizon properties

The generated data matches the schema expected by the Green-Ampt toolkit and includes
realistic soil properties for multiple texture classes and hydrologic soil groups.
