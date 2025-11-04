"""Create test data for Green-Ampt plugin testing."""

import json
from pathlib import Path

def create_test_fixtures():
    """Create test fixture data files."""
    fixtures_dir = Path(__file__).parent
    
    # Create test AOI files
    create_test_aoi_files(fixtures_dir)
    
    # Create mock SSURGO data
    create_mock_ssurgo_data(fixtures_dir)
    
    # Create expected output files
    create_expected_outputs(fixtures_dir)

def create_test_aoi_files(fixtures_dir):
    """Create test AOI files in various formats.""" 
    aoi_dir = fixtures_dir / "aoi_files"
    aoi_dir.mkdir(exist_ok=True)
    
    # Small test AOI (Dallas, TX area)
    small_aoi = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-97.1, 32.7], [-97.0, 32.7],
                    [-97.0, 32.8], [-97.1, 32.8], [-97.1, 32.7]
                ]]
            },
            "properties": {"id": 1, "name": "Small Test AOI", "area_ha": 100}
        }]
    }
    
    # Medium test AOI (larger area)
    medium_aoi = {
        "type": "FeatureCollection", 
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-97.2, 32.6], [-96.8, 32.6],
                    [-96.8, 33.0], [-97.2, 33.0], [-97.2, 32.6]
                ]]
            },
            "properties": {"id": 1, "name": "Medium Test AOI", "area_ha": 1000}
        }]
    }
    
    # Save AOI files
    with open(aoi_dir / "small_aoi.geojson", 'w', encoding='utf-8') as f:
        json.dump(small_aoi, f, indent=2)
        
    with open(aoi_dir / "medium_aoi.geojson", 'w', encoding='utf-8') as f:
        json.dump(medium_aoi, f, indent=2)

def create_mock_ssurgo_data(fixtures_dir):
    """Create mock SSURGO data for testing."""
    data_dir = fixtures_dir / "test_data"
    data_dir.mkdir(exist_ok=True)
    
    # Mock map unit polygon data
    mupolygon_data = [
        {"mukey": "123456", "musym": "ABC", "muname": "Test Soil A", "area_sqm": 10000},
        {"mukey": "789012", "musym": "DEF", "muname": "Test Soil B", "area_sqm": 15000},
        {"mukey": "345678", "musym": "GHI", "muname": "Test Soil C", "area_sqm": 8000}
    ]
    
    # Mock component data
    component_data = [
        {"mukey": "123456", "cokey": "111", "comppct_r": 85, "hydgrp": "B", "majcompflag": "Yes"},
        {"mukey": "123456", "cokey": "112", "comppct_r": 15, "hydgrp": "C", "majcompflag": "No"},
        {"mukey": "789012", "cokey": "221", "comppct_r": 70, "hydgrp": "A", "majcompflag": "Yes"},
        {"mukey": "789012", "cokey": "222", "comppct_r": 30, "hydgrp": "B", "majcompflag": "No"},
        {"mukey": "345678", "cokey": "331", "comppct_r": 90, "hydgrp": "C", "majcompflag": "Yes"}
    ]
    
    # Mock chorizon data
    chorizon_data = [
        {"cokey": "111", "hzdept_r": 0, "hzdepb_r": 30, "ksat_r": 10.0, 
         "sandtotal_r": 45.0, "claytotal_r": 25.0, "dbthirdbar_r": 1.4, "texcl": "SL"},
        {"cokey": "112", "hzdept_r": 0, "hzdepb_r": 25, "ksat_r": 5.0,
         "sandtotal_r": 25.0, "claytotal_r": 45.0, "dbthirdbar_r": 1.6, "texcl": "CL"},
        {"cokey": "221", "hzdept_r": 0, "hzdepb_r": 35, "ksat_r": 25.0,
         "sandtotal_r": 65.0, "claytotal_r": 15.0, "dbthirdbar_r": 1.3, "texcl": "SL"},
        {"cokey": "222", "hzdept_r": 0, "hzdepb_r": 30, "ksat_r": 15.0,
         "sandtotal_r": 40.0, "claytotal_r": 30.0, "dbthirdbar_r": 1.5, "texcl": "L"},
        {"cokey": "331", "hzdept_r": 0, "hzdepb_r": 28, "ksat_r": 3.0,
         "sandtotal_r": 20.0, "claytotal_r": 50.0, "dbthirdbar_r": 1.7, "texcl": "C"}
    ]
    
    # Save mock data files
    with open(data_dir / "mock_mupolygon.json", 'w', encoding='utf-8') as f:
        json.dump(mupolygon_data, f, indent=2)
        
    with open(data_dir / "mock_component.json", 'w', encoding='utf-8') as f:
        json.dump(component_data, f, indent=2)
        
    with open(data_dir / "mock_chorizon.json", 'w', encoding='utf-8') as f:
        json.dump(chorizon_data, f, indent=2)

def create_expected_outputs(fixtures_dir):
    """Create expected output files for testing."""
    outputs_dir = fixtures_dir / "expected_outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # Expected Green-Ampt parameters
    expected_parameters = [
        {
            "mukey": "123456",
            "ks": 8.5,          # mm/hr
            "theta_s": 0.45,    # saturated water content
            "theta_r": 0.08,    # residual water content
            "alpha": 0.012,     # van Genuchten alpha
            "n": 1.8,           # van Genuchten n
            "psi": 120.0,       # wetting front suction head (mm)
            "texture": "SL"
        },
        {
            "mukey": "789012",
            "ks": 20.0,
            "theta_s": 0.40,
            "theta_r": 0.06,
            "alpha": 0.025,
            "n": 2.2,
            "psi": 85.0,
            "texture": "SL"
        },
        {
            "mukey": "345678",
            "ks": 2.8,
            "theta_s": 0.55,
            "theta_r": 0.12,
            "alpha": 0.008,
            "n": 1.4,
            "psi": 280.0,
            "texture": "C"
        }
    ]
    
    # Expected summary report content
    expected_summary = """Green-Ampt Parameter Summary
===========================
Generated by: Green-Ampt Parameter Generator QGIS Plugin
Date: Test Date

Input Information:
- AOI File: test_aoi.geojson
- Area: 1000 hectares
- Texture Method: lookup

Results Summary:
- Total Map Units: 3
- Average Hydraulic Conductivity: 10.4 mm/hr
- Dominant Texture Class: Sandy Loam (SL)
- Hydrologic Soil Groups: A (33%), B (33%), C (33%)

Output Files Generated:
- green_ampt_parameters.shp (vector)
- ks.tif (hydraulic conductivity raster)
- theta_s.tif (saturated water content raster)
- psi.tif (wetting front suction head raster)
"""
    
    # Save expected outputs
    with open(outputs_dir / "expected_parameters.json", 'w', encoding='utf-8') as f:
        json.dump(expected_parameters, f, indent=2)
        
    with open(outputs_dir / "expected_summary.txt", 'w', encoding='utf-8') as f:
        f.write(expected_summary)

if __name__ == '__main__':
    create_test_fixtures()
    print("Test fixtures created successfully!")