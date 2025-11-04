# Testing Documentation

## Overview

The Green-Ampt Estimation Toolkit includes a comprehensive test suite to ensure functionality is maintained during development and iterations. The test suite covers all core modules and validates both normal operation and error handling.

## Test Coverage

### Summary Statistics

- **Total Tests:** 117
- **Test Modules:** 6
- **Code Coverage:** Core functionality (config, data_access, processing, parameters, export, rasterization)

### Test Breakdown by Module

| Module | Test File | Test Count | Coverage |
|--------|-----------|------------|----------|
| `config.py` | `test_config.py` | 17 tests | Configuration validation, path handling, error cases |
| `data_access.py` | `test_data_access.py` | 7 tests | AOI loading, SSURGO data structures, CRS handling |
| `processing.py` | `test_processing.py` | 43 tests | Spatial operations, aggregations, HSG parsing |
| `parameters.py` | `test_parameters.py` | 28 tests | Pedotransfer functions, parameter enrichment, utilities |
| `export.py` | `test_export.py` | 9 tests | Vector and raw data export functionality |
| `rasterization.py` | `test_rasterization.py` | 13 tests | Grid preparation, rasterization operations |

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install pytest
pip install -r requirements.txt
```

### Basic Test Execution

Run all tests:

```bash
python -m pytest green_ampt_tool/tests/
```

Run with verbose output:

```bash
python -m pytest green_ampt_tool/tests/ -v
```

Run specific test module:

```bash
python -m pytest green_ampt_tool/tests/test_config.py -v
```

Run specific test:

```bash
python -m pytest green_ampt_tool/tests/test_config.py::TestPipelineConfig::test_basic_initialization -v
```

### Using the Test Runner Script

The repository includes a test runner script with additional options:

```bash
# Basic run
./scripts/run_tests.sh

# Verbose output
./scripts/run_tests.sh --verbose

# Save results to log file
./scripts/run_tests.sh --log-file test_results.log

# Generate coverage report (requires pytest-cov)
./scripts/run_tests.sh --coverage

# Combine options
./scripts/run_tests.sh --verbose --log-file test_results.log
```

### CI/CD Integration

Tests can be easily integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install pytest
    pip install -r requirements.txt
    python -m pytest green_ampt_tool/tests/ -v
```

## Test Organization

### Test Structure

Tests are organized by module with the following structure:

```
green_ampt_tool/tests/
├── test_config.py           # Configuration module tests
├── test_data_access.py      # Data loading and access tests
├── test_export.py           # Export functionality tests
├── test_lookup_us.py        # US lookup table tests (existing)
├── test_parameters.py       # Parameter calculation tests
├── test_processing.py       # Processing and aggregation tests
└── test_rasterization.py    # Rasterization tests
```

### Test Classes

Each test file contains multiple test classes that group related tests:

- **Class naming:** `Test<FunctionName>` or `Test<FeatureName>`
- **Method naming:** `test_<specific_behavior>`
- **Fixtures:** Use `tmp_path` for temporary file operations

Example:
```python
class TestPipelineConfig:
    """Test PipelineConfig initialization and validation."""
    
    def test_basic_initialization(self, tmp_path):
        """Test basic config initialization with required parameters."""
        # Test implementation
```

## Test Categories

### 1. Configuration Tests (`test_config.py`)

Tests for `config.py` module:

- **Path validation:** Verifies that file paths exist and are accessible
- **Configuration initialization:** Tests proper setup of PipelineConfig
- **Error handling:** Validates error messages for invalid configurations
- **Path generation:** Tests raster and vector path building
- **CRS inheritance:** Tests CRS handling from AOI

Key test cases:
- Missing AOI file raises FileNotFoundError
- Negative resolution raises ValueError
- Output directories are created automatically
- Prefix handling in output filenames

### 2. Data Access Tests (`test_data_access.py`)

Tests for `data_access.py` module:

- **AOI loading:** Tests reading and CRS reprojection
- **SSURGO loading:** Tests local file loading
- **Column validation:** Tests required column checking
- **Data merging:** Tests mukey merging between tables

Key test cases:
- AOI reprojection to WGS84
- Empty geometry detection
- Missing required columns error handling
- Pipe-delimited file parsing

### 3. Processing Tests (`test_processing.py`)

Tests for `processing.py` module:

- **Spatial clipping:** Tests polygon clipping to AOI
- **Property aggregation:** Tests weighted mean calculations
- **HSG parsing:** Tests hydrologic soil group parsing
- **Component summarization:** Tests depth-weighted aggregations

Key test cases:
- CRS mismatch handling during clipping
- Depth limiting in horizon aggregation
- Theta_s (porosity) bounds checking
- Dual HSG format parsing (e.g., "A/D")
- Major component prioritization

### 4. Parameters Tests (`test_parameters.py`)

Tests for `parameters.py` module:

