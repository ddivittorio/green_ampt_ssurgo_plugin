import sys
from pathlib import Path
import json
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.processing import (
    clip_to_aoi,
    summarize_mapunit_properties,
    attach_properties,
    summarize_hsg,
    _weighted_mean,
    _parse_dual_hsg,
)


class TestClipToAOI:
    """Test clip_to_aoi spatial operations."""

    def test_basic_clipping(self):
        """Test basic polygon clipping to AOI."""
        # Create AOI (small square)
        aoi = gpd.GeoDataFrame(
            {"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        
        # Create mupolygon (larger square that overlaps)
        mupolygon = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2"],
                "geometry": [
                    Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]),
                    Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),  # Outside AOI
                ],
            },
            crs="EPSG:4326",
        )
        
        clipped = clip_to_aoi(mupolygon, aoi)
        
        # Should only keep the overlapping polygon
        assert len(clipped) == 1
        assert "1" in clipped["mukey"].values

    def test_crs_mismatch_handling(self):
        """Test that CRS mismatch is handled correctly."""
        aoi = gpd.GeoDataFrame(
            {"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        
        # Create mupolygon in different CRS
        mupolygon = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
            },
            crs="EPSG:3857",
        )
        
        clipped = clip_to_aoi(mupolygon, aoi)
        
        # Should have reprojected and clipped
        assert len(clipped) > 0
        assert clipped.crs == aoi.crs

    def test_missing_crs_raises_error(self):
        """Test that missing CRS raises ValueError."""
        aoi = gpd.GeoDataFrame(
            {"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs=None,
        )
        
        with pytest.raises(ValueError, match="mupolygon dataset lacks a CRS"):
            clip_to_aoi(mupolygon, aoi)

    def test_empty_clipping_raises_error(self):
        """Test that empty result raises ValueError."""
        aoi = gpd.GeoDataFrame(
            {"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            crs="EPSG:4326",
        )
        
        # Create mupolygon far from AOI
        mupolygon = gpd.GeoDataFrame(
            {"mukey": ["1"], "geometry": [Polygon([(10, 10), (11, 10), (11, 11), (10, 11)])]},
            crs="EPSG:4326",
        )
        
        with pytest.raises(ValueError, match="Clipping mupolygon to AOI produced an empty"):
            clip_to_aoi(mupolygon, aoi)


class TestSummarizeMapunitProperties:
    """Test summarize_mapunit_properties aggregation logic."""

    def test_basic_aggregation(self):
        """Test basic property aggregation."""
        component = pd.DataFrame(
            {
                "mukey": ["1", "1"],
                "cokey": ["10", "11"],
                "comppct_r": [60, 40],
            }
        )
        
        chorizon = pd.DataFrame(
            {
                "cokey": ["10", "10", "11", "11"],
                "hzdept_r": [0, 10, 0, 10],
                "hzdepb_r": [10, 20, 10, 20],
                "ksat_r": [5.0, 3.0, 4.0, 2.0],
                "sandtotal_r": [50.0, 40.0, 60.0, 50.0],
                "claytotal_r": [20.0, 30.0, 15.0, 25.0],
                "dbthirdbar_r": [1.5, 1.6, 1.4, 1.5],
            }
        )
        
        result = summarize_mapunit_properties(component, chorizon, depth_limit_cm=30.0)
        
        assert len(result) == 1
        assert result.iloc[0]["mukey"] == "1"
        assert "ksat" in result.columns
        assert "sand_pct" in result.columns
        assert "clay_pct" in result.columns
        assert "theta_s" in result.columns

    def test_depth_limiting(self):
        """Test that depth_limit_cm is respected."""
        component = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
            }
        )
        
        chorizon = pd.DataFrame(
            {
                "cokey": ["10", "10"],
                "hzdept_r": [0, 50],  # Second horizon is deep
                "hzdepb_r": [50, 100],
                "ksat_r": [5.0, 1.0],  # Different values
                "sandtotal_r": [50.0, 10.0],
                "claytotal_r": [20.0, 50.0],
                "dbthirdbar_r": [1.5, 1.8],
            }
        )
        
        result = summarize_mapunit_properties(component, chorizon, depth_limit_cm=10.0)
        
        # Should only use first 10cm of first horizon
        assert len(result) == 1
        # Sand percentage should be closer to top horizon value
        assert result.iloc[0]["sand_pct"] == pytest.approx(50.0, abs=5.0)

    def test_empty_input_returns_empty(self):
        """Test that empty inputs return empty DataFrame."""
        component = pd.DataFrame(columns=["mukey", "cokey", "comppct_r"])
        chorizon = pd.DataFrame(
            columns=["cokey", "hzdept_r", "hzdepb_r", "ksat_r", "sandtotal_r", "claytotal_r", "dbthirdbar_r"]
        )
        
        result = summarize_mapunit_properties(component, chorizon)
        
        assert result.empty
        assert "mukey" in result.columns

    def test_missing_mukey_handling(self):
        """Test that missing mukey in horizons is handled."""
        component = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
            }
        )
        
        # chorizon missing mukey column
        chorizon = pd.DataFrame(
            {
                "cokey": ["10"],
                "hzdept_r": [0],
                "hzdepb_r": [10],
                "ksat_r": [5.0],
                "sandtotal_r": [50.0],
                "claytotal_r": [20.0],
                "dbthirdbar_r": [1.5],
            }
        )
        
        result = summarize_mapunit_properties(component, chorizon)
        
        # Should merge mukey from component
        assert len(result) == 1
        assert result.iloc[0]["mukey"] == "1"

    def test_theta_s_calculation(self):
        """Test porosity (theta_s) calculation from bulk density."""
        component = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
            }
        )
        
        chorizon = pd.DataFrame(
            {
                "cokey": ["10"],
                "hzdept_r": [0],
                "hzdepb_r": [10],
                "ksat_r": [5.0],
                "sandtotal_r": [50.0],
                "claytotal_r": [20.0],
                "dbthirdbar_r": [1.325],  # Should give theta_s = 1 - 1.325/2.65 = 0.5
            }
        )
        
        result = summarize_mapunit_properties(component, chorizon)
        
        assert result.iloc[0]["theta_s"] == pytest.approx(0.5, abs=0.01)

    def test_theta_s_bounds(self):
        """Test that theta_s is bounded between 0 and 0.9."""
        component = pd.DataFrame(
            {
                "mukey": ["1", "2"],
                "cokey": ["10", "20"],
                "comppct_r": [100, 100],
            }
        )
        
        chorizon = pd.DataFrame(
            {
                "cokey": ["10", "20"],
                "mukey": ["1", "2"],
                "hzdept_r": [0, 0],
                "hzdepb_r": [10, 10],
                "ksat_r": [5.0, 5.0],
                "sandtotal_r": [50.0, 50.0],
                "claytotal_r": [20.0, 20.0],
                "dbthirdbar_r": [3.0, 0.1],  # One too high, one too low
            }
        )
        
        result = summarize_mapunit_properties(component, chorizon)
        
        # Should be capped at 0.9
        for _, row in result.iterrows():
            if not pd.isna(row["theta_s"]):
                assert 0.0 <= row["theta_s"] <= 0.9


