# Test Configuration for Green-Ampt QGIS Plugin

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "green_ampt_plugin"))
sys.path.insert(0, str(PROJECT_ROOT / "green-ampt-estimation"))

# Test data paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DATA_DIR = FIXTURES_DIR / "test_data"
MOCK_AOI_DIR = FIXTURES_DIR / "aoi_files"
EXPECTED_OUTPUTS_DIR = FIXTURES_DIR / "expected_outputs"

# QGIS Testing Configuration
QGIS_TESTING = os.environ.get('QGIS_TESTING', 'false').lower() == 'true'
QGIS_PREFIX_PATH = os.environ.get('QGIS_PREFIX_PATH', '/usr')

# Test database configuration (for SSURGO testing)
TEST_DB_CONFIG = {
    'use_mock_data': True,
    'mock_mukeys': ['123456', '789012', '345678'],
    'expected_texture_classes': ['SL', 'L', 'CL']
}

# Algorithm testing parameters
ALGORITHM_TEST_PARAMS = {
    'test_aoi_paths': [
        str(MOCK_AOI_DIR / "small_polygon.shp"),
        str(MOCK_AOI_DIR / "medium_polygon.gpkg"),
        str(MOCK_AOI_DIR / "large_polygon.geojson")
    ],
    'output_formats': ['ESRI Shapefile', 'GeoPackage', 'GeoJSON'],
    'texture_methods': ['lookup', 'rosetta'],
    'expected_parameters': ['ks', 'theta_s', 'theta_r', 'alpha', 'n']
}

# Auto-loading test configuration
AUTO_LOADING_TESTS = {
    'test_vector_loading': True,
    'test_raster_loading': True,
    'expected_layer_count': {'vector': 1, 'raster': 3}  # ks, theta_s, psi
}