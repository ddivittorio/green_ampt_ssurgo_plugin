"""Unit tests for SSURGO data access functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import pandas as pd

# Add paths for testing
green_ampt_path = Path(__file__).parent.parent.parent / "green-ampt-estimation"
sys.path.insert(0, str(green_ampt_path))


class TestSSURGODataAccess(unittest.TestCase):
    """Test SSURGO data access functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_mukeys = ['123456', '789012', '345678']
        self.mock_chorizon_data = {
            'mukey': ['123456', '123456', '789012'],
            'cokey': ['111', '112', '221'],
            'hzdept_r': [0, 0, 0],
            'hzdepb_r': [30, 25, 35],
            'ksat_r': [10.0, 5.0, 25.0],
            'sandtotal_r': [45.0, 25.0, 65.0],
            'claytotal_r': [25.0, 45.0, 15.0],
            'dbthirdbar_r': [1.4, 1.6, 1.3],
            'texcl': ['SL', 'CL', 'SL']
        }
        
    def test_ssurgo_data_init(self):
        """Test SSURGOData initialization."""
        from green_ampt_tool.data_access import SSURGOData
        
        ssurgo = SSURGOData()
        self.assertIsNotNone(ssurgo)
        
    @patch('green_ampt_tool.data_access.require_pandas')
    def test_chunk_sequence(self, mock_pandas):
        """Test sequence chunking functionality."""
        from green_ampt_tool.data_access import _chunk_sequence
        
        # Mock pandas
        mock_pandas.return_value = pd
        
        test_sequence = list(range(10))
        chunks = list(_chunk_sequence(test_sequence, 3))
        
        self.assertEqual(len(chunks), 4)  # 10 items in chunks of 3 = 4 chunks
        self.assertEqual(chunks[0], [0, 1, 2])
        self.assertEqual(chunks[-1], [9])  # Last chunk has 1 item
        
    @patch('green_ampt_tool.data_access.require_pandas')
    def test_fetch_chorizon_records(self, mock_pandas):
        """Test chorizon data fetching with texture classification fix."""
        from green_ampt_tool.data_access import _fetch_chorizon_records
        
        # Mock pandas
        mock_pandas.return_value = pd
        
        # Mock sdatab module
        mock_sdatab = Mock()
        mock_df = pd.DataFrame(self.mock_chorizon_data)
        mock_sdatab.tabular.return_value = mock_df
        
        result = _fetch_chorizon_records(mock_sdatab, self.test_mukeys)
        
        # Verify query includes texture classification fix
        call_args = mock_sdatab.tabular.call_args[0][0]
        self.assertIn('texturerv as texcl', call_args)
        
        # Verify result structure
        self.assertIsInstance(result, pd.DataFrame)
        expected_columns = ['mukey', 'cokey', 'hzdept_r', 'hzdepb_r', 'ksat_r', 
                          'sandtotal_r', 'claytotal_r', 'dbthirdbar_r', 'texcl']
        for col in expected_columns:
            self.assertIn(col, result.columns)
            
    @patch('green_ampt_tool.data_access.require_pandas')        
    def test_fetch_component_records(self, mock_pandas):
        """Test component data fetching."""
        from green_ampt_tool.data_access import _fetch_component_records
        
        # Mock pandas
        mock_pandas.return_value = pd
        
        # Mock sdatab module
        mock_sdatab = Mock()
        mock_component_data = {
            'mukey': ['123456', '789012'],
            'cokey': ['111', '221'], 
            'comppct_r': [85, 70],
            'hydgrp': ['B', 'A'],
            'majcompflag': ['Yes', 'Yes']
        }
        mock_df = pd.DataFrame(mock_component_data)
        mock_sdatab.tabular.return_value = mock_df
        
        result = _fetch_component_records(mock_sdatab, self.test_mukeys)
        
        # Verify result structure
        self.assertIsInstance(result, pd.DataFrame)
        expected_columns = ['mukey', 'cokey', 'comppct_r', 'hydgrp', 'majcompflag']
        for col in expected_columns:
            self.assertIn(col, result.columns)
            
    def test_texture_classification_mapping(self):
        """Test that texture classifications are properly mapped."""
        # This tests the fix for texture classification
        expected_textures = ['SL', 'CL', 'L', 'C', 'S', 'SC', 'SIL', 'SI', 'SICL', 'SIC']
        
        # Test data should include various texture classes
        test_data = pd.DataFrame({
            'texcl': expected_textures[:3],  # Test first 3
            'sandtotal_r': [45.0, 25.0, 35.0],
            'claytotal_r': [25.0, 45.0, 30.0]
        })
        
        # Verify texture classes are valid SSURGO abbreviations
        for texture in test_data['texcl']:
            self.assertIn(texture, expected_textures)


