"""Unit tests for Green-Ampt plugin loading and initialization."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add plugin path to sys.path for testing
plugin_path = Path(__file__).parent.parent.parent / "green_ampt_plugin"
sys.path.insert(0, str(plugin_path))


class TestPluginInitialization(unittest.TestCase):
    """Test plugin loading and initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_iface = Mock()
        self.mock_iface.addPluginToMenu = Mock()
        self.mock_iface.removePluginMenu = Mock()
        
    @patch('green_ampt_plugin.QIcon')
    @patch('green_ampt_plugin.QAction') 
    def test_plugin_init(self, mock_action, mock_icon):
        """Test plugin initialization."""
        from green_ampt_plugin import GreenAmptPlugin
        
        plugin = GreenAmptPlugin(self.mock_iface)
        
        self.assertEqual(plugin.iface, self.mock_iface)
        self.assertIsNotNone(plugin.plugin_dir)
        
    @patch('green_ampt_plugin.QgsApplication')
    def test_plugin_initProcessing(self, mock_qgs_app):
        """Test processing initialization."""
        from green_ampt_plugin import GreenAmptPlugin
        
        # Mock processing registry
        mock_registry = Mock()
        mock_qgs_app.processingRegistry.return_value = mock_registry
        
        plugin = GreenAmptPlugin(self.mock_iface)
        plugin.initProcessing()
        
        # Verify provider was added
        mock_registry.addProvider.assert_called_once()
        
    def test_plugin_initGui(self):
        """Test GUI initialization."""
        from green_ampt_plugin import GreenAmptPlugin
        
        with patch('green_ampt_plugin.QAction') as mock_action, \
             patch('green_ampt_plugin.QIcon') as mock_icon:
            
            plugin = GreenAmptPlugin(self.mock_iface)
            plugin.initGui()
            
            # Verify menu action was created and added
            mock_action.assert_called()
            self.mock_iface.addPluginToMenu.assert_called()
            
    def test_plugin_unload(self):
        """Test plugin unloading."""
        from green_ampt_plugin import GreenAmptPlugin
        
        with patch('green_ampt_plugin.QgsApplication') as mock_qgs_app:
            mock_registry = Mock()
            mock_qgs_app.processingRegistry.return_value = mock_registry
            
            plugin = GreenAmptPlugin(self.mock_iface)
            plugin.initProcessing()
            plugin.initGui()
            plugin.unload()
            
            # Verify cleanup
            mock_registry.removeProvider.assert_called_once()
            self.mock_iface.removePluginMenu.assert_called()


class TestProcessingProvider(unittest.TestCase):
    """Test the processing provider registration."""
    
    @patch('green_ampt_processing.green_ampt_provider.QIcon')
    def test_provider_init(self, mock_icon):
        """Test provider initialization."""
        from green_ampt_processing.green_ampt_provider import GreenAmptProvider
        
        provider = GreenAmptProvider()
        
        self.assertEqual(provider.id(), 'green_ampt')
        self.assertEqual(provider.name(), 'Green-Ampt Parameter Generator')
        self.assertIsInstance(provider.longName(), str)
        
    def test_provider_loadAlgorithms(self):
        """Test algorithm loading."""
        from green_ampt_processing.green_ampt_provider import GreenAmptProvider
        
        provider = GreenAmptProvider()
        provider.loadAlgorithms()
        
        # Verify algorithms were loaded
        algorithms = provider.algorithms
        self.assertGreater(len(algorithms), 0)
        
        # Check for SSURGO algorithm
        algorithm_names = [alg.name() for alg in algorithms]
        self.assertIn('Green-Ampt Parameters from SSURGO', algorithm_names)


class TestAlgorithmRegistration(unittest.TestCase):
    """Test algorithm registration and availability."""
    
    def setUp(self):
        """Set up algorithm for testing.""" 
        from green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSSURGOAlgorithm
        self.algorithm = GreenAmptSSURGOAlgorithm()
        
    def test_algorithm_metadata(self):
        """Test algorithm metadata."""
        self.assertEqual(self.algorithm.name(), 'Green-Ampt Parameters from SSURGO')
        self.assertEqual(self.algorithm.displayName(), 'Green-Ampt Parameters from SSURGO')
        self.assertEqual(self.algorithm.group(), 'Green-Ampt Tools')
        self.assertEqual(self.algorithm.groupId(), 'green_ampt_tools')
        
    def test_algorithm_parameters(self):
        """Test algorithm parameter definitions."""
        with patch.object(self.algorithm, '_import_green_ampt_modules', return_value=(Mock(), Mock(), Mock(), Mock())):
            params = self.algorithm.initAlgorithm()
            
            # Should not return anything (initAlgorithm returns None)
            self.assertIsNone(params)
            
            # Check that parameters were added to parameterDefinitions
            param_names = [param.name() for param in self.algorithm.parameterDefinitions()]
            
            expected_params = ['AOI', 'OUTPUT_DIR', 'TEXTURE_METHOD', 'LOAD_VECTOR', 'LOAD_RASTERS']
            for param in expected_params:
                self.assertIn(param, param_names)
                
    def test_algorithm_outputs(self):
        """Test algorithm output definitions.""" 
        with patch.object(self.algorithm, '_import_green_ampt_modules', return_value=(Mock(), Mock(), Mock(), Mock())):
            self.algorithm.initAlgorithm()
            
            output_names = [output.name() for output in self.algorithm.outputDefinitions()]
            
            expected_outputs = ['OUTPUT_VECTOR', 'SUMMARY_REPORT']
            for output in expected_outputs:
                self.assertIn(output, output_names)


if __name__ == '__main__':
    unittest.main()