class TestAttachProperties:
    """Test attach_properties joining logic."""

    def test_basic_join(self):
        """Test basic property attachment."""
        mupolygon = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2"],
                "geometry": [Point(0, 0), Point(1, 1)],
            },
            crs="EPSG:4326",
        )
        
        aggregated = pd.DataFrame(
            {
                "mukey": ["1", "2"],
                "ksat": [5.0, 3.0],
                "theta_s": [0.4, 0.5],
            }
        )
        
        result = attach_properties(mupolygon, aggregated)
        
        assert len(result) == 2
        assert "ksat" in result.columns
        assert "theta_s" in result.columns
        assert result.loc[result["mukey"] == "1", "ksat"].iloc[0] == 5.0

    def test_partial_match(self):
        """Test when not all mukeys have properties."""
        mupolygon = gpd.GeoDataFrame(
            {
                "mukey": ["1", "2", "3"],
                "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
            },
            crs="EPSG:4326",
        )
        
        aggregated = pd.DataFrame(
            {
                "mukey": ["1", "3"],
                "ksat": [5.0, 3.0],
            }
        )
        
        result = attach_properties(mupolygon, aggregated)
        
        assert len(result) == 3
        assert pd.isna(result.loc[result["mukey"] == "2", "ksat"].iloc[0])

    def test_preserves_crs(self):
        """Test that CRS is preserved."""
        mupolygon = gpd.GeoDataFrame(
            {
                "mukey": ["1"],
                "geometry": [Point(0, 0)],
            },
            crs="EPSG:4326",
        )
        
        aggregated = pd.DataFrame({"mukey": ["1"], "ksat": [5.0]})
        
        result = attach_properties(mupolygon, aggregated)
        
        assert result.crs == mupolygon.crs


class TestWeightedMean:
    """Test _weighted_mean utility function."""

    def test_basic_weighted_mean(self):
        """Test basic weighted mean calculation."""
        values = pd.Series([10.0, 20.0, 30.0])
        weights = pd.Series([1.0, 2.0, 1.0])
        
        result = _weighted_mean(values, weights)
        
        # (10*1 + 20*2 + 30*1) / (1+2+1) = 80/4 = 20
        assert result == pytest.approx(20.0)

    def test_normalized_weights(self):
        """Test weighted mean with normalization."""
        values = pd.Series([10.0, 20.0])
        weights = pd.Series([30.0, 70.0])
        
        result = _weighted_mean(values, weights, normalize=True)
        
        # 0.3 * 10 + 0.7 * 20 = 3 + 14 = 17
        assert result == pytest.approx(17.0)

    def test_handles_nan_values(self):
        """Test handling of NaN values."""
        values = pd.Series([10.0, float("nan"), 30.0])
        weights = pd.Series([1.0, 1.0, 1.0])
        
        result = _weighted_mean(values, weights)
        
        # Should skip NaN: (10*1 + 30*1) / (1+1) = 20
        assert result == pytest.approx(20.0)

    def test_zero_weights(self):
        """Test handling of zero weights."""
        values = pd.Series([10.0, 20.0, 30.0])
        weights = pd.Series([1.0, 0.0, 1.0])
        
        result = _weighted_mean(values, weights)
        
        # Should skip zero weight: (10*1 + 30*1) / (1+1) = 20
        assert result == pytest.approx(20.0)

    def test_all_weights_zero(self):
        """Test when all weights are zero."""
        values = pd.Series([10.0, 20.0, 30.0])
        weights = pd.Series([0.0, 0.0, 0.0])
        
        result = _weighted_mean(values, weights)
        
        # Should return simple mean: (10+20+30)/3 = 20
        assert result == pytest.approx(20.0)

    def test_all_nan_values(self):
        """Test when all values are NaN."""
        values = pd.Series([float("nan"), float("nan")])
        weights = pd.Series([1.0, 1.0])
        
        result = _weighted_mean(values, weights)
        
        assert pd.isna(result)


