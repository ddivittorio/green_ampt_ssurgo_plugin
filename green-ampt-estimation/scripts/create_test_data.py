#!/usr/bin/env python
"""
Create synthetic SSURGO test data for testing without network access.
This creates minimal valid SSURGO datasets that match the schema expected by the tool.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import box

def create_synthetic_ssurgo_data(output_dir: Path):
    """Create synthetic SSURGO data for testing"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the test AOI to get bounds
    test_aoi = gpd.read_file('test_aoi/test_aoi.shp')
    test_aoi_wgs84 = test_aoi.to_crs('EPSG:4326')
    bounds = test_aoi_wgs84.total_bounds  # minx, miny, maxx, maxy
    
    # Create synthetic mupolygon (spatial data)
    # Create two map units covering the AOI
    minx, miny, maxx, maxy = bounds
    midx = (minx + maxx) / 2
    
    geometries = [
        box(minx, miny, midx, maxy),  # Left half
        box(midx, miny, maxx, maxy),  # Right half
    ]
    
    mupolygon_data = {
        'mukey': ['1001', '1002'],
        'geometry': geometries
    }
    
    mupolygon = gpd.GeoDataFrame(mupolygon_data, crs='EPSG:4326')
    mupolygon.to_file(output_dir / 'mupolygon_raw.shp')
    print(f"✓ Created {output_dir / 'mupolygon_raw.shp'}")
    
    # Create synthetic mapunit (tabular data)
    mapunit_data = {
        'mukey': ['1001', '1002'],
        'musym': ['TestMU1', 'TestMU2'],
        'muname': ['Test Map Unit 1', 'Test Map Unit 2'],
    }
    mapunit = pd.DataFrame(mapunit_data)
    mapunit.to_csv(output_dir / 'mapunit_raw.txt', index=False, sep='|')
    print(f"✓ Created {output_dir / 'mapunit_raw.txt'}")
    
    # Create synthetic component (soil components)
    # Each map unit has 1-2 components
    component_data = {
        'mukey': ['1001', '1002', '1002'],
        'cokey': ['2001', '2002', '2003'],
        'compname': ['Sandy loam', 'Clay loam', 'Silt loam'],
        'comppct_r': [100, 60, 40],  # Component percentage
        'hydgrp': ['B', 'C', 'B'],  # Hydrologic soil group
        'texcl': ['Sandy Loam', 'Clay Loam', 'Silt Loam'],  # Texture class (full names for lookup)
    }
    component = pd.DataFrame(component_data)
    component.to_csv(output_dir / 'component_raw.txt', index=False, sep='|')
    print(f"✓ Created {output_dir / 'component_raw.txt'}")
    
    # Create synthetic chorizon (soil horizons with properties)
    # Each component has 2-3 horizons
    chorizon_data = {
        'cokey': ['2001', '2001', '2002', '2002', '2003', '2003'],
        'chkey': ['3001', '3002', '3003', '3004', '3005', '3006'],
        'hzname': ['A', 'Bw', 'Ap', 'Bt', 'A', 'Bw'],
        'hzdept_r': [0, 15, 0, 20, 0, 10],  # Top depth (cm)
        'hzdepb_r': [15, 50, 20, 60, 10, 40],  # Bottom depth (cm)
        'sandtotal_r': [65.0, 60.0, 25.0, 20.0, 35.0, 30.0],  # Sand %
        'silttotal_r': [25.0, 28.0, 45.0, 42.0, 55.0, 52.0],  # Silt %
        'claytotal_r': [10.0, 12.0, 30.0, 38.0, 10.0, 18.0],  # Clay %
        'texcl': ['Sandy Loam', 'Sandy Loam', 'Clay Loam', 'Clay Loam', 'Silt Loam', 'Silt Loam'],  # Texture class (full names)
        'ksat_r': [28.0, 14.0, 4.0, 1.5, 14.0, 9.0],  # Saturated hydraulic conductivity (µm/s)
        'dbthirdbar_r': [1.45, 1.55, 1.35, 1.40, 1.40, 1.50],  # Bulk density (g/cm³)
        'wthirdbar_r': [0.15, 0.18, 0.28, 0.32, 0.20, 0.24],  # Water content at 33 kPa
        'wfifteenbar_r': [0.08, 0.10, 0.18, 0.22, 0.12, 0.15],  # Water content at 1500 kPa
    }
    chorizon = pd.DataFrame(chorizon_data)
    chorizon.to_csv(output_dir / 'chorizon_raw.txt', index=False, sep='|')
    print(f"✓ Created {output_dir / 'chorizon_raw.txt'}")
    
    print(f"\n✓ Synthetic SSURGO test data created in {output_dir}")
    return output_dir


if __name__ == '__main__':
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else 'outputs/test_ssurgo_data'
    create_synthetic_ssurgo_data(output_dir)
