import sys
from pathlib import Path
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.data_access import (
    SSURGOData,
    read_aoi,
    load_ssurgo_local,
    parse_aoi_path,
)
from green_ampt_tool.config import LocalSSURGOPaths


class TestParseAOIPath:
    """Test parse_aoi_path function."""

    def test_simple_path_without_layer(self):
        """Test parsing simple path without layer."""
        path, layer = parse_aoi_path("test.shp")
        assert path == Path("test.shp")
        assert layer is None

    def test_path_with_layer(self):
        """Test parsing path with layer specification."""
        path, layer = parse_aoi_path("test.gpkg:my_layer")
        assert path == Path("test.gpkg")
        assert layer == "my_layer"

    def test_geodatabase_with_feature_class(self):
        """Test parsing geodatabase with feature class."""
        path, layer = parse_aoi_path("data.gdb:feature_class")
        assert path == Path("data.gdb")
        assert layer == "feature_class"

    def test_windows_drive_letter(self):
        """Test handling Windows drive letter (C:)."""
        path, layer = parse_aoi_path("C:\\data\\test.shp")
        assert path == Path("C:\\data\\test.shp")
        assert layer is None

    def test_windows_path_with_layer(self):
        """Test Windows path with layer specification."""
        path, layer = parse_aoi_path("C:\\data\\test.gpkg:my_layer")
        assert path == Path("C:\\data\\test.gpkg")
        assert layer == "my_layer"

    def test_absolute_unix_path(self):
        """Test absolute Unix path."""
        path, layer = parse_aoi_path("/home/user/data.gpkg:layer")
        assert path == Path("/home/user/data.gpkg")
        assert layer == "layer"


