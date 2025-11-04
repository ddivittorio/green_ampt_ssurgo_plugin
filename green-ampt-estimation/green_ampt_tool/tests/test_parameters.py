import sys
from pathlib import Path
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.parameters import (
    default_wetting_front_suction,
    enrich_with_green_ampt_parameters,
    build_lookup_parameters,
    build_hsg_lookup_parameters,
    apply_initial_deficit_mode,
    enrich_with_lookup_parameters,
    emit_units_summary,
    _clamp_percentage,
    _safe_float,
)


class TestDefaultWettingFrontSuction:
    """Test default_wetting_front_suction pedotransfer function."""

    def test_pure_sand(self):
        """Test suction for pure sand."""
        result = default_wetting_front_suction(100.0, 0.0)
        # 20 * (100/100) + 10 * (0/100) = 20
        assert result == pytest.approx(20.0)

    def test_pure_clay(self):
        """Test suction for pure clay."""
        result = default_wetting_front_suction(0.0, 100.0)
        # 20 * (0/100) + 10 * (100/100) = 10
        assert result == pytest.approx(10.0)

    def test_mixed_soil(self):
        """Test suction for mixed soil."""
        result = default_wetting_front_suction(50.0, 20.0)
        # 20 * (50/100) + 10 * (20/100) = 10 + 2 = 12
        assert result == pytest.approx(12.0)

    def test_out_of_bounds_values(self):
        """Test that values are clamped to 0-100 range."""
        result1 = default_wetting_front_suction(-10.0, 50.0)
        result2 = default_wetting_front_suction(0.0, 50.0)
        assert result1 == result2
        
        result3 = default_wetting_front_suction(50.0, 150.0)
        result4 = default_wetting_front_suction(50.0, 100.0)
        assert result3 == result4


class TestEnrichWithGreenAmptParameters:
    """Test enrich_with_green_ampt_parameters function."""

    def test_basic_enrichment(self):
        """Test basic parameter enrichment."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "ksat": [5.0],
                "theta_s": [0.45],
                "sand_pct": [50.0],
                "clay_pct": [20.0],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils)
        
        assert "psi" in result.columns
        assert "theta_i" in result.columns
        assert result.iloc[0]["theta_i"] == pytest.approx(0.2)

    def test_missing_columns_use_defaults(self):
        """Test that missing columns use default values."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils)
        
        assert "ksat" in result.columns
        assert "theta_s" in result.columns
        assert "psi" in result.columns
        assert result.iloc[0]["ksat"] == pytest.approx(0.0)

    def test_theta_s_bounds(self):
        """Test that theta_s is bounded between 0 and 0.9."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2", "3"],
                "theta_s": [-0.1, 0.5, 1.5],
                "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils)
        
        assert result.iloc[0]["theta_s"] == pytest.approx(0.0)
        assert result.iloc[1]["theta_s"] == pytest.approx(0.5)
        assert result.iloc[2]["theta_s"] == pytest.approx(0.9)

    def test_custom_suction_function(self):
        """Test using custom suction function."""
        def custom_suction(sand, clay):
            return 50.0  # Constant value
        
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "sand_pct": [50.0],
                "clay_pct": [20.0],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils, suction_fn=custom_suction)
        
        assert result.iloc[0]["psi"] == pytest.approx(50.0)

    def test_custom_initial_theta(self):
        """Test using custom initial theta."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils, initial_theta=0.35)
        
        assert result.iloc[0]["theta_i"] == pytest.approx(0.35)

    def test_preserves_crs(self):
        """Test that CRS is preserved."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_green_ampt_parameters(soils)
        
        assert result.crs == soils.crs


class TestBuildLookupParameters:
    """Test build_lookup_parameters function."""

    def test_empty_inputs(self):
        """Test that empty inputs return empty DataFrame."""
        components = pd.DataFrame()
        horizons = pd.DataFrame()
        
        result = build_lookup_parameters(components, horizons)
        
        assert result.empty
        assert "mukey" in result.columns
        assert "Ks_inhr" in result.columns

    def test_basic_lookup(self):
        """Test basic lookup parameter building."""
        components = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
                "hydgrp": ["B"],
                "majcompflag": ["Yes"],
            }
        )
        
        horizons = pd.DataFrame(
            {
                "cokey": ["10"],
                "chkey": ["100"],
                "texcl": ["Loam"],
                "hzdept_r": [0.0],
                "hzdepb_r": [10.0],
            }
        )
        
        result = build_lookup_parameters(components, horizons)
        
        assert len(result) == 1
        assert "Ks_inhr" in result.columns
        assert "psi_in" in result.columns
        assert "theta_s" in result.columns

    def test_initial_deficit_calculations(self):
        """Test that initial deficit calculations are included."""
        components = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
                "hydgrp": ["A"],
                "majcompflag": ["Yes"],
            }
        )
        
        horizons = pd.DataFrame(
            {
                "cokey": ["10"],
                "texcl": ["Sand"],
                "hzdept_r": [0.0],
                "hzdepb_r": [10.0],
            }
        )
        
        result = build_lookup_parameters(components, horizons)
        
        assert "theta_i_design" in result.columns
        assert "theta_i_cont" in result.columns
        assert "dtheta_design" in result.columns
        assert "dtheta_cont" in result.columns

    def test_hsg_merge(self):
        """Test that HSG information is merged."""
        components = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
                "hydgrp": ["A/D"],
                "majcompflag": ["Yes"],
            }
        )
        
        horizons = pd.DataFrame(
            {
                "cokey": ["10"],
                "texcl": ["Sand"],
                "hzdept_r": [0.0],
                "hzdepb_r": [10.0],
            }
        )
        
        result = build_lookup_parameters(components, horizons)
        
        assert "hsg_dom" in result.columns
        assert "hsg_drained" in result.columns
        assert result.iloc[0]["hsg_dom"] == "A"
        assert result.iloc[0]["hsg_drained"] == "D"


class TestBuildHSGLookupParameters:
    """Test build_hsg_lookup_parameters function."""

    def test_basic_hsg_lookup(self):
        """Test basic HSG-based parameter lookup."""
        components = pd.DataFrame(
            {
                "mukey": ["1", "2"],
                "cokey": ["10", "20"],
                "comppct_r": [100, 100],
                "hydgrp": ["A", "D"],
                "majcompflag": ["Yes", "Yes"],
            }
        )
        
        # Create minimal horizons data for the components
        horizons = pd.DataFrame(
            {
                "cokey": ["10", "20"],
                "chkey": ["100", "200"],
                "texcl": ["Sand", "Clay"],
                "hzdept_r": [0, 0],
                "hzdepb_r": [10, 10],
            }
        )
        
        result = build_hsg_lookup_parameters(components, horizons)
        
        assert len(result) == 2
        assert "Ks_inhr" in result.columns
        
        # Check that HSG A has higher Ksat than HSG D
        ksat_a = result[result["hsg_dom"] == "A"]["Ks_inhr"].iloc[0]
        ksat_d = result[result["hsg_dom"] == "D"]["Ks_inhr"].iloc[0]
        assert ksat_a > ksat_d

    def test_empty_components(self):
        """Test with empty components."""
        components = pd.DataFrame()
        horizons = pd.DataFrame()
        
        result = build_hsg_lookup_parameters(components, horizons)
        
        assert result.empty
        assert "mukey" in result.columns


class TestApplyInitialDeficitMode:
    """Test apply_initial_deficit_mode function."""

    def test_design_mode(self):
        """Test design mode application."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "theta_i_design": [0.3],
                "theta_i_cont": [0.4],
                "dtheta_design": [0.2],
                "dtheta_cont": [0.1],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = apply_initial_deficit_mode(soils, mode="design")
        
        assert "theta_i" in result.columns
        assert "dtheta" in result.columns
        assert result.iloc[0]["theta_i"] == pytest.approx(0.3)
        assert result.iloc[0]["dtheta"] == pytest.approx(0.2)

    def test_continuous_mode(self):
        """Test continuous mode application."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "theta_i_design": [0.3],
                "theta_i_cont": [0.4],
                "dtheta_design": [0.2],
                "dtheta_cont": [0.1],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = apply_initial_deficit_mode(soils, mode="continuous")
        
        assert result.iloc[0]["theta_i"] == pytest.approx(0.4)
        assert result.iloc[0]["dtheta"] == pytest.approx(0.1)

    def test_missing_columns_no_error(self):
        """Test that missing columns don't cause errors."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        # Should not raise error
        result = apply_initial_deficit_mode(soils, mode="design")
        assert len(result) == 1


