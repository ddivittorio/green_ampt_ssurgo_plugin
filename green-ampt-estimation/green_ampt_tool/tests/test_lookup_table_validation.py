"""
Test suite to validate and protect lookup table definitions.

These tests ensure that critical lookup tables (GA_TABLE_US, HSG_KSAT_RANGES_INHR,
HSG_KSAT_TABLE) maintain their expected values and structure. Any changes to these
tables should be reviewed carefully as they affect all Green-Ampt parameter estimates.

The values in these tables are based on peer-reviewed literature and NRCS standards:
- Rawls et al. (1983) for texture-based parameters
- NRCS National Engineering Handbook Chapter 7 for HSG ranges
- Green-Ampt SWMM Parameters documentation
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.lookup import GA_TABLE_US, HSG_KSAT_RANGES_INHR, HSG_KSAT_TABLE


class TestGATableUSValidation:
    """Validate the GA_TABLE_US texture-based lookup table."""
    
    def test_table_has_all_expected_texture_classes(self):
        """Ensure all 11 USDA texture classes are present."""
        expected_classes = [
            "Sand", "Loamy Sand", "Sandy Loam", "Loam", "Silt Loam",
            "Sandy Clay Loam", "Clay Loam", "Silty Clay Loam",
            "Sandy Clay", "Silty Clay", "Clay"
        ]
        assert set(GA_TABLE_US.keys()) == set(expected_classes)
    
    def test_each_texture_has_required_parameters(self):
        """Ensure each texture class has all required parameters."""
        required_params = ["ks_inhr", "psi_in", "theta_s", "theta_fc", "theta_wp", "init_def"]
        for texture, params in GA_TABLE_US.items():
            assert set(params.keys()) == set(required_params), f"{texture} missing parameters"
    
    def test_parameter_values_are_positive(self):
        """All parameter values should be positive numbers."""
        for texture, params in GA_TABLE_US.items():
            for param, value in params.items():
                assert value > 0, f"{texture}.{param} is not positive: {value}"
    
    def test_theta_relationships(self):
        """Validate theta_s > theta_fc > theta_wp for all textures."""
        for texture, params in GA_TABLE_US.items():
            assert params["theta_s"] > params["theta_fc"], f"{texture}: theta_s not > theta_fc"
            assert params["theta_fc"] > params["theta_wp"], f"{texture}: theta_fc not > theta_wp"
            assert params["theta_s"] <= 1.0, f"{texture}: theta_s > 1.0"
            assert params["theta_wp"] >= 0.0, f"{texture}: theta_wp < 0.0"
    
    def test_init_def_reasonable(self):
        """Initial deficit should be less than porosity."""
        for texture, params in GA_TABLE_US.items():
            assert params["init_def"] < params["theta_s"], f"{texture}: init_def >= theta_s"
            assert params["init_def"] > 0, f"{texture}: init_def <= 0"
    
    def test_ksat_ordering_by_texture(self):
        """Verify general Ksat ordering: Sand > Loamy Sand > ... > Clay."""
        # Sand should have highest Ksat
        assert GA_TABLE_US["Sand"]["ks_inhr"] > GA_TABLE_US["Loamy Sand"]["ks_inhr"]
        assert GA_TABLE_US["Loamy Sand"]["ks_inhr"] > GA_TABLE_US["Sandy Loam"]["ks_inhr"]
        
        # Clay should have lowest Ksat
        assert GA_TABLE_US["Clay"]["ks_inhr"] < GA_TABLE_US["Silty Clay"]["ks_inhr"]
        assert GA_TABLE_US["Clay"]["ks_inhr"] < GA_TABLE_US["Sandy Clay"]["ks_inhr"]
    
    def test_specific_reference_values(self):
        """Validate specific values from Rawls et al. (1983)."""
        # These are the published reference values that should not change
        sand = GA_TABLE_US["Sand"]
        assert sand["ks_inhr"] == pytest.approx(4.74, rel=1e-6)
        assert sand["psi_in"] == pytest.approx(1.93, rel=1e-6)
        assert sand["theta_s"] == pytest.approx(0.437, rel=1e-6)
        
        loam = GA_TABLE_US["Loam"]
        assert loam["ks_inhr"] == pytest.approx(0.13, rel=1e-6)
        assert loam["psi_in"] == pytest.approx(3.50, rel=1e-6)
        assert loam["theta_s"] == pytest.approx(0.463, rel=1e-6)
        
        clay = GA_TABLE_US["Clay"]
        assert clay["ks_inhr"] == pytest.approx(0.01, rel=1e-6)
        assert clay["psi_in"] == pytest.approx(12.60, rel=1e-6)
        assert clay["theta_s"] == pytest.approx(0.475, rel=1e-6)


class TestHSGKsatRangesValidation:
    """Validate the HSG_KSAT_RANGES_INHR table."""
    
    def test_all_hsg_groups_present(self):
        """Ensure all four HSG groups are defined."""
        assert set(HSG_KSAT_RANGES_INHR.keys()) == {"A", "B", "C", "D"}
    
    def test_each_hsg_has_min_max(self):
        """Each HSG should have min and max values."""
        for hsg, ranges in HSG_KSAT_RANGES_INHR.items():
            assert "min" in ranges
            assert "max" in ranges
    
    def test_min_less_than_or_equal_max(self):
        """Min should be <= max for all HSG groups."""
        for hsg, ranges in HSG_KSAT_RANGES_INHR.items():
            assert ranges["min"] <= ranges["max"], f"HSG {hsg}: min > max"
    
    def test_hsg_ranges_are_ordered(self):
        """HSG A should have highest Ksat, D lowest."""
        # A > B > C > D in terms of minimum Ksat
        assert HSG_KSAT_RANGES_INHR["A"]["min"] > HSG_KSAT_RANGES_INHR["B"]["min"]
        assert HSG_KSAT_RANGES_INHR["B"]["min"] > HSG_KSAT_RANGES_INHR["C"]["min"]
        assert HSG_KSAT_RANGES_INHR["C"]["min"] > HSG_KSAT_RANGES_INHR["D"]["min"]
    
    def test_hsg_reference_values(self):
        """Validate specific reference values from NRCS NEH Chapter 7."""
        assert HSG_KSAT_RANGES_INHR["A"]["min"] == pytest.approx(0.45, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["B"]["min"] == pytest.approx(0.15, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["B"]["max"] == pytest.approx(0.30, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["C"]["min"] == pytest.approx(0.05, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["C"]["max"] == pytest.approx(0.15, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["D"]["min"] == pytest.approx(0.00, rel=1e-6)
        assert HSG_KSAT_RANGES_INHR["D"]["max"] == pytest.approx(0.05, rel=1e-6)
    
    def test_non_overlapping_ranges(self):
        """HSG ranges should not overlap (except at boundaries)."""
        # B max should equal or be less than A min, etc.
        assert HSG_KSAT_RANGES_INHR["B"]["max"] <= HSG_KSAT_RANGES_INHR["A"]["min"]
        assert HSG_KSAT_RANGES_INHR["C"]["max"] <= HSG_KSAT_RANGES_INHR["B"]["min"]
        assert HSG_KSAT_RANGES_INHR["D"]["max"] <= HSG_KSAT_RANGES_INHR["C"]["min"]


class TestHSGKsatTableValidation:
    """Validate the HSG_KSAT_TABLE representative values."""
    
    def test_all_hsg_groups_present(self):
        """Ensure all four HSG groups are defined."""
        assert set(HSG_KSAT_TABLE.keys()) == {"A", "B", "C", "D"}
    
    def test_each_hsg_has_ks_inhr(self):
        """Each HSG should have a ks_inhr value."""
        for hsg, params in HSG_KSAT_TABLE.items():
            assert "ks_inhr" in params
            assert params["ks_inhr"] > 0
    
    def test_values_within_valid_ranges(self):
        """Representative values should fall within their respective HSG ranges."""
        for hsg, params in HSG_KSAT_TABLE.items():
            ks_value = params["ks_inhr"]
            range_min = HSG_KSAT_RANGES_INHR[hsg]["min"]
            range_max = HSG_KSAT_RANGES_INHR[hsg]["max"]
            assert range_min <= ks_value <= range_max, f"HSG {hsg}: {ks_value} not in [{range_min}, {range_max}]"
    
    def test_hsg_ordering(self):
        """HSG A should have highest representative Ksat, D lowest."""
        assert HSG_KSAT_TABLE["A"]["ks_inhr"] > HSG_KSAT_TABLE["B"]["ks_inhr"]
        assert HSG_KSAT_TABLE["B"]["ks_inhr"] > HSG_KSAT_TABLE["C"]["ks_inhr"]
        assert HSG_KSAT_TABLE["C"]["ks_inhr"] > HSG_KSAT_TABLE["D"]["ks_inhr"]
    
    def test_specific_reference_values(self):
        """Validate the specific representative values chosen."""
        assert HSG_KSAT_TABLE["A"]["ks_inhr"] == pytest.approx(0.45, rel=1e-6)
        assert HSG_KSAT_TABLE["B"]["ks_inhr"] == pytest.approx(0.22, rel=1e-6)
        assert HSG_KSAT_TABLE["C"]["ks_inhr"] == pytest.approx(0.10, rel=1e-6)
        assert HSG_KSAT_TABLE["D"]["ks_inhr"] == pytest.approx(0.025, rel=1e-6)


class TestLookupTableConsistency:
    """Test consistency between different lookup tables."""
    
    def test_texture_ksat_generally_aligns_with_hsg(self):
        """Coarse textures should generally have higher Ksat than fine textures."""
        # Sand (coarse) should be in HSG A or B range
        sand_ks = GA_TABLE_US["Sand"]["ks_inhr"]
        assert sand_ks >= HSG_KSAT_RANGES_INHR["A"]["min"]
        
        # Clay (fine) should be in HSG C or D range
        clay_ks = GA_TABLE_US["Clay"]["ks_inhr"]
        assert clay_ks <= HSG_KSAT_RANGES_INHR["C"]["max"]
    
    def test_no_table_is_empty(self):
        """All lookup tables should have entries."""
        assert len(GA_TABLE_US) > 0
        assert len(HSG_KSAT_RANGES_INHR) > 0
        assert len(HSG_KSAT_TABLE) > 0
    
    def test_table_immutability_warning(self):
        """Document that these tables should not be modified without review.
        
        This test always passes but serves as documentation that any changes
        to the lookup tables require:
        1. Literature review and justification
        2. Update to this test file with new expected values
        3. Documentation of the change in CHANGELOG or similar
        """
        # This test documents the requirement for careful review
        # If you're modifying lookup tables and this test fails,
        # you need to update the expected values in this test file
        # AND document why the change is being made.
        assert True, "Lookup table changes require careful review and documentation"
