"""
Green-Ampt QGIS Plugin Test Suite
==================================

This test suite validates all functionality of the Green-Ampt Parameter Generator QGIS plugin.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions  
- system/: End-to-end system tests
- fixtures/: Test data and configuration files

Running Tests:
```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/system/

# Run with coverage
python -m pytest tests/ --cov=green_ampt_plugin --cov-report=html
```

Test Coverage Areas:
- Plugin loading and initialization
- SSURGO data access and texture classification
- Algorithm parameter validation
- Workflow execution
- Output generation and file operations
- Auto-loading functionality
- Error handling and edge cases
"""