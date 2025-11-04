import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from green_ampt_tool.lookup import component_surface_params_us, mapunit_params_us
from green_ampt_tool.parameters import build_lookup_parameters
from green_ampt_tool.processing import summarize_hsg


def test_harmonic_vs_arithmetic():
    horizons = pd.DataFrame(
        {
            "mukey": ["1", "1"],
            "cokey": ["10", "10"],
            "chkey": ["100", "101"],
            "texcl": ["Sand", "Clay"],
            "hzdept_r": [0, 5],
            "hzdepb_r": [5, 10],
        }
    )

    comp = component_surface_params_us(horizons, surface_top_cm=0.0, surface_bot_cm=10.0)
    ks = comp.loc[(comp["mukey"] == "1") & (comp["cokey"] == "10"), "Ks_inhr"].iloc[0]
    assert ks < 0.2


def test_mapunit_weights():
    comp = pd.DataFrame(
        {
            "mukey": ["1", "1"],
            "cokey": ["10", "11"],
            "Ks_inhr": [1.0, 5.0],
            "psi_in": [4.0, 8.0],
            "theta_s": [0.4, 0.5],
            "theta_fc": [0.2, 0.3],
            "theta_wp": [0.1, 0.2],
            "init_def": [0.3, 0.25],
            "texcl": ["Sand", "Loam"],
        }
    )
    components = pd.DataFrame(
        {
            "mukey": ["1", "1"],
            "cokey": ["10", "11"],
            "comppct_r": [30, 70],
        }
    )
    mu = mapunit_params_us(comp, components)
    row = mu.iloc[0]
    assert row["Ks_inhr"] == pytest.approx(0.3 * 1.0 + 0.7 * 5.0)
    assert row["psi_in"] == pytest.approx(0.3 * 4.0 + 0.7 * 8.0)
    assert row["theta_s"] == pytest.approx(0.3 * 0.4 + 0.7 * 0.5)


def test_dual_hsg_parsing():
    components = pd.DataFrame(
        {
            "mukey": ["1", "1", "2"],
            "cokey": ["10", "11", "20"],
            "comppct_r": [60, 40, 100],
            "hydgrp": ["A/D", "B", "C/D"],
            "majcompflag": ["Yes", "No", "Yes"],
        }
    )
    summary = summarize_hsg(components)
    aoi = summary.set_index("mukey")
    row1 = aoi.loc["1"]
    assert row1["hsg_dom"] == "A"
    comp = json.loads(row1["hsg_comp"])
    assert comp["A"] == 60
    assert comp["B"] == 40
    row2 = aoi.loc["2"]
    assert row2["hsg_dom"] == "C"
    assert row2["hsg_drained"] == "D"


def test_lookup_loam_units_and_theta_relationships():
    horizons = pd.DataFrame(
        {
            "cokey": ["10"],
            "chkey": ["100"],
            "texcl": ["Loam"],
            "hzdept_r": [0.0],
            "hzdepb_r": [10.0],
        }
    )
    components = pd.DataFrame(
        {
            "mukey": ["1"],
            "cokey": ["10"],
            "comppct_r": [100],
            "hydgrp": ["A/D"],
            "majcompflag": ["Yes"],
        }
    )
    params = build_lookup_parameters(components, horizons)
    assert len(params) == 1
    row = params.iloc[0]
    assert row["Ks_inhr"] == pytest.approx(0.13, rel=1e-6)
    assert row["psi_in"] == pytest.approx(3.50, rel=1e-6)
    assert row["theta_i_cont"] == pytest.approx(row["theta_s"] - row["init_def"], rel=1e-6)
    assert row["dtheta_cont"] == pytest.approx(row["theta_s"] - row["theta_i_cont"], rel=1e-6)
    assert json.loads(row["hsg_comp"])["A"] == 100
    assert row["hsg_drained"] == "D"


def test_hsg_based_parameter_estimation():
    """Test HSG-based parameter estimation using hydrologic soil groups."""
    from green_ampt_tool.parameters import build_hsg_lookup_parameters
    from green_ampt_tool.lookup import HSG_KSAT_TABLE
    
    components = pd.DataFrame(
        {
            "mukey": ["1", "1", "2", "3", "4"],
            "cokey": ["10", "11", "20", "30", "40"],
            "comppct_r": [70, 30, 100, 100, 100],
            "hydgrp": ["A", "B", "C/D", "D", "B/D"],
            "majcompflag": ["Yes", "No", "Yes", "Yes", "Yes"],
        }
    )
    
    # Create minimal horizons data for each component
    horizons = pd.DataFrame(
        {
            "cokey": ["10", "11", "20", "30", "40"],
            "chkey": ["100", "110", "200", "300", "400"],
            "texcl": ["Sand", "Loam", "Clay Loam", "Clay", "Loam"],
            "hzdept_r": [0, 0, 0, 0, 0],
            "hzdepb_r": [10, 10, 10, 10, 10],
        }
    )
    
    params = build_hsg_lookup_parameters(components, horizons)
    
    # Should have 4 mapunits
    assert len(params) == 4
    
    # Check HSG A parameters
    row_a = params[params["hsg_dom"] == "A"].iloc[0]
    assert row_a["Ks_inhr"] == HSG_KSAT_TABLE["A"]["ks_inhr"]
    assert row_a["Ks_inhr"] == pytest.approx(0.45, rel=1e-6)
    
    # Check HSG C parameters (uses undrained HSG from C/D)
    row_c = params[params["hsg_dom"] == "C"].iloc[0]
    assert row_c["Ks_inhr"] == HSG_KSAT_TABLE["C"]["ks_inhr"]
    assert row_c["Ks_inhr"] == pytest.approx(0.10, rel=1e-6)
    assert row_c["hsg_drained"] == "D"
    
    # Check HSG D parameters
    row_d = params[params["hsg_dom"] == "D"].iloc[0]
    assert row_d["Ks_inhr"] == HSG_KSAT_TABLE["D"]["ks_inhr"]
    assert row_d["Ks_inhr"] == pytest.approx(0.025, rel=1e-6)
    
    # Verify ordering: A > B > C > D for Ksat
    assert row_a["Ks_inhr"] > params[params["hsg_dom"] == "B"]["Ks_inhr"].iloc[0]
    assert params[params["hsg_dom"] == "B"]["Ks_inhr"].iloc[0] > row_c["Ks_inhr"]
    assert row_c["Ks_inhr"] > row_d["Ks_inhr"]
    
    # Check that initial moisture parameters are calculated
    for _, row in params.iterrows():
        assert "theta_i_design" in params.columns
        assert "theta_i_cont" in params.columns
        assert "dtheta_design" in params.columns
        assert "dtheta_cont" in params.columns
        assert row["theta_i_design"] == pytest.approx(row["theta_fc"], rel=1e-6)
        assert row["theta_i_cont"] == pytest.approx(row["theta_s"] - row["init_def"], rel=1e-6)