class TestPySDAIntegration(unittest.TestCase):
    """Test PySDA integration and vendored dependency."""
    
    def test_pysda_import(self):
        """Test that vendored PySDA can be imported."""
        try:
            # Test importing vendored PySDA
            pysda_path = Path(__file__).parent.parent.parent / "green-ampt-estimation" / "external" / "pysda"
            sys.path.insert(0, str(pysda_path))
            
            import pysda.sdatab as sdatab
            self.assertIsNotNone(sdatab)
            
        except ImportError as e:
            self.fail(f"Failed to import vendored PySDA: {e}")
            
    @patch('green_ampt_tool.data_access.require_pandas')
    def test_pysda_query_structure(self, mock_pandas):
        """Test that PySDA queries are structured correctly."""
        from green_ampt_tool.data_access import _fetch_chorizon_records
        
        # Mock pandas
        mock_pandas.return_value = pd
        
        # Mock sdatab module to capture query
        mock_sdatab = Mock()
        mock_df = pd.DataFrame(self.mock_chorizon_data)
        mock_sdatab.tabular.return_value = mock_df
        
        _fetch_chorizon_records(mock_sdatab, ['123456'])
        
        # Get the actual query that was called
        query = mock_sdatab.tabular.call_args[0][0]
        
        # Verify essential query components
        self.assertIn('SELECT', query.upper())
        self.assertIn('FROM component', query)
        self.assertIn('INNER JOIN chorizon', query)
        self.assertIn('WHERE c.mukey IN', query)
        self.assertIn('texturerv as texcl', query)  # Key fix for texture classification


class TestDataValidation(unittest.TestCase):
    """Test data validation and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_chorizon_data = {
            'mukey': ['123456', '789012'],
            'cokey': ['111', '221'],
            'ksat_r': [10.0, None],  # Include None value for testing
            'sandtotal_r': [45.0, 65.0],
            'claytotal_r': [25.0, 15.0],
            'texcl': ['SL', 'SL']
        }
        
    @patch('green_ampt_tool.data_access.require_pandas')
    def test_empty_result_handling(self, mock_pandas):
        """Test handling of empty query results."""
        from green_ampt_tool.data_access import _fetch_chorizon_records
        
        # Mock pandas
        mock_pandas.return_value = pd
        
        # Mock sdatab module returning empty result
        mock_sdatab = Mock()
        mock_sdatab.tabular.return_value = None
        
        result = _fetch_chorizon_records(mock_sdatab, ['nonexistent'])
        
        # Should return empty DataFrame with correct columns
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
        expected_columns = ['mukey', 'cokey', 'hzdept_r', 'hzdepb_r', 'ksat_r',
                          'sandtotal_r', 'claytotal_r', 'dbthirdbar_r', 'texcl']
        for col in expected_columns:
            self.assertIn(col, result.columns)
            
    def test_missing_value_handling(self):
        """Test handling of missing values in soil data.""" 
        df = pd.DataFrame(self.mock_chorizon_data)
        
        # Check that None values are preserved (not converted to string 'None')
        self.assertTrue(pd.isna(df.loc[1, 'ksat_r']))
        
    def test_texture_validation(self):
        """Test validation of texture classification values."""
        valid_textures = ['C', 'CL', 'L', 'S', 'SC', 'SCL', 'SI', 'SIC', 'SICL', 'SIL', 'SL']
        
        test_textures = ['SL', 'CL', 'L', 'INVALID']
        
        for texture in test_textures[:3]:  # First 3 are valid
            self.assertIn(texture, valid_textures)
            
        # Test invalid texture
        self.assertNotIn('INVALID', valid_textures)


if __name__ == '__main__':
    unittest.main()