- **Pedotransfer functions:** Tests wetting front suction calculations
- **Parameter enrichment:** Tests Green-Ampt parameter generation
- **Lookup tables:** Tests texture-based parameter lookup
- **HSG-based parameters:** Tests hydrologic soil group lookups
- **Initial deficit modes:** Tests design vs continuous moisture modes

Key test cases:
- Sand and clay percentage clamping
- Theta_s bounds (0 to 0.9)
- Custom suction functions
- Missing column defaults
- Initial moisture calculations

### 5. Export Tests (`test_export.py`)

Tests for `export.py` module:

- **Vector export:** Tests shapefile writing
- **Raw data export:** Tests SSURGO data archival
- **Format validation:** Tests pipe-delimited and shapefile formats
- **Overwrite behavior:** Tests file replacement

Key test cases:
- Directory creation for exports
- Pipe delimiter in text files
- CRS preservation in shapefiles
- Multiple parameter columns in output

### 6. Rasterization Tests (`test_rasterization.py`)

Tests for `rasterization.py` module:

- **Grid preparation:** Tests raster grid calculation
- **Rasterization:** Tests vector-to-raster conversion
- **Resolution handling:** Tests pixel size calculations
- **CRS reprojection:** Tests coordinate system transformations
- **Format validation:** Tests GeoTIFF output

Key test cases:
- Grid dimensions match resolution
- Higher resolution increases pixel count
- Missing parameters are skipped
- NaN handling for missing values
- Metadata tags in output

## Writing New Tests

### Test Template

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.module_name import function_to_test


class TestFunctionName:
    """Test function_name behavior."""
    
    def test_basic_case(self):
        """Test basic functionality."""
        result = function_to_test(input_data)
        assert result == expected_value
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError, match="error message"):
            function_to_test(invalid_input)
    
    def test_edge_case(self):
        """Test edge case behavior."""
        result = function_to_test(edge_case_input)
        assert result is not None
```

### Best Practices

1. **Use descriptive names:** Test names should clearly describe what is being tested
2. **Test one thing:** Each test should verify a single behavior
3. **Use fixtures:** Use pytest fixtures for common setup (especially `tmp_path`)
4. **Test both success and failure:** Include both positive and negative test cases
5. **Use parametrization:** For testing multiple similar cases, use `@pytest.mark.parametrize`
6. **Document with docstrings:** Add clear docstrings explaining what each test validates
7. **Clean up resources:** Use context managers and fixtures for cleanup
8. **Isolate tests:** Tests should not depend on each other

### Example: Testing with Temporary Files

```python
def test_with_files(self, tmp_path):
    """Test functionality that requires files."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")
    
    # Run function
    result = process_file(test_file)
    
    # Verify results
    assert result.exists()
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install pytest
          pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest green_ampt_tool/tests/ -v
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'pytest'**
   - Solution: `pip install pytest`

2. **ModuleNotFoundError: No module named 'pandas'**
   - Solution: `pip install -r requirements.txt`

3. **Tests fail with "rasterio not available"**
   - This is expected if rasterio is not installed
   - Rasterization tests are skipped automatically
   - For full testing: `conda install -c conda-forge rasterio`

4. **Permission denied on test script**
   - Solution: `chmod +x scripts/run_tests.sh`

5. **Tests pass locally but fail in CI**
   - Check Python version consistency
   - Verify all dependencies are installed
   - Check for platform-specific issues

## Test Maintenance

### Adding New Tests

When adding new functionality:

1. Create tests before or alongside implementation (TDD recommended)
2. Add tests to appropriate test file or create new test file
3. Ensure all tests pass: `python -m pytest green_ampt_tool/tests/`
4. Update this documentation if adding new test categories

### Updating Existing Tests

When modifying existing functionality:

1. Update affected tests to match new behavior
2. Add new tests for new edge cases
3. Ensure backward compatibility tests still pass
4. Document any breaking changes

### Deprecated Functionality

When deprecating functionality:

1. Mark tests with `@pytest.mark.skip` or remove them
2. Document the deprecation in test docstrings
3. Consider keeping tests for one release cycle with deprecation warnings

## Performance Considerations

- Tests run in ~1-2 seconds on typical hardware
- Rasterization tests may take longer due to file I/O
- Use `pytest -k "not slow"` to skip slow tests during development
- Consider marking slow tests with `@pytest.mark.slow` decorator

## Future Enhancements

Potential improvements to the test suite:

- [ ] Add integration tests for complete pipeline workflows
- [ ] Add performance benchmarking tests
- [ ] Add code coverage reporting (pytest-cov)
- [ ] Add property-based testing with Hypothesis
- [ ] Add mutation testing to verify test quality
- [ ] Add visual regression tests for map outputs
- [ ] Add load testing for large AOIs

## Support

For questions about testing:

1. Check this documentation
2. Review existing tests for examples
3. Open an issue on GitHub
4. Consult pytest documentation: https://docs.pytest.org/
