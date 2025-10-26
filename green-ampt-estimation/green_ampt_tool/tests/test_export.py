import sys
from pathlib import Path
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.export import export_raw_ssurgo_data, export_parameter_vectors
from green_ampt_tool.data_access import SSURGOData
from green_ampt_tool.config import PipelineConfig


class TestExportRawSSURGOData:
    """Test export_raw_ssurgo_data function."""

    def test_basic_export(self, tmp_path):
        """Test basic raw SSURGO data export."""
        # Create sample SSURGO data
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1", "2"], "geometry": [Point(0, 0), Point(1, 1)]},
            crs="EPSG:4326",
        )
        mapunit = pd.DataFrame({"mukey": ["1", "2"], "muname": ["Soil A", "Soil B"]})
        component = pd.DataFrame({"mukey": ["1", "2"], "cokey": ["10", "20"], "compname": ["Comp A", "Comp B"]})
        chorizon = pd.DataFrame({"cokey": ["10", "20"], "hzdept_r": [0, 0], "hzdepb_r": [10, 10]})
        
        data = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        target_dir = tmp_path / "raw_data"
        export_raw_ssurgo_data(data, target_dir)
        
        # Check that files were created
        assert (target_dir / "mupolygon_raw.shp").exists()
        assert (target_dir / "mapunit_raw.txt").exists()
        assert (target_dir / "component_raw.txt").exists()
        assert (target_dir / "chorizon_raw.txt").exists()

    def test_creates_directory_if_missing(self, tmp_path):
        """Test that target directory is created if it doesn't exist."""
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Point(0, 0)]},
            crs="EPSG:4326",
        )
        mapunit = pd.DataFrame({"mukey": ["1"]})
        component = pd.DataFrame({"mukey": ["1"], "cokey": ["10"]})
        chorizon = pd.DataFrame({"cokey": ["10"]})
        
        data = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        target_dir = tmp_path / "nested" / "raw_data"
        assert not target_dir.exists()
        
        export_raw_ssurgo_data(data, target_dir)
        
        assert target_dir.exists()
        assert (target_dir / "mupolygon_raw.shp").exists()

    def test_pipe_delimited_format(self, tmp_path):
        """Test that text files use pipe delimiter."""
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Point(0, 0)]},
            crs="EPSG:4326",
        )
        mapunit = pd.DataFrame({"mukey": ["1"], "muname": ["Test Soil"]})
        component = pd.DataFrame({"mukey": ["1"], "cokey": ["10"]})
        chorizon = pd.DataFrame({"cokey": ["10"]})
        
        data = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        target_dir = tmp_path / "raw_data"
        export_raw_ssurgo_data(data, target_dir)
        
        # Read and check format
        content = (target_dir / "mapunit_raw.txt").read_text()
        assert "|" in content
        assert "mukey|muname" in content or "muname|mukey" in content

    def test_overwrites_existing_files(self, tmp_path):
        """Test that existing files are overwritten."""
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Point(0, 0)]},
            crs="EPSG:4326",
        )
        mapunit = pd.DataFrame({"mukey": ["1"], "value": ["first"]})
        component = pd.DataFrame({"mukey": ["1"], "cokey": ["10"]})
        chorizon = pd.DataFrame({"cokey": ["10"]})
        
        data1 = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        target_dir = tmp_path / "raw_data"
        export_raw_ssurgo_data(data1, target_dir)
        
        # Export again with different data
        mapunit2 = pd.DataFrame({"mukey": ["1"], "value": ["second"]})
        data2 = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit2,
            component=component,
            chorizon=chorizon,
        )
        export_raw_ssurgo_data(data2, target_dir)
        
        # Read and verify it was overwritten
        content = (target_dir / "mapunit_raw.txt").read_text()
        assert "second" in content


class TestExportParameterVectors:
    """Test export_parameter_vectors function."""

    def test_basic_vector_export(self, tmp_path):
        """Test basic vector parameter export."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2"],
                "ksat": [5.0, 3.0],
                "theta_s": [0.45, 0.50],
                "geometry": [Point(0, 0), Point(1, 1)],
            },
            crs="EPSG:4326",
        )
        
        result_path = export_parameter_vectors(vector, config)
        
        assert result_path.exists()
        assert result_path.suffix == ".shp"
        assert result_path.parent == config.vector_dir

    def test_shapefile_format(self, tmp_path):
        """Test that output is in ESRI Shapefile format."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result_path = export_parameter_vectors(vector, config)
        
        # Read back the shapefile
        reloaded = gpd.read_file(result_path)
        assert len(reloaded) == 1
        assert "ksat" in reloaded.columns

    def test_uses_config_prefix(self, tmp_path):
        """Test that output filename uses config prefix."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_prefix="test_run",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result_path = export_parameter_vectors(vector, config)
        
        assert "test_run" in result_path.name

    def test_preserves_crs(self, tmp_path):
        """Test that CRS is preserved in output."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:3857",
        )
        
        result_path = export_parameter_vectors(vector, config)
        
        reloaded = gpd.read_file(result_path)
        assert reloaded.crs is not None

    def test_multiple_parameters(self, tmp_path):
        """Test export with multiple parameter columns."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "theta_s": [0.45],
                "psi": [10.0],
                "theta_i": [0.2],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result_path = export_parameter_vectors(vector, config)
        
        reloaded = gpd.read_file(result_path)
        assert "ksat" in reloaded.columns
        assert "theta_s" in reloaded.columns
        assert "psi" in reloaded.columns
        assert "theta_i" in reloaded.columns