class TestParseDualHSG:
    """Test _parse_dual_hsg utility function."""

    def test_single_hsg(self):
        """Test parsing single HSG value."""
        dry, drained = _parse_dual_hsg("A")
        assert dry == "A"
        assert drained == "A"

    def test_dual_hsg(self):
        """Test parsing dual HSG value."""
        dry, drained = _parse_dual_hsg("A/D")
        assert dry == "A"
        assert drained == "D"

    def test_dual_hsg_with_backslash(self):
        """Test parsing dual HSG with backslash."""
        dry, drained = _parse_dual_hsg("C\\D")
        assert dry == "C"
        assert drained == "D"

    def test_none_value(self):
        """Test parsing None value."""
        dry, drained = _parse_dual_hsg(None)
        assert dry == "U"
        assert drained == "U"

    def test_nan_value(self):
        """Test parsing NaN value."""
        dry, drained = _parse_dual_hsg(float("nan"))
        assert dry == "U"
        assert drained == "U"

    def test_empty_string(self):
        """Test parsing empty string."""
        dry, drained = _parse_dual_hsg("")
        assert dry == "U"
        assert drained == "U"

    def test_lowercase_normalization(self):
        """Test that values are normalized to uppercase."""
        dry, drained = _parse_dual_hsg("b/d")
        assert dry == "B"
        assert drained == "D"


class TestSummarizeHSG:
    """Test summarize_hsg aggregation logic."""

    def test_basic_hsg_summary(self):
        """Test basic HSG summarization."""
        components = pd.DataFrame(
            {
                "mukey": ["1", "1"],
                "cokey": ["10", "11"],
                "comppct_r": [70, 30],
                "hydgrp": ["A", "B"],
                "majcompflag": ["Yes", "No"],
            }
        )
        
        result = summarize_hsg(components)
        
        assert len(result) == 1
        assert result.iloc[0]["mukey"] == "1"
        assert result.iloc[0]["hsg_dom"] == "A"
        assert result.iloc[0]["hsg_dry"] == "A"

    def test_dual_hsg_handling(self):
        """Test dual HSG handling."""
        components = pd.DataFrame(
            {
                "mukey": ["1"],
                "cokey": ["10"],
                "comppct_r": [100],
                "hydgrp": ["C/D"],
                "majcompflag": ["Yes"],
            }
        )
        
        result = summarize_hsg(components)
        
        assert result.iloc[0]["hsg_dom"] == "C"
        assert result.iloc[0]["hsg_dry"] == "C"
        assert result.iloc[0]["hsg_drained"] == "D"

    def test_hsg_composition_percentages(self):
        """Test HSG composition percentages."""
        components = pd.DataFrame(
            {
                "mukey": ["1", "1", "1"],
                "cokey": ["10", "11", "12"],
                "comppct_r": [50, 30, 20],
                "hydgrp": ["A", "B", "C"],
                "majcompflag": ["Yes", "No", "No"],
            }
        )
        
        result = summarize_hsg(components)
        
        comp = json.loads(result.iloc[0]["hsg_comp"])
        assert comp["A"] == 50
        assert comp["B"] == 30
        assert comp["C"] == 20

    def test_major_component_prioritization(self):
        """Test that major components are prioritized when percentages are equal."""
        components = pd.DataFrame(
            {
                "mukey": ["1", "1"],
                "cokey": ["10", "11"],
                "comppct_r": [50, 50],  # Equal percentages
                "hydgrp": ["A", "B"],
                "majcompflag": ["Yes", "No"],  # Major flag should be tiebreaker
            }
        )
        
        result = summarize_hsg(components)
        
        # Should pick A because it's marked as major component (tiebreaker)
        assert result.iloc[0]["hsg_dom"] == "A"

    def test_empty_input(self):
        """Test empty input."""
        components = pd.DataFrame(columns=["mukey", "cokey", "comppct_r", "hydgrp", "majcompflag"])
        
        result = summarize_hsg(components)
        
        assert result.empty
        assert "mukey" in result.columns
        assert "hsg_dom" in result.columns
