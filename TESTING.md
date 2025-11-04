# Green-Ampt QGIS Plugin Test Suite

## Overview

This comprehensive test suite validates all functionality of the Green-Ampt Parameter Generator QGIS plugin. The tests are organized into three categories:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test component interactions and workflows  
- **System Tests** (`tests/system/`): End-to-end functionality and real-world scenarios

## Quick Start

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run with coverage report
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file test_data_access.py

# Run tests without QGIS dependencies
python run_tests.py --no-qgis
```

### Alternative (using pytest directly)

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=green_ampt_plugin --cov-report=html
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **`test_plugin_loading.py`**: Plugin initialization and provider registration
- **`test_data_access.py`**: SSURGO data access and texture classification
- **`test_algorithm_parameters.py`**: Parameter validation and input handling
- **`test_auto_loading.py`**: Auto-loading functionality tests
- **`test_auto_loading_analysis.py`**: Identifies current auto-loading bugs

### Integration Tests (`tests/integration/`)

- **`test_algorithm_workflow.py`**: Complete workflow execution and output generation

### System Tests (`tests/system/`)

- **`test_end_to_end.py`**: Real-world scenarios, performance, and scalability

## Test Configuration

### pytest.ini

The test suite uses pytest with the following configuration:

- Test discovery in `tests/` directory
- Markers for categorizing tests (unit, integration, system, slow, etc.)
- Coverage reporting with 70% minimum threshold
- HTML coverage reports generated in `tests/coverage_html_report/`

### Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests  
- `@pytest.mark.system`: System tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.requires_qgis`: Tests requiring QGIS environment
- `@pytest.mark.requires_ssurgo`: Tests requiring SSURGO data access
- `@pytest.mark.mock_only`: Tests using only mocked dependencies

## Test Data and Fixtures

### Test Fixtures (`tests/fixtures/`)

- **AOI Files**: Mock area-of-interest files in various formats
- **Mock SSURGO Data**: Simulated soil survey data for testing
- **Expected Outputs**: Reference files for validation

### Creating Test Data

```bash
cd tests/fixtures
python create_test_data.py
```

## Current Test Results and Known Issues

### ✅ Working Functionality

- Plugin loading and initialization
- SSURGO data access and texture classification fix  
- Parameter validation and error handling
- Basic workflow execution
- Output file generation

### ⚠️ Identified Issues

**Auto-Loading Vector Toggle Not Working**

The test suite has identified the specific bug preventing the vector auto-loading feature from working:

1. **Issue**: `_load_output_layers` method exists but is **NOT CALLED** in `processAlgorithm`
2. **Location**: `green_ampt_plugin/green_ampt_processing/algorithms/green_ampt_ssurgo.py`
3. **Impact**: Vector layers are generated but not automatically loaded into QGIS
4. **Fix Required**: Add `self._load_output_layers(...)` call after output generation

To see the detailed analysis:

```bash
python -m pytest tests/unit/test_auto_loading_analysis.py -v -s
```

## Test Coverage

Current test coverage includes:

- **Plugin Architecture**: Loading, providers, algorithms
- **Data Access**: SSURGO queries, texture classification, PySDA integration
- **Parameter Handling**: Validation, type checking, error handling
- **Workflow Execution**: Configuration, processing, output generation
- **Output Generation**: File creation, format validation
- **Auto-Loading Analysis**: Bug identification and documentation

## Development Workflow

### Adding New Tests

1. Create test file in appropriate category directory
2. Use fixtures from `tests/fixtures/`
3. Add appropriate markers
4. Run tests to verify functionality

### Test-Driven Development

1. Write failing tests for new functionality
2. Implement functionality to pass tests
3. Refactor and ensure all tests pass
4. Update documentation

### Running Tests During Development

```bash
# Quick tests (no QGIS, no slow tests)
python run_tests.py --no-qgis --fast

# Full test suite
python run_tests.py --coverage --html-coverage
```

## CI/CD Integration

The test suite is designed for easy integration with continuous integration systems:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r test_requirements.txt
    python run_tests.py --coverage --no-qgis
```

## Debugging Tests

### Using pytest with debugging

```bash
# Run with detailed output
pytest tests/ -v -s

# Run single test with debugging
pytest tests/unit/test_data_access.py::TestSSURGODataAccess::test_fetch_chorizon_records -v -s

# Drop into debugger on failure
pytest tests/ --pdb
```

### Test Output Analysis

The auto-loading analysis test provides detailed diagnostic output showing exactly what's wrong with the current implementation. This makes it easy to identify and fix issues.

## Contributing

When contributing to the test suite:

1. Ensure all new functionality has corresponding tests
2. Run the full test suite before committing
3. Update this documentation for any new test categories
4. Use descriptive test names and docstrings
5. Include both positive and negative test cases

## Next Steps

1. **Fix Auto-Loading Bug**: Use test analysis to implement the missing method call
2. **Add QGIS Integration Tests**: Tests that run in actual QGIS environment
3. **Performance Benchmarks**: Add timing and memory usage benchmarks
4. **Mock SSURGO Server**: Create local mock server for testing data access
5. **Automated Testing**: Set up CI/CD pipeline for automated test execution

For questions or issues with the test suite, see the test output or run the analysis tests for detailed diagnostics.