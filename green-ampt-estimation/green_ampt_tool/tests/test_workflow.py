"""
Tests for workflow.py module.

These tests verify the pipeline orchestration functions work correctly.
"""

import sys
from pathlib import Path
import tempfile

import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.workflow import _prepare_green_ampt_vector
from green_ampt_tool.data_access import SSURGOData
from green_ampt_tool.config import PipelineConfig


class TestPrepareGreenAmptVector:
    """Test the _prepare_green_ampt_vector function."""
    
    @pytest.fixture
    def sample_aoi(self):
        """Create a sample AOI GeoDataFrame."""
        polygon = Polygon([(-120, 40), (-120, 41), (-119, 41), (-119, 40)])
        return gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[polygon],
            crs="EPSG:4326"
        )
    
    @pytest.fixture
    def sample_ssurgo(self):
        """Create sample SSURGO data."""
        # Create mupolygon
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1", "2"], "musym": ["A", "B"]},
            geometry=[
                Polygon([(-120, 40), (-120, 40.5), (-119.5, 40.5), (-119.5, 40)]),
                Polygon([(-119.5, 40), (-119.5, 40.5), (-119, 40.5), (-119, 40)]),
            ],
            crs="EPSG:4326"
        )
        
        # Create component
        component = pd.DataFrame({
            "mukey": ["1", "2"],
            "cokey": ["10", "20"],
            "comppct_r": [100, 100],
            "hydgrp": ["A", "B"],
            "majcompflag": ["Yes", "Yes"],
        })
        
        # Create chorizon
        chorizon = pd.DataFrame({
            "cokey": ["10", "20"],
            "chkey": ["100", "200"],
            "texcl": ["Sand", "Loam"],
            "hzdept_r": [0, 0],
            "hzdepb_r": [10, 10],
            "sandtotal_r": [90, 40],
            "claytotal_r": [5, 20],
        })
        
        # Create mapunit
        mapunit = pd.DataFrame({
            "mukey": ["1", "2"],
            "muname": ["Test Soil 1", "Test Soil 2"],
        })
        
        return SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon
        )
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample pipeline config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aoi_file = Path(tmpdir) / "test_aoi.gpkg"
            polygon = Polygon([(-120, 40), (-120, 41), (-119, 41), (-119, 40)])
            aoi = gpd.GeoDataFrame(
                {"id": [1]},
                geometry=[polygon],
                crs="EPSG:4326"
            )
            aoi.to_file(aoi_file, driver="GPKG")
            
            config = PipelineConfig(
                aoi_path=aoi_file,
                output_dir=Path(tmpdir),
                data_source="pysda",  # Use pysda instead of local
            )
            yield config
    
    def test_prepare_with_lookup_table(self, sample_aoi, sample_ssurgo, sample_config):
        """Test vector preparation with lookup table method."""
        sample_config.use_lookup_table = True
        sample_config.use_hsg_lookup = False
        
        result = _prepare_green_ampt_vector(sample_aoi, sample_ssurgo, sample_config)
        
        assert not result.empty
        assert "Ks_inhr" in result.columns
        assert "psi_in" in result.columns
        assert "theta_s" in result.columns
        assert isinstance(result, gpd.GeoDataFrame)
    
    def test_prepare_with_hsg_lookup(self, sample_aoi, sample_ssurgo, sample_config):
        """Test vector preparation with HSG lookup method."""
        sample_config.use_lookup_table = False
        sample_config.use_hsg_lookup = True
        
        result = _prepare_green_ampt_vector(sample_aoi, sample_ssurgo, sample_config)
        
        assert not result.empty
        assert "Ks_inhr" in result.columns
        assert "hsg_dom" in result.columns
        assert isinstance(result, gpd.GeoDataFrame)
    
    def test_prepare_with_pedotransfer(self, sample_aoi, sample_ssurgo, sample_config):
        """Test vector preparation with pedotransfer method."""
        sample_config.use_lookup_table = False
        sample_config.use_hsg_lookup = False
        
        result = _prepare_green_ampt_vector(sample_aoi, sample_ssurgo, sample_config)
        
        assert not result.empty
        assert "ksat" in result.columns
        assert "sand_pct" in result.columns
        assert isinstance(result, gpd.GeoDataFrame)
    
    def test_prepare_with_custom_depth_limit(self, sample_aoi, sample_ssurgo, sample_config):
        """Test vector preparation with custom depth limit."""
        sample_config.use_lookup_table = True
        sample_config.depth_limit_cm = 5.0
        
        result = _prepare_green_ampt_vector(sample_aoi, sample_ssurgo, sample_config)
        
        assert not result.empty
        assert isinstance(result, gpd.GeoDataFrame)
    
    def test_prepare_empty_aggregation_raises_error(self, sample_aoi, sample_config):
        """Test that empty aggregated data raises an error."""
        # Create SSURGO data with no overlapping components
        empty_ssurgo = SSURGOData(
            mupolygon=sample_aoi.copy(),
            mapunit=pd.DataFrame({"mukey": [], "muname": []}),
            component=pd.DataFrame(),
            chorizon=pd.DataFrame()
        )
        
        sample_config.use_lookup_table = True
        
        with pytest.raises(RuntimeError, match="No soil properties could be derived"):
            _prepare_green_ampt_vector(sample_aoi, empty_ssurgo, sample_config)
