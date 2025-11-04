import sys
from pathlib import Path
import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.rasterization import prepare_grid, rasterize_parameters, RasterGrid
from green_ampt_tool.config import PipelineConfig

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio not available")
class TestPrepareGrid:
    """Test prepare_grid function."""

    def test_basic_grid_preparation(self):
        """Test basic grid preparation."""
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        grid = prepare_grid(vector, resolution=1.0, output_crs="EPSG:4326")
        
        assert isinstance(grid, RasterGrid)
        assert grid.width > 0
        assert grid.height > 0
        assert grid.transform is not None

    def test_grid_dimensions_match_resolution(self):
        """Test that grid dimensions match specified resolution."""
        # Create 10x10 square
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        grid = prepare_grid(vector, resolution=1.0, output_crs="EPSG:4326")
        
        # With 10x10 area and 1.0 resolution, expect ~10x10 grid
        assert 8 <= grid.width <= 12  # Allow some tolerance
        assert 8 <= grid.height <= 12

    def test_higher_resolution_increases_dimensions(self):
        """Test that higher resolution (smaller value) increases grid dimensions."""
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        grid_low_res = prepare_grid(vector, resolution=2.0, output_crs="EPSG:4326")
        grid_high_res = prepare_grid(vector, resolution=1.0, output_crs="EPSG:4326")
        
        # Higher resolution (smaller value) should have more pixels
        assert grid_high_res.width > grid_low_res.width
        assert grid_high_res.height > grid_low_res.height

    def test_crs_reprojection(self):
        """Test that vector is reprojected to output CRS."""
        # Create vector in EPSG:4326
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
            },
            crs="EPSG:4326",
        )
        
        # Request grid in EPSG:3857
        grid = prepare_grid(vector, resolution=1000.0, output_crs="EPSG:3857")
        
        # Should succeed without error
        assert grid.width > 0
        assert grid.height > 0

    def test_minimum_dimensions(self):
        """Test that grid has minimum dimensions of 1x1."""
        # Very small polygon with high resolution
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001)])],
            },
            crs="EPSG:4326",
        )
        
        grid = prepare_grid(vector, resolution=1.0, output_crs="EPSG:4326")
        
        # Should have at least 1x1 pixels
        assert grid.width >= 1
        assert grid.height >= 1


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio not available")
class TestRasterizeParameters:
    """Test rasterize_parameters function."""

    def test_basic_rasterization(self, tmp_path):
        """Test basic parameter rasterization."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        # Check that raster file was created
        raster_path = config.build_raster_path("ksat")
        assert raster_path.exists()

    def test_multiple_parameters(self, tmp_path):
        """Test rasterizing multiple parameters."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "theta_s": [0.45],
                "psi": [10.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat", "theta_s", "psi"], config)
        
        # Check that all raster files were created
        assert config.build_raster_path("ksat").exists()
        assert config.build_raster_path("theta_s").exists()
        assert config.build_raster_path("psi").exists()

    def test_skips_missing_columns(self, tmp_path):
        """Test that missing parameter columns are skipped."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        # Request rasterization of both existing and non-existing parameters
        rasterize_parameters(vector, ["ksat", "missing_param"], config)
        
        # Only ksat should be created
        assert config.build_raster_path("ksat").exists()
        assert not config.build_raster_path("missing_param").exists()

    def test_geotiff_format(self, tmp_path):
        """Test that output is in GeoTIFF format."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        raster_path = config.build_raster_path("ksat")
        
        # Read and verify format
        with rasterio.open(raster_path) as src:
            assert src.driver == "GTiff"
            assert src.count == 1  # Single band
            assert src.dtypes[0] == "float32"

    def test_raster_values(self, tmp_path):
        """Test that raster contains correct values."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        raster_path = config.build_raster_path("ksat")
        
        # Read and check values
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            # Most pixels should have the value 5.0 (or NaN outside polygon)
            valid_pixels = data[~np.isnan(data)]
            assert len(valid_pixels) > 0
            assert np.all(valid_pixels == pytest.approx(5.0))

    def test_nan_for_missing_values(self, tmp_path):
        """Test that NaN values are handled correctly."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2"],
                "ksat": [5.0, float("nan")],
                "geometry": [
                    Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),
                    Polygon([(5, 0), (10, 0), (10, 5), (5, 5)]),
                ],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        raster_path = config.build_raster_path("ksat")
        
        # Read and verify NaN handling
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            # Should have both valid and NaN values
            assert np.any(~np.isnan(data))
            assert np.any(np.isnan(data))

    def test_raster_metadata(self, tmp_path):
        """Test that raster has correct metadata."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        raster_path = config.build_raster_path("ksat")
        
        # Read and check metadata
        with rasterio.open(raster_path) as src:
            assert src.crs.to_string() == "EPSG:4326"
            # Nodata can be set to a specific value, NaN, or None depending on format
            # Just verify it's accessible without error
            _ = src.nodata
            tags = src.tags()
            assert "parameter" in tags or "source" in tags

    def test_uses_config_prefix(self, tmp_path):
        """Test that raster filename uses config prefix."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_prefix="test_run",
            output_resolution=1.0,
            output_crs="EPSG:4326",
        )
        
        vector = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
            },
            crs="EPSG:4326",
        )
        
        rasterize_parameters(vector, ["ksat"], config)
        
        raster_path = config.build_raster_path("ksat")
        assert "test_run" in raster_path.name
        assert raster_path.exists()
