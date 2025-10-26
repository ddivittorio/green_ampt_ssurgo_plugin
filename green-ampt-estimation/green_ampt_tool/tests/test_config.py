import sys
from pathlib import Path
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.config import LocalSSURGOPaths, PipelineConfig


class TestLocalSSURGOPaths:
    """Test LocalSSURGOPaths configuration and validation."""

    def test_resolve_existing_paths(self, tmp_path):
        """Test that resolve() works with existing files."""
        # Create temporary files
        mupolygon = tmp_path / "mupolygon.shp"
        mapunit = tmp_path / "mapunit.txt"
        component = tmp_path / "component.txt"
        chorizon = tmp_path / "chorizon.txt"
        
        for file in [mupolygon, mapunit, component, chorizon]:
            file.touch()
        
        paths = LocalSSURGOPaths(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        resolved = paths.resolve()
        
        assert resolved.mupolygon.exists()
        assert resolved.mapunit.exists()
        assert resolved.component.exists()
        assert resolved.chorizon.exists()

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing files raise FileNotFoundError."""
        mupolygon = tmp_path / "mupolygon.shp"
        mapunit = tmp_path / "mapunit.txt"
        component = tmp_path / "component.txt"
        chorizon = tmp_path / "missing.txt"  # This one doesn't exist
        
        mupolygon.touch()
        mapunit.touch()
        component.touch()
        
        paths = LocalSSURGOPaths(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        with pytest.raises(FileNotFoundError, match="SSURGO file not found"):
            paths.resolve()


class TestPipelineConfig:
    """Test PipelineConfig initialization and validation."""

    def test_basic_initialization(self, tmp_path):
        """Test basic config initialization with required parameters."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            data_source="pysda",
        )
        
        assert config.aoi_path.exists()
        assert config.output_dir.exists()
        assert config.raster_dir.exists()
        assert config.vector_dir.exists()
        assert config.data_source == "pysda"

    def test_missing_aoi_raises_error(self, tmp_path):
        """Test that missing AOI file raises FileNotFoundError."""
        aoi_file = tmp_path / "missing_aoi.shp"
        output_dir = tmp_path / "output"
        
        with pytest.raises(FileNotFoundError, match="AOI file not found"):
            PipelineConfig(
                aoi_path=aoi_file,
                output_dir=output_dir,
            )

    def test_local_data_source_requires_ssurgo_paths(self, tmp_path):
        """Test that local data source requires LocalSSURGOPaths."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        with pytest.raises(ValueError, match="local_ssurgo paths must be provided"):
            PipelineConfig(
                aoi_path=aoi_file,
                output_dir=output_dir,
                data_source="local",
                local_ssurgo=None,
            )

    def test_negative_resolution_raises_error(self, tmp_path):
        """Test that negative resolution raises ValueError."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        with pytest.raises(ValueError, match="output_resolution must be positive"):
            PipelineConfig(
                aoi_path=aoi_file,
                output_dir=output_dir,
                output_resolution=-10.0,
            )

    def test_negative_depth_limit_raises_error(self, tmp_path):
        """Test that negative depth limit raises ValueError."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        with pytest.raises(ValueError, match="depth_limit_cm must be positive"):
            PipelineConfig(
                aoi_path=aoi_file,
                output_dir=output_dir,
                depth_limit_cm=-5.0,
            )

    def test_output_crs_inheritance(self, tmp_path):
        """Test that output_crs can be None for AOI inheritance."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_crs=None,
        )
        
        assert config.output_crs is None
        
        # Test various "None-like" values
        for value in ["None", "AOI", ""]:
            config = PipelineConfig(
                aoi_path=aoi_file,
                output_dir=output_dir,
                output_crs=value,
            )
            assert config.output_crs is None

    def test_raw_data_directory_creation(self, tmp_path):
        """Test that raw data directory is created when export is enabled."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            export_raw_data=True,
        )
        
        assert config.raw_data_dir is not None
        assert config.raw_data_dir.exists()
        assert config.raw_data_dir.parent == config.output_dir

    def test_raw_data_disabled(self, tmp_path):
        """Test that raw data directory is None when export is disabled."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            export_raw_data=False,
        )
        
        assert config.raw_data_dir is None

    def test_custom_raw_data_directory(self, tmp_path):
        """Test custom raw data directory path."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        custom_raw_dir = tmp_path / "custom_raw"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            export_raw_data=True,
            raw_data_dir=custom_raw_dir,
        )
        
        assert config.raw_data_dir == custom_raw_dir
        assert config.raw_data_dir.exists()

    def test_use_pysda_property(self, tmp_path):
        """Test use_pysda convenience property."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config_pysda = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            data_source="pysda",
        )
        assert config_pysda.use_pysda is True
        
        # Create local SSURGO paths
        mupolygon = tmp_path / "mupolygon.shp"
        mapunit = tmp_path / "mapunit.txt"
        component = tmp_path / "component.txt"
        chorizon = tmp_path / "chorizon.txt"
        for file in [mupolygon, mapunit, component, chorizon]:
            file.touch()
        
        local_paths = LocalSSURGOPaths(
            mupolygon=mupolygon,
            mapunit=mapunit,
            component=component,
            chorizon=chorizon,
        )
        
        config_local = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            data_source="local",
            local_ssurgo=local_paths,
        )
        assert config_local.use_pysda is False

    def test_build_raster_path(self, tmp_path):
        """Test raster path generation."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        raster_path = config.build_raster_path("ksat")
        assert raster_path.name == "ksat_green_ampt.tif"
        assert raster_path.parent == config.raster_dir

    def test_build_raster_path_with_prefix(self, tmp_path):
        """Test raster path generation with custom prefix."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_prefix="test_run",
        )
        
        raster_path = config.build_raster_path("theta_s")
        assert raster_path.name == "test_run_theta_s_green_ampt.tif"

    def test_build_vector_path(self, tmp_path):
        """Test vector path generation."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        
        vector_path = config.build_vector_path()
        assert vector_path.name == "green_ampt_params.shp"
        assert vector_path.parent == config.vector_dir

    def test_build_vector_path_with_prefix(self, tmp_path):
        """Test vector path generation with custom prefix."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            output_prefix="test_run",
        )
        
        vector_path = config.build_vector_path()
        assert vector_path.name == "test_run_green_ampt_params.shp"

    def test_lookup_table_flags(self, tmp_path):
        """Test lookup table configuration flags."""
        aoi_file = tmp_path / "aoi.shp"
        aoi_file.touch()
        output_dir = tmp_path / "output"
        
        # Test default (use lookup table)
        config = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
        )
        assert config.use_lookup_table is True
        assert config.use_hsg_lookup is False
        
        # Test HSG lookup
        config_hsg = PipelineConfig(
            aoi_path=aoi_file,
            output_dir=output_dir,
            use_hsg_lookup=True,
        )
        assert config_hsg.use_hsg_lookup is True
