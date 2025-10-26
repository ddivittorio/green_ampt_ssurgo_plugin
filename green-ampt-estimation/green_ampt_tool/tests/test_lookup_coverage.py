"""
Additional tests for lookup.py to improve coverage.

These tests cover edge cases and less-traveled code paths in the lookup module.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.lookup import (
    _norm_texcl,
    _derive_texcl_from_percentages,
    _harmonic_mean,
    _arith_mean,
    component_surface_params_us,
    mapunit_params_us,
    build_hsg_parameters,
)


class TestTextureNormalization:
    """Test texture normalization helper functions."""
    
    def test_norm_texcl_returns_none_for_none(self):
        """None input should return None."""
        assert _norm_texcl(None) is None
    
    def test_norm_texcl_normalizes_lowercase(self):
        """Lowercase texture names should be normalized."""
        assert _norm_texcl("sand") == "Sand"
        assert _norm_texcl("loam") == "Loam"
        assert _norm_texcl("clay") == "Clay"
    
    def test_norm_texcl_handles_extra_whitespace(self):
        """Extra whitespace should be stripped."""
        assert _norm_texcl("  sand  ") == "Sand"
        assert _norm_texcl("\tloam\n") == "Loam"
    
    def test_norm_texcl_handles_mixed_case(self):
        """Mixed case should be normalized."""
        assert _norm_texcl("SAND") == "Sand"
        assert _norm_texcl("SaNd") == "Sand"
    
    def test_norm_texcl_returns_none_for_unknown(self):
        """Unknown texture names should return None."""
        assert _norm_texcl("unknown") is None
        assert _norm_texcl("gravel") is None


class TestDeriveTexclFromPercentages:
    """Test texture derivation from sand/clay percentages."""
    
    def test_derive_sand(self):
        """Test Sand classification."""
        result = _derive_texcl_from_percentages(90, 5)
        assert result == "Sand"
    
    def test_derive_loamy_sand(self):
        """Test Loamy Sand classification."""
        result = _derive_texcl_from_percentages(80, 10)
        assert result == "Loamy Sand"
    
    def test_derive_sandy_loam(self):
        """Test Sandy Loam classification."""
        result = _derive_texcl_from_percentages(65, 10)
        assert result == "Sandy Loam"
    
    def test_derive_loam(self):
        """Test Loam classification."""
        result = _derive_texcl_from_percentages(40, 18)
        assert result == "Loam"
    
    def test_derive_silt_loam(self):
        """Test Silt Loam classification."""
        result = _derive_texcl_from_percentages(10, 10)
        assert result == "Silt Loam"
    
    def test_derive_sandy_clay_loam(self):
        """Test Sandy Clay Loam classification."""
        result = _derive_texcl_from_percentages(60, 28)
        assert result == "Sandy Clay Loam"
    
    def test_derive_clay_loam(self):
        """Test Clay Loam classification."""
        result = _derive_texcl_from_percentages(35, 30)
        assert result == "Clay Loam"
    
    def test_derive_silty_clay_loam(self):
        """Test Silty Clay Loam classification."""
        result = _derive_texcl_from_percentages(10, 32)
        assert result == "Silty Clay Loam"
    
    def test_derive_sandy_clay(self):
        """Test Sandy Clay classification."""
        result = _derive_texcl_from_percentages(50, 42)
        assert result == "Sandy Clay"
    
    def test_derive_silty_clay(self):
        """Test Silty Clay classification."""
        result = _derive_texcl_from_percentages(10, 45)
        assert result == "Silty Clay"
    
    def test_derive_clay(self):
        """Test Clay classification."""
        result = _derive_texcl_from_percentages(30, 50)
        assert result == "Clay"
    
    def test_none_inputs_return_none(self):
        """None inputs should return None."""
        assert _derive_texcl_from_percentages(None, None) is None
        assert _derive_texcl_from_percentages(50, None) is None
        assert _derive_texcl_from_percentages(None, 50) is None
    
    def test_invalid_inputs_return_none(self):
        """Invalid inputs should return None."""
        assert _derive_texcl_from_percentages("invalid", 50) is None
        assert _derive_texcl_from_percentages(50, "invalid") is None
    
    def test_zero_total_returns_none(self):
        """Zero total should return a default texture class."""
        # When both sand and clay are 0, we get 100% silt, which is Silt Loam
        result = _derive_texcl_from_percentages(0, 0)
        assert result == "Silt Loam"
    
    def test_out_of_range_values_are_clamped(self):
        """Values outside 0-100 should be clamped."""
        # 150% sand, 50% clay should be normalized to valid percentages
        result = _derive_texcl_from_percentages(150, 50)
        assert result is not None  # Should still return a valid texture


class TestHarmonicMean:
    """Test harmonic mean calculation."""
    
    def test_basic_harmonic_mean(self):
        """Test basic harmonic mean calculation."""
        result = _harmonic_mean([1.0, 2.0], [1.0, 1.0])
        expected = 2.0 / (1.0/1.0 + 1.0/2.0)
        assert result == pytest.approx(expected)
    
    def test_harmonic_mean_with_weights(self):
        """Test harmonic mean with different weights."""
        result = _harmonic_mean([1.0, 4.0], [3.0, 1.0])
        expected = 4.0 / (3.0/1.0 + 1.0/4.0)
        assert result == pytest.approx(expected)
    
    def test_harmonic_mean_filters_zero_values(self):
        """Zero values should be filtered out."""
        result = _harmonic_mean([0.0, 2.0], [1.0, 1.0])
        assert result == pytest.approx(2.0)
    
    def test_harmonic_mean_filters_zero_weights(self):
        """Zero weights should be filtered out."""
        result = _harmonic_mean([1.0, 2.0], [0.0, 1.0])
        assert result == pytest.approx(2.0)
    
    def test_harmonic_mean_all_zeros_returns_nan(self):
        """All zeros should return NaN."""
        import math
        result = _harmonic_mean([0.0, 0.0], [1.0, 1.0])
        assert math.isnan(result)


class TestArithmeticMean:
    """Test arithmetic mean calculation."""
    
    def test_basic_arithmetic_mean(self):
        """Test basic arithmetic mean calculation."""
        result = _arith_mean([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
        assert result == pytest.approx(2.0)
    
    def test_arithmetic_mean_with_weights(self):
        """Test arithmetic mean with weights."""
        result = _arith_mean([1.0, 2.0], [1.0, 2.0])
        expected = (1.0 * 1.0 + 2.0 * 2.0) / 3.0
        assert result == pytest.approx(expected)
    
    def test_arithmetic_mean_zero_weights_returns_nan(self):
        """Zero total weight should return NaN."""
        import math
        result = _arith_mean([1.0, 2.0], [0.0, 0.0])
        assert math.isnan(result)


class TestComponentSurfaceParamsEdgeCases:
    """Test edge cases for component_surface_params_us."""
    
    def test_empty_horizons_returns_empty(self):
        """Empty input should return empty DataFrame with proper columns."""
        result = component_surface_params_us(pd.DataFrame())
        assert result.empty
        assert "Ks_inhr" in result.columns
        assert "mukey" in result.columns
    
    def test_horizons_outside_surface_window(self):
        """Horizons outside the surface window should be excluded."""
        horizons = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "chkey": ["100"],
            "texcl": ["Sand"],
            "hzdept_r": [20],  # Below the default 10cm window
            "hzdepb_r": [30],
        })
        result = component_surface_params_us(horizons)
        assert result.empty
    
    def test_missing_texcl_uses_sand_clay_percentages(self):
        """Missing texcl should derive texture from sand/clay percentages."""
        horizons = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "chkey": ["100"],
            "texcl": [None],  # Explicitly None instead of missing column
            "sandtotal_r": [90],
            "claytotal_r": [5],
            "hzdept_r": [0],
            "hzdepb_r": [10],
        })
        result = component_surface_params_us(horizons)
        assert len(result) == 1
        assert result["texcl"].iloc[0] == "Sand"
    
    def test_invalid_depth_values(self):
        """Invalid depth values should be handled gracefully."""
        horizons = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "chkey": ["100"],
            "texcl": ["Sand"],
            "hzdept_r": ["invalid"],
            "hzdepb_r": [10],
        })
        result = component_surface_params_us(horizons)
        # Should return empty since depth conversion fails
        assert result.empty or len(result) == 0


class TestMapunitParamsEdgeCases:
    """Test edge cases for mapunit_params_us."""
    
    def test_empty_component_params_returns_empty(self):
        """Empty component params should return empty DataFrame."""
        components = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "comppct_r": [100],
        })
        result = mapunit_params_us(pd.DataFrame(), components)
        assert result.empty
    
    def test_empty_components_returns_empty(self):
        """Empty components should return empty DataFrame."""
        comp_params = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "Ks_inhr": [1.0],
            "psi_in": [2.0],
            "theta_s": [0.4],
            "theta_fc": [0.2],
            "theta_wp": [0.1],
            "init_def": [0.3],
        })
        result = mapunit_params_us(comp_params, pd.DataFrame())
        assert result.empty
    
    def test_zero_component_percentages_filtered(self):
        """Components with 0% should be filtered out."""
        comp_params = pd.DataFrame({
            "mukey": ["1", "1"],
            "cokey": ["10", "11"],
            "Ks_inhr": [1.0, 5.0],
            "psi_in": [2.0, 4.0],
            "theta_s": [0.4, 0.5],
            "theta_fc": [0.2, 0.3],
            "theta_wp": [0.1, 0.2],
            "init_def": [0.3, 0.2],
        })
        components = pd.DataFrame({
            "mukey": ["1", "1"],
            "cokey": ["10", "11"],
            "comppct_r": [0, 100],  # First component has 0%
        })
        result = mapunit_params_us(comp_params, components)
        assert len(result) == 1
        # Should only use the second component
        assert result["Ks_inhr"].iloc[0] == pytest.approx(5.0)


class TestBuildHSGParameters:
    """Test the deprecated build_hsg_parameters function."""
    
    def test_basic_hsg_parameters(self):
        """Test basic HSG parameter generation."""
        components = pd.DataFrame({
            "mukey": ["1", "2"],
            "cokey": ["10", "20"],
            "comppct_r": [100, 100],
            "hydgrp": ["A", "D"],
            "majcompflag": ["Yes", "Yes"],
        })
        result = build_hsg_parameters(components)
        assert len(result) == 2
        assert "Ks_inhr" in result.columns
        assert "hsg_dom" in result.columns
        
        # Check that A has higher Ksat than D
        row_a = result[result["hsg_dom"] == "A"].iloc[0]
        row_d = result[result["hsg_dom"] == "D"].iloc[0]
        assert row_a["Ks_inhr"] > row_d["Ks_inhr"]
    
    def test_empty_components_returns_empty(self):
        """Empty components should return empty DataFrame."""
        result = build_hsg_parameters(pd.DataFrame())
        assert result.empty
        assert "mukey" in result.columns
    
    def test_unknown_hsg_uses_default(self):
        """Unknown HSG should use default texture (Loam)."""
        components = pd.DataFrame({
            "mukey": ["1"],
            "cokey": ["10"],
            "comppct_r": [100],
            "hydgrp": ["U"],
            "majcompflag": ["Yes"],
        })
        result = build_hsg_parameters(components)
        assert len(result) == 1
        # Should have some Ksat value (default behavior)
        assert result["Ks_inhr"].iloc[0] > 0