class TestEnrichWithLookupParameters:
    """Test enrich_with_lookup_parameters wrapper function."""

    def test_applies_design_mode_by_default(self):
        """Test that design mode is applied by default."""
        soils = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "theta_i_design": [0.3],
                "theta_i_cont": [0.4],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        result = enrich_with_lookup_parameters(soils)
        
        assert result.iloc[0]["theta_i"] == pytest.approx(0.3)


class TestEmitUnitsSummary:
    """Test emit_units_summary function."""

    def test_returns_dict(self):
        """Test that function returns dictionary."""
        result = emit_units_summary()
        
        assert isinstance(result, dict)
        assert "Ks_inhr" in result
        assert "theta_s" in result
        assert "hsg_dom" in result

    def test_all_expected_keys(self):
        """Test that all expected keys are present."""
        result = emit_units_summary()
        
        expected_keys = [
            "Ks_inhr",
            "psi_in",
            "theta_s",
            "theta_fc",
            "theta_wp",
            "init_def",
            "theta_i_design",
            "theta_i_cont",
            "dtheta_design",
            "dtheta_cont",
            "hsg_dom",
            "hsg_dry",
            "hsg_drained",
            "hsg_comp",
            "texcl",
        ]
        
        for key in expected_keys:
            assert key in result


class TestClampPercentage:
    """Test _clamp_percentage utility function."""

    def test_normal_value(self):
        """Test normal percentage value."""
        assert _clamp_percentage(50.0) == 50.0

    def test_negative_value(self):
        """Test negative value is clamped to 0."""
        assert _clamp_percentage(-10.0) == 0.0

    def test_over_100_value(self):
        """Test value over 100 is clamped to 100."""
        assert _clamp_percentage(150.0) == 100.0

    def test_zero_value(self):
        """Test zero value."""
        assert _clamp_percentage(0.0) == 0.0

    def test_hundred_value(self):
        """Test 100 value."""
        assert _clamp_percentage(100.0) == 100.0

    def test_none_value(self):
        """Test None value returns 0."""
        assert _clamp_percentage(None) == 0.0

    def test_nan_value(self):
        """Test NaN value returns 0."""
        assert _clamp_percentage(float("nan")) == 0.0


class TestSafeFloat:
    """Test _safe_float utility function."""

    def test_valid_float(self):
        """Test valid float conversion."""
        assert _safe_float(5.0) == 5.0
        assert _safe_float("5.0") == 5.0
        assert _safe_float(5) == 5.0

    def test_none_value(self):
        """Test None returns None."""
        assert _safe_float(None) is None

    def test_nan_value(self):
        """Test NaN returns None."""
        assert _safe_float(float("nan")) is None

    def test_invalid_string(self):
        """Test invalid string returns None."""
        assert _safe_float("not a number") is None

    def test_empty_string(self):
        """Test empty string returns None."""
        assert _safe_float("") is None
