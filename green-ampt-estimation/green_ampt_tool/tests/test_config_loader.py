"""Tests for configuration file loading."""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.config_loader import (
    load_config_file,
    build_config_from_dict,
    load_config_from_file,
)
from green_ampt_tool.config import PipelineConfig


class TestLoadConfigFile:
    """Test load_config_file function."""

    def test_load_json_config(self, tmp_path):
        """Test loading JSON configuration file."""
        config_path = tmp_path / "config.json"
        config_data = {
            "aoi": "test.shp",
            "output_dir": "outputs",
            "output_resolution": 20.0,
        }
        config_path.write_text(json.dumps(config_data))
        
        result = load_config_file(config_path)
        
        assert result["aoi"] == "test.shp"
        assert result["output_dir"] == "outputs"
        assert result["output_resolution"] == 20.0

    def test_load_yaml_config(self, tmp_path):
        """Test loading YAML configuration file."""
        pytest.importorskip("yaml")
        
        config_path = tmp_path / "config.yaml"
        config_text = """
aoi: test.shp
output_dir: outputs
output_resolution: 20.0
depth_limit_cm: 15.0
"""
        config_path.write_text(config_text)
        
        result = load_config_file(config_path)
        
        assert result["aoi"] == "test.shp"
        assert result["output_dir"] == "outputs"
        assert result["output_resolution"] == 20.0
        assert result["depth_limit_cm"] == 15.0

    def test_load_yml_extension(self, tmp_path):
        """Test loading .yml extension."""
        pytest.importorskip("yaml")
        
        config_path = tmp_path / "config.yml"
        config_text = "aoi: test.shp\noutput_dir: outputs"
        config_path.write_text(config_text)
        
        result = load_config_file(config_path)
        
        assert result["aoi"] == "test.shp"

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        config_path = tmp_path / "missing.json"
        
        with pytest.raises(FileNotFoundError):
            load_config_file(config_path)

    def test_unsupported_format_raises_error(self, tmp_path):
        """Test that unsupported format raises ValueError."""
        config_path = tmp_path / "config.txt"
        config_path.write_text("aoi: test.shp")
        
        with pytest.raises(ValueError, match="Unsupported configuration file format"):
            load_config_file(config_path)


class TestBuildConfigFromDict:
    """Test build_config_from_dict function."""

    def test_minimal_config(self, tmp_path):
        """Test building config with minimal required fields."""
        aoi_path = tmp_path / "test.shp"
        aoi_path.touch()
        
        config_dict = {
            "aoi": str(aoi_path),
            "output_dir": str(tmp_path / "outputs"),
        }
        
        config = build_config_from_dict(config_dict)
        
        assert isinstance(config, PipelineConfig)
        assert config.aoi_path == aoi_path
        assert config.output_resolution == 10.0  # default
        assert config.data_source == "pysda"  # default

    def test_config_with_layer_in_path(self, tmp_path):
        """Test parsing layer from AOI path."""
        aoi_path = tmp_path / "test.gpkg"
        aoi_path.touch()
        
        config_dict = {
            "aoi": f"{aoi_path}:my_layer",
            "output_dir": str(tmp_path / "outputs"),
        }
        
        config = build_config_from_dict(config_dict)
        
        assert config.aoi_path == aoi_path
        assert config.aoi_layer == "my_layer"

    def test_config_with_explicit_layer(self, tmp_path):
        """Test explicit aoi_layer field."""
        aoi_path = tmp_path / "test.gpkg"
        aoi_path.touch()
        
        config_dict = {
            "aoi": str(aoi_path),
            "aoi_layer": "explicit_layer",
            "output_dir": str(tmp_path / "outputs"),
        }
        
        config = build_config_from_dict(config_dict)
        
        assert config.aoi_layer == "explicit_layer"

    def test_config_with_all_fields(self, tmp_path):
        """Test building config with all fields."""
        aoi_path = tmp_path / "test.shp"
        aoi_path.touch()
        
        config_dict = {
            "aoi": str(aoi_path),
            "output_dir": str(tmp_path / "outputs"),
            "output_resolution": 5.0,
            "output_crs": "EPSG:3857",
            "output_prefix": "test_",
            "data_source": "pysda",
            "pysda_timeout": 600,
            "depth_limit_cm": 20.0,
            "export_raw_data": False,
            "use_lookup_table": False,
            "use_hsg_lookup": True,
        }
        
        config = build_config_from_dict(config_dict)
        
        assert config.output_resolution == 5.0
        assert config.output_crs == "EPSG:3857"
        assert config.output_prefix == "test_"
        assert config.pysda_timeout == 600
        assert config.depth_limit_cm == 20.0
        assert config.export_raw_data is False
        assert config.use_lookup_table is False
        assert config.use_hsg_lookup is True

    def test_config_with_local_ssurgo(self, tmp_path):
        """Test config with local SSURGO paths."""
        # Create dummy files
        aoi_path = tmp_path / "test.shp"
        aoi_path.touch()
        mupolygon = tmp_path / "mupolygon.shp"
        mupolygon.touch()
        mapunit = tmp_path / "mapunit.txt"
        mapunit.touch()
        component = tmp_path / "component.txt"
        component.touch()
        chorizon = tmp_path / "chorizon.txt"
        chorizon.touch()
        
        config_dict = {
            "aoi": str(aoi_path),
            "output_dir": str(tmp_path / "outputs"),
            "data_source": "local",
            "local_ssurgo": {
                "mupolygon": str(mupolygon),
                "mapunit": str(mapunit),
                "component": str(component),
                "chorizon": str(chorizon),
            },
        }
        
        config = build_config_from_dict(config_dict)
        
        assert config.data_source == "local"
        assert config.local_ssurgo is not None
        assert config.local_ssurgo.mupolygon == mupolygon

    def test_missing_aoi_raises_error(self, tmp_path):
        """Test that missing AOI field raises ValueError."""
        config_dict = {
            "output_dir": str(tmp_path / "outputs"),
        }
        
        with pytest.raises(ValueError, match="must specify 'aoi_path' or 'aoi'"):
            build_config_from_dict(config_dict)


class TestLoadConfigFromFile:
    """Test load_config_from_file function."""

    def test_load_complete_workflow(self, tmp_path):
        """Test complete workflow from file to config."""
        aoi_path = tmp_path / "test.shp"
        aoi_path.touch()
        
        config_path = tmp_path / "config.json"
        config_data = {
            "aoi": str(aoi_path),
            "output_dir": str(tmp_path / "outputs"),
            "output_resolution": 15.0,
        }
        config_path.write_text(json.dumps(config_data))
        
        config = load_config_from_file(config_path)
        
        assert isinstance(config, PipelineConfig)
        assert config.aoi_path == aoi_path
        assert config.output_resolution == 15.0
