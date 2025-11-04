"""
Test suite for the Green-Ampt Estimation Toolkit.

This package contains comprehensive unit tests for all core modules:
- config: Configuration and path handling
- data_access: AOI loading and SSURGO data access
- processing: Spatial operations and soil property aggregation
- parameters: Green-Ampt parameter calculations
- export: Data export functionality
- rasterization: Vector-to-raster conversion
- lookup: US texture-based parameter lookups

Run all tests:
    python -m pytest green_ampt_tool/tests/

Run specific module tests:
    python -m pytest green_ampt_tool/tests/test_config.py

Run with verbose output:
    python -m pytest green_ampt_tool/tests/ -v
"""

__version__ = "1.0.0"
