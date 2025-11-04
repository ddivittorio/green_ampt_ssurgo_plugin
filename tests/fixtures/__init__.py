"""Test fixtures and utilities for Green-Ampt plugin testing."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

def create_mock_aoi_file(geometry_type="Polygon", crs="EPSG:4326", temp_dir=None):
    """Create a mock AOI file for testing."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    # Create a simple GeoJSON for testing
    aoi_data = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": crs}},
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": geometry_type,
                "coordinates": [[
                    [-120.5, 35.5],
                    [-120.4, 35.5], 
                    [-120.4, 35.6],
                    [-120.5, 35.6],
                    [-120.5, 35.5]
                ]]
            },
            "properties": {"test_id": 1, "name": "Test AOI"}
        }]
    }
    
    aoi_file = Path(temp_dir) / "test_aoi.geojson"
    with open(aoi_file, 'w') as f:
        json.dump(aoi_data, f)
    
    return str(aoi_file)

def create_mock_ssurgo_data():
    """Create mock SSURGO data for testing."""
    return {
        'mupolygon': {
            'mukey': ['123456', '789012', '345678'],
            'area_sqm': [1000.0, 2000.0, 1500.0]
        },
        'component': {
            'mukey': ['123456', '123456', '789012', '789012', '345678'],
            'cokey': ['111', '112', '221', '222', '331'],
            'comppct_r': [85, 15, 70, 30, 90],
            'hydgrp': ['B', 'C', 'A', 'B', 'C'],
            'majcompflag': ['Yes', 'No', 'Yes', 'No', 'Yes']
        },
        'chorizon': {
            'cokey': ['111', '112', '221', '222', '331'],
            'hzdept_r': [0, 0, 0, 0, 0],
            'hzdepb_r': [30, 25, 35, 30, 28],
            'ksat_r': [10.0, 5.0, 25.0, 15.0, 3.0],
            'sandtotal_r': [45.0, 25.0, 65.0, 40.0, 20.0],
            'claytotal_r': [25.0, 45.0, 15.0, 30.0, 50.0],
            'dbthirdbar_r': [1.4, 1.6, 1.3, 1.5, 1.7],
            'texcl': ['SL', 'CL', 'SL', 'L', 'C']
        }
    }

def mock_pysda_response():
    """Mock PySDA tabular response for testing."""
    class MockDataFrame:
        def __init__(self, data=None):
            self.data = data or {}
            self.empty = len(self.data) == 0
            
        def __getitem__(self, key):
            return self.data.get(key, [])
            
        def to_dict(self, orient='records'):
            if not self.data:
                return []
            keys = list(self.data.keys())
            records = []
            for i in range(len(self.data[keys[0]])):
                record = {key: self.data[key][i] for key in keys}
                records.append(record)
            return records
    
    mock_data = create_mock_ssurgo_data()
    return MockDataFrame(mock_data['chorizon'])

@pytest.fixture
def mock_qgis_environment():
    """Mock QGIS environment for testing."""
    with patch('qgis.core.QgsApplication') as mock_app, \
         patch('qgis.core.QgsProject') as mock_project, \
         patch('qgis.core.QgsVectorLayer') as mock_vector, \
         patch('qgis.core.QgsRasterLayer') as mock_raster:
        
        # Mock QgsApplication
        mock_app.instance.return_value = Mock()
        mock_app.instance().processingRegistry.return_value = Mock()
        
        # Mock QgsProject
        mock_project.instance.return_value = Mock()
        mock_project.instance().addMapLayer = Mock()
        
        yield {
            'app': mock_app,
            'project': mock_project,
            'vector_layer': mock_vector,
            'raster_layer': mock_raster
        }

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture  
def mock_algorithm_parameters():
    """Mock algorithm parameters for testing."""
    return {
        'AOI': create_mock_aoi_file(),
        'OUTPUT_DIR': '/tmp/test_output',
        'TEXTURE_METHOD': 'lookup',
        'LOAD_VECTOR': True,
        'LOAD_RASTERS': False
    }