class TestSSURGOData:
    """Test SSURGOData dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        mupolygon = gpd.GeoDataFrame({"mukey": ["1"], "geometry": [Point(0, 0)]}, crs="EPSG:4326")
        mapunit = pd.DataFrame({"mukey": ["1"]})
        component = pd.DataFrame({"mukey": ["1"], "cokey": ["10"]})
        chorizon = pd.DataFrame({"cokey": ["10"]})
        
        data = SSURGOData(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        assert len(data.mupolygon) == 1
        assert len(data.mapunit) == 1
        assert len(data.component) == 1
        assert len(data.chorizon) == 1


class TestReadAOI:
    """Test read_aoi function."""

    def test_basic_reading(self, tmp_path):
        """Test basic AOI reading."""
        aoi_path = tmp_path / "test_aoi.shp"
        
        # Create a simple shapefile
        gdf = gpd.GeoDataFrame(
            {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:3857",
        )
        gdf.to_file(aoi_path)
        
        result = read_aoi(aoi_path)
        
        assert len(result) == 1
        # Should be reprojected to WGS84
        assert result.crs.to_string() == "EPSG:4326"

    def test_already_wgs84(self, tmp_path):
        """Test AOI already in WGS84."""
        aoi_path = tmp_path / "test_aoi.shp"
        
        gdf = gpd.GeoDataFrame(
            {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        gdf.to_file(aoi_path)
        
        result = read_aoi(aoi_path)
        
        assert result.crs.to_string() == "EPSG:4326"

    def test_geopackage_with_layer(self, tmp_path):
        """Test reading GeoPackage with explicit layer."""
        gpkg_path = tmp_path / "test.gpkg"
        
        gdf = gpd.GeoDataFrame(
            {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        gdf.to_file(gpkg_path, layer="my_layer", driver="GPKG")
        
        result = read_aoi(gpkg_path, layer="my_layer")
        
        assert len(result) == 1
        assert result.crs.to_string() == "EPSG:4326"

    def test_empty_geometry_raises_error(self, tmp_path):
        """Test that empty geometry raises ValueError."""
        aoi_path = tmp_path / "empty_aoi.shp"
        
        # Create empty shapefile
        gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        gdf.to_file(aoi_path)
        
        with pytest.raises(ValueError, match="AOI geometry is empty"):
            read_aoi(aoi_path)

    def test_missing_crs_raises_error(self, tmp_path):
        """Test that missing CRS raises ValueError."""
        aoi_path = tmp_path / "no_crs_aoi.shp"
        
        # Create shapefile without CRS
        gdf = gpd.GeoDataFrame(
            {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs=None,
        )
        gdf.to_file(aoi_path, crs=None)
        
        with pytest.raises(ValueError, match="AOI file is missing a Coordinate Reference System"):
            read_aoi(aoi_path)


class TestLoadSSURGOLocal:
    """Test load_ssurgo_local function."""

    def test_basic_loading(self, tmp_path):
        """Test basic SSURGO data loading."""
        # Create mupolygon shapefile
        mupolygon_path = tmp_path / "mupolygon.shp"
        gdf = gpd.GeoDataFrame(
            {"mukey": ["1", "2"], "geometry": [Point(0, 0), Point(1, 1)]},
            crs="EPSG:4326",
        )
        gdf.to_file(mupolygon_path)
        
        # Create pipe-delimited text files
        mapunit_path = tmp_path / "mapunit.txt"
        mapunit_path.write_text("mukey|muname\n1|Test Soil 1\n2|Test Soil 2\n")
        
        component_path = tmp_path / "component.txt"
        component_path.write_text("mukey|cokey|compname\n1|10|Component 1\n2|20|Component 2\n")
        
        chorizon_path = tmp_path / "chorizon.txt"
        chorizon_path.write_text(
            "cokey|hzdept_r|hzdepb_r|ksat_r|sandtotal_r|claytotal_r|dbthirdbar_r\n"
            "10|0|10|5.0|50.0|20.0|1.5\n"
            "20|0|10|3.0|30.0|40.0|1.6\n"
        )
        
        paths = LocalSSURGOPaths(
            mupolygon=mupolygon_path,
            mapunit=mapunit_path,
            component=component_path,
            chorizon=chorizon_path,
        )
        
        result = load_ssurgo_local(paths)
        
        assert isinstance(result, SSURGOData)
        assert len(result.mupolygon) == 2
        assert len(result.mapunit) == 2
        assert len(result.component) == 2
        assert len(result.chorizon) == 2
        # chorizon should have mukey merged from component
        assert "mukey" in result.chorizon.columns

    def test_missing_required_columns_raises_error(self, tmp_path):
        """Test that missing required columns raises error."""
        mupolygon_path = tmp_path / "mupolygon.shp"
        gdf = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Point(0, 0)]},
            crs="EPSG:4326",
        )
        gdf.to_file(mupolygon_path)
        
        mapunit_path = tmp_path / "mapunit.txt"
        # Missing mukey column
        mapunit_path.write_text("muname\nTest Soil\n")
        
        component_path = tmp_path / "component.txt"
        component_path.write_text("mukey|cokey\n1|10\n")
        
        chorizon_path = tmp_path / "chorizon.txt"
        chorizon_path.write_text(
            "cokey|hzdept_r|hzdepb_r|ksat_r|sandtotal_r|claytotal_r|dbthirdbar_r\n"
            "10|0|10|5.0|50.0|20.0|1.5\n"
        )
        
        paths = LocalSSURGOPaths(
            mupolygon=mupolygon_path,
            mapunit=mapunit_path,
            component=component_path,
            chorizon=chorizon_path,
        )
        
        with pytest.raises(ValueError, match="Required columns"):
            load_ssurgo_local(paths)

    def test_mukey_merge_from_component(self, tmp_path):
        """Test that mukey is properly merged from component to chorizon."""
        mupolygon_path = tmp_path / "mupolygon.shp"
        gdf = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Point(0, 0)]},
            crs="EPSG:4326",
        )
        gdf.to_file(mupolygon_path)
        
        mapunit_path = tmp_path / "mapunit.txt"
        mapunit_path.write_text("mukey\n1\n")
        
        component_path = tmp_path / "component.txt"
        component_path.write_text("mukey|cokey\n1|10\n")
        
        chorizon_path = tmp_path / "chorizon.txt"
        # No mukey in chorizon
        chorizon_path.write_text(
            "cokey|hzdept_r|hzdepb_r|ksat_r|sandtotal_r|claytotal_r|dbthirdbar_r\n"
            "10|0|10|5.0|50.0|20.0|1.5\n"
        )
        
        paths = LocalSSURGOPaths(
            mupolygon=mupolygon_path,
            mapunit=mapunit_path,
            component=component_path,
            chorizon=chorizon_path,
        )
        
        result = load_ssurgo_local(paths)
        
        # chorizon should have mukey merged
        assert "mukey" in result.chorizon.columns
        assert result.chorizon.iloc[0]["mukey"] == "1"
