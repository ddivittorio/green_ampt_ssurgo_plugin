"""
Specific test to identify and document the auto-loading issue.

This test analyzes the current algorithm implementation to identify
why the vector auto-loading toggle is not working.
"""

import unittest
from pathlib import Path
import re


class TestAutoLoadingIssueAnalysis(unittest.TestCase):
    """Analyze the auto-loading implementation to identify issues."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.algorithm_file = Path(__file__).parent.parent.parent / "green_ampt_plugin" / "green_ampt_processing" / "algorithms" / "green_ampt_ssurgo.py"
        
    def test_algorithm_file_exists(self):
        """Verify the algorithm file exists."""
        self.assertTrue(self.algorithm_file.exists(), "Algorithm file should exist")
        
    def test_analyze_load_output_layers_method(self):
        """Analyze the _load_output_layers method implementation."""
        if not self.algorithm_file.exists():
            self.skipTest("Algorithm file not found")
            
        content = self.algorithm_file.read_text(encoding='utf-8')
        
        # Check if method exists
        method_exists = '_load_output_layers' in content
        self.assertTrue(method_exists, "_load_output_layers method should exist")
        
        if method_exists:
            # Extract the method content
            method_pattern = r'def _load_output_layers\(self.*?\n(.*?)(?=\n    def|\n\n|\Z)'
            method_match = re.search(method_pattern, content, re.DOTALL)
            
            if method_match:
                method_content = method_match.group(1)
                print(f"\\n_load_output_layers method content:\\n{method_content}")
                
                # Check for implementation issues
                issues = []
                
                # Check if it actually loads vector layers
                if 'QgsVectorLayer' not in method_content:
                    issues.append("QgsVectorLayer not used - vector loading not implemented")
                    
                # Check if it adds to project
                if 'QgsProject.instance().addMapLayer' not in method_content:
                    issues.append("Layers not added to project")
                    
                # Check parameter handling
                if 'LOAD_VECTOR' not in method_content and 'load_vector' not in method_content:
                    issues.append("LOAD_VECTOR parameter not handled")
                    
                if issues:
                    print(f"\\nIssues identified: {issues}")
                    self.fail(f"Auto-loading issues found: {'; '.join(issues)}")
                else:
                    print("\\nNo obvious issues found in _load_output_layers method")
            else:
                self.fail("Could not extract _load_output_layers method content")
                
    def test_check_method_call_in_process_algorithm(self):
        """Check if _load_output_layers is called in processAlgorithm."""
        if not self.algorithm_file.exists():
            self.skipTest("Algorithm file not found")
            
        content = self.algorithm_file.read_text(encoding='utf-8')
        
        # Find processAlgorithm method
        process_pattern = r'def processAlgorithm\(self.*?\n(.*?)(?=\n    def|\Z)'
        process_match = re.search(process_pattern, content, re.DOTALL)
        
        if process_match:
            process_content = process_match.group(1)
            
            # Check if _load_output_layers is called
            if '_load_output_layers' in process_content:
                print("\\n✓ _load_output_layers is called in processAlgorithm")
                
                # Check if it's called after output generation
                lines = process_content.split('\\n')
                load_line = None
                output_line = None
                
                for i, line in enumerate(lines):
                    if '_load_output_layers' in line:
                        load_line = i
                    if 'OUTPUT_VECTOR' in line and 'output_vector' in line:
                        output_line = i
                        
                if load_line is not None and output_line is not None:
                    if load_line > output_line:
                        print("✓ _load_output_layers called after output generation")
                    else:
                        print("⚠ _load_output_layers called before output generation")
                        
            else:
                self.fail("_load_output_layers is NOT called in processAlgorithm - this is the issue!")
        else:
            self.fail("Could not find processAlgorithm method")
            
    def test_parameter_retrieval(self):
        """Test how parameters are retrieved in the algorithm."""
        if not self.algorithm_file.exists():
            self.skipTest("Algorithm file not found")
            
        content = self.algorithm_file.read_text(encoding='utf-8')
        
        # Check parameter retrieval patterns
        load_vector_pattern = r'parameters\[.*[\'"]LOAD_VECTOR[\'"].*\]'
        load_rasters_pattern = r'parameters\[.*[\'"]LOAD_RASTERS[\'"].*\]'
        
        load_vector_found = re.search(load_vector_pattern, content)
        load_rasters_found = re.search(load_rasters_pattern, content)
        
        if load_vector_found:
            print(f"\\n✓ LOAD_VECTOR parameter retrieved: {load_vector_found.group()}")
        else:
            print("\\n⚠ LOAD_VECTOR parameter not properly retrieved")
            
        if load_rasters_found:
            print(f"✓ LOAD_RASTERS parameter retrieved: {load_rasters_found.group()}")
        else:
            print("⚠ LOAD_RASTERS parameter not properly retrieved")
            
    def test_identify_specific_auto_loading_bug(self):
        """Identify the specific bug preventing auto-loading from working."""
        if not self.algorithm_file.exists():
            self.skipTest("Algorithm file not found")
            
        content = self.algorithm_file.read_text(encoding='utf-8')
        
        print("\\n" + "="*60)
        print("AUTO-LOADING BUG ANALYSIS")
        print("="*60)
        
        # Check 1: Method exists
        method_exists = '_load_output_layers' in content
        print(f"1. _load_output_layers method exists: {method_exists}")
        
        # Check 2: Method is called
        method_called = 'self._load_output_layers' in content
        print(f"2. _load_output_layers method called: {method_called}")
        
        # Check 3: Parameters retrieved
        load_vector_retrieved = 'LOAD_VECTOR' in content and 'parameters[' in content
        print(f"3. LOAD_VECTOR parameter retrieved: {load_vector_retrieved}")
        
        # Check 4: Vector layer creation
        vector_layer_creation = 'QgsVectorLayer' in content
        print(f"4. QgsVectorLayer used: {vector_layer_creation}")
        
        # Check 5: Project addition
        project_addition = 'QgsProject.instance().addMapLayer' in content
        print(f"5. addMapLayer called: {project_addition}")
        
        # Summary
        print("\\n" + "-"*60)
        print("LIKELY ISSUES:")
        
        if not method_called:
            print("• CRITICAL: _load_output_layers method is defined but NOT CALLED")
            print("  → This is likely the main bug!")
            
        if not vector_layer_creation:
            print("• Vector layer creation not implemented in _load_output_layers")
            
        if not project_addition:
            print("• Layer addition to project not implemented")
            
        print("\\n" + "="*60)
        
        # This test passes but documents the issues
        self.assertTrue(True, "Analysis complete - see output for issues")


if __name__ == '__main__':
    # Run with high verbosity to see all output
    unittest.main(verbosity=2, buffer=False)