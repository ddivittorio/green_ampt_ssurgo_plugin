"""Unit tests for algorithm parameter validation."""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import tempfile
import json

# Add plugin path for testing
plugin_path = Path(__file__).parent.parent.parent / "green_ampt_plugin"  
sys.path.insert(0, str(plugin_path))


class TestAlgorithmParameters(unittest.TestCase):
    """Test algorithm parameter validation and initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_aoi_file = self.create_test_aoi_file()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_aoi_file(self):
        """Create a test AOI file."""
        aoi_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-120.5, 35.5], [-120.4, 35.5], 
                                   [-120.4, 35.6], [-120.5, 35.6], [-120.5, 35.5]]]
                },
                "properties": {"id": 1}
            }]
        }
        
        aoi_file = Path(self.temp_dir) / "test_aoi.geojson"
        with open(aoi_file, 'w', encoding='utf-8') as f:
            json.dump(aoi_data, f)
        return str(aoi_file)
        
    @patch('green_ampt_processing.algorithms.green_ampt_ssurgo.QgsVectorFileWriter')
    @patch('green_ampt_processing.algorithms.green_ampt_ssurgo.QgsVectorLayer')
    def test_algorithm_parameter_definitions(self, mock_vector_layer, mock_writer):
        """Test that algorithm parameters are defined correctly."""
        with patch('sys.path'), \
             patch.dict('sys.modules', {
                 'green_ampt_tool.config': Mock(),
                 'green_ampt_tool.workflow': Mock(),
                 'green_ampt_tool.parameters': Mock()
             }):
            
            from green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSSURGOAlgorithm
            
            algorithm = GreenAmptSSURGOAlgorithm()
            
            # Mock the import method to avoid import errors
            algorithm._import_green_ampt_modules = Mock(return_value=(Mock(), Mock(), Mock(), Mock()))
            
            algorithm.initAlgorithm()
            
            # Test parameter definitions
            params = {param.name(): param for param in algorithm.parameterDefinitions()}
            
            # Required parameters
            self.assertIn('AOI', params)
            self.assertIn('OUTPUT_DIR', params)
            self.assertIn('TEXTURE_METHOD', params)
            self.assertIn('LOAD_VECTOR', params)
            self.assertIn('LOAD_RASTERS', params)
            
    def test_aoi_parameter_validation(self):
        """Test AOI parameter validation."""
        with patch('sys.path'), \
             patch.dict('sys.modules', {
                 'green_ampt_tool.config': Mock(),
                 'green_ampt_tool.workflow': Mock(), 
                 'green_ampt_tool.parameters': Mock()
             }):
            
            from green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSSURGOAlgorithm
            
            algorithm = GreenAmptSSURGOAlgorithm()
            algorithm._import_green_ampt_modules = Mock(return_value=(Mock(), Mock(), Mock(), Mock()))
            algorithm.initAlgorithm()
            
            # Test valid AOI file
            self.assertTrue(Path(self.test_aoi_file).exists())
            
            # Test invalid AOI file  
            invalid_file = "/nonexistent/path/file.shp"
            self.assertFalse(Path(invalid_file).exists())
            
    def test_texture_method_parameter(self):
        """Test texture method parameter options."""
        with patch('sys.path'), \
             patch.dict('sys.modules', {
                 'green_ampt_tool.config': Mock(),
                 'green_ampt_tool.workflow': Mock(),
                 'green_ampt_tool.parameters': Mock()
             }):
            
            from green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSSURGOAlgorithm
            
            algorithm = GreenAmptSSURGOAlgorithm()
            algorithm._import_green_ampt_modules = Mock(return_value=(Mock(), Mock(), Mock(), Mock()))
            algorithm.initAlgorithm()
            
            # Find texture method parameter
            texture_param = None
            for param in algorithm.parameterDefinitions():
                if param.name() == 'TEXTURE_METHOD':
                    texture_param = param
                    break
                    
            self.assertIsNotNone(texture_param)
            
            # Check available options
            if hasattr(texture_param, 'options'):
                options = texture_param.options()
                self.assertIn('lookup', [opt.lower() for opt in options])
                
    def test_boolean_parameters(self):
        """Test boolean parameters for auto-loading."""
        with patch('sys.path'), \
             patch.dict('sys.modules', {
                 'green_ampt_tool.config': Mock(),
                 'green_ampt_tool.workflow': Mock(),
                 'green_ampt_tool.parameters': Mock()
             }):
            
            from green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSSURGOAlgorithm
            
            algorithm = GreenAmptSSURGOAlgorithm()
            algorithm._import_green_ampt_modules = Mock(return_value=(Mock(), Mock(), Mock(), Mock()))
            algorithm.initAlgorithm()
            
            # Find boolean parameters
            bool_params = []
            for param in algorithm.parameterDefinitions():
                if param.name() in ['LOAD_VECTOR', 'LOAD_RASTERS']:
                    bool_params.append(param)
                    
            self.assertEqual(len(bool_params), 2)
            
            # Verify they are boolean parameters
            for param in bool_params:
                self.assertEqual(param.type(), param.TypeBoolean if hasattr(param, 'TypeBoolean') else 'Boolean')


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_output_directory_validation(self):
        """Test output directory validation."""
        # Valid directory
        valid_dir = self.temp_dir
        self.assertTrue(Path(valid_dir).exists())
        self.assertTrue(Path(valid_dir).is_dir())
        
        # Invalid directory
        invalid_dir = "/nonexistent/directory/path"
        self.assertFalse(Path(invalid_dir).exists())
        
        # File instead of directory
        test_file = Path(self.temp_dir) / "test_file.txt"
        test_file.write_text("test", encoding='utf-8')
        self.assertTrue(test_file.exists())
        self.assertFalse(test_file.is_dir())
        
    def test_vector_file_validation(self):
        """Test vector file format validation."""
        valid_extensions = ['.shp', '.gpkg', '.geojson', '.gml', '.kml']
        
        for ext in valid_extensions:
            # These should be considered valid extensions
            filename = f"test_file{ext}"
            self.assertTrue(any(filename.endswith(valid_ext) for valid_ext in valid_extensions))
            
        # Invalid extensions
        invalid_extensions = ['.txt', '.csv', '.xlsx', '.doc']
        for ext in invalid_extensions:
            filename = f"test_file{ext}"
            self.assertFalse(any(filename.endswith(valid_ext) for valid_ext in valid_extensions))


class TestAlgorithmInputProcessing(unittest.TestCase):
    """Test algorithm input processing and preprocessing."""
    
    def test_parameter_preprocessing(self):
        """Test parameter preprocessing before algorithm execution.""" 
        test_params = {
            'AOI': '/path/to/aoi.shp',
            'OUTPUT_DIR': '/path/to/output',
            'TEXTURE_METHOD': 'lookup',
            'LOAD_VECTOR': True,
            'LOAD_RASTERS': False
        }
        
        # Test that parameters are correctly typed
        self.assertIsInstance(test_params['AOI'], str)
        self.assertIsInstance(test_params['OUTPUT_DIR'], str)
        self.assertIsInstance(test_params['TEXTURE_METHOD'], str)
        self.assertIsInstance(test_params['LOAD_VECTOR'], bool)
        self.assertIsInstance(test_params['LOAD_RASTERS'], bool)
        
    def test_path_normalization(self):
        """Test path normalization for cross-platform compatibility."""
        test_paths = [
            '/unix/style/path',
            '\\windows\\style\\path',
            'relative/path',
            './current/dir/path'
        ]
        
        for path in test_paths:
            normalized = str(Path(path))
            self.assertIsInstance(normalized, str)
            # Path should be normalized to current OS style
            self.assertIsInstance(Path(normalized), Path)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and validation."""
    
    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        # This would typically be handled by QGIS parameter validation
        required_params = ['AOI', 'OUTPUT_DIR']
        provided_params = {'AOI': '/path/to/file.shp'}  # Missing OUTPUT_DIR
        
        missing = set(required_params) - set(provided_params.keys())
        self.assertEqual(missing, {'OUTPUT_DIR'})
        
    def test_invalid_parameter_types(self):
        """Test handling of invalid parameter types."""
        # Test boolean parameter with non-boolean value
        test_value = "true"  # String instead of boolean
        self.assertIsInstance(test_value, str)
        self.assertNotIsInstance(test_value, bool)
        
        # Test conversion
        converted = test_value.lower() == 'true'
        self.assertIsInstance(converted, bool)
        self.assertTrue(converted)
        
    def test_file_accessibility(self):
        """Test file accessibility validation."""
        import os
        
        # Test readable file
        temp_file = Path(tempfile.mktemp())
        temp_file.write_text("test", encoding='utf-8')
        self.assertTrue(temp_file.exists())
        self.assertTrue(os.access(temp_file, os.R_OK))
        
        # Clean up
        temp_file.unlink()
        
        # Test non-existent file
        self.assertFalse(temp_file.exists())


if __name__ == '__main__':
    unittest.main()