from __future__ import annotations

import json
from typing import Dict, Optional, TYPE_CHECKING

import math
import numpy as np

from ._compat import require_pandas

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


GA_TABLE_US: Dict[str, Dict[str, float]] = {
    "Sand": {
        "ks_inhr": 4.74,
        "psi_in": 1.93,
        "theta_s": 0.437,
        "theta_fc": 0.062,
        "theta_wp": 0.024,
        "init_def": 0.413,
    },
    "Loamy Sand": {
        "ks_inhr": 1.18,
        "psi_in": 2.40,
        "theta_s": 0.437,
        "theta_fc": 0.105,
        "theta_wp": 0.047,
        "init_def": 0.390,
    },
    "Sandy Loam": {
        "ks_inhr": 0.43,
        "psi_in": 4.33,
        "theta_s": 0.453,
        "theta_fc": 0.190,
        "theta_wp": 0.085,
        "init_def": 0.368,
    },
    "Loam": {
        "ks_inhr": 0.13,
        "psi_in": 3.50,
        "theta_s": 0.463,
        "theta_fc": 0.232,
        "theta_wp": 0.116,
        "init_def": 0.347,
    },
    "Silt Loam": {
        "ks_inhr": 0.26,
        "psi_in": 6.69,
        "theta_s": 0.501,
        "theta_fc": 0.284,
        "theta_wp": 0.135,
        "init_def": 0.366,
    },
    "Sandy Clay Loam": {
        "ks_inhr": 0.06,
        "psi_in": 8.66,
        "theta_s": 0.398,
        "theta_fc": 0.244,
        "theta_wp": 0.136,
        "init_def": 0.262,
    },
    "Clay Loam": {
        "ks_inhr": 0.04,
        "psi_in": 8.27,
        "theta_s": 0.464,
        "theta_fc": 0.310,
        "theta_wp": 0.187,
        "init_def": 0.277,
    },
    "Silty Clay Loam": {
        "ks_inhr": 0.04,
        "psi_in": 10.63,
        "theta_s": 0.471,
        "theta_fc": 0.342,
        "theta_wp": 0.210,
        "init_def": 0.261,
    },
    "Sandy Clay": {
        "ks_inhr": 0.02,
        "psi_in": 9.45,
        "theta_s": 0.430,
        "theta_fc": 0.321,
        "theta_wp": 0.221,
        "init_def": 0.209,
    },
    "Silty Clay": {
        "ks_inhr": 0.02,
        "psi_in": 11.42,
        "theta_s": 0.479,
        "theta_fc": 0.371,
        "theta_wp": 0.251,
        "init_def": 0.228,
    },
    "Clay": {
        "ks_inhr": 0.01,
        "psi_in": 12.60,
        "theta_s": 0.475,
        "theta_fc": 0.378,
        "theta_wp": 0.265,
        "init_def": 0.210,
    },
}

# HSG-based Ksat lookup table (mm/hr)
# Source: NRCS Hydrology National Engineering Handbook, Chapter 7
# and Green-Ampt_SWMM_Parameters.PDF
HSG_KSAT_RANGES_INHR: Dict[str, Dict[str, float]] = {
    # Saturated Hydraulic Conductivity (in/hr) from NEH, Chapter 7
    "A": {"min": 0.45, "max": float("inf")},
    "B": {"min": 0.15, "max": 0.30},
    "C": {"min": 0.05, "max": 0.15},
    "D": {"min": 0.00, "max": 0.05},
}

# HSG-based representative values for Green-Ampt parameters
# These represent typical/median values for each HSG category
# Source: NRCS Hydrology National Engineering Handbook and Green-Ampt SWMM Parameters
HSG_KSAT_TABLE: Dict[str, Dict[str, float]] = {
    "A": {"ks_inhr": 0.45},  # Minimum of HSG A range (conservative)
    "B": {"ks_inhr": 0.22},  # Midpoint of 0.15-0.30 range
    "C": {"ks_inhr": 0.10},  # Midpoint of 0.05-0.15 range
    "D": {"ks_inhr": 0.025}, # Midpoint of 0.00-0.05 range
}


_ALIAS = {texture.lower(): texture for texture in GA_TABLE_US}


def _norm_texcl(texture: Optional[str]) -> Optional[str]:
    if texture is None:
        return None
    return _ALIAS.get(str(texture).strip().lower())


def _derive_texcl_from_percentages(sand: Optional[float], clay: Optional[float]) -> Optional[str]:
    """Infer a USDA textural class using sand and clay percentages."""

    try:
        sand_val = float(sand) if sand is not None else float("nan")
    except (TypeError, ValueError):
        sand_val = float("nan")
    try:
        clay_val = float(clay) if clay is not None else float("nan")
    except (TypeError, ValueError):
        clay_val = float("nan")

    if math.isnan(sand_val) or math.isnan(clay_val):
        return None

    sand_val = max(0.0, min(100.0, sand_val))
    clay_val = max(0.0, min(100.0, clay_val))
    silt_val = max(0.0, min(100.0, 100.0 - sand_val - clay_val))

    total = sand_val + silt_val + clay_val
    if total <= 0:
        return None

    sand_pct = sand_val / total * 100.0
    clay_pct = clay_val / total * 100.0
    silt_pct = silt_val / total * 100.0

    if sand_pct >= 85.0 and clay_pct <= 10.0 and silt_pct <= 15.0:
        return "Sand"
    if sand_pct >= 70.0 and sand_pct < 90.0 and clay_pct <= 15.0 and silt_pct <= 30.0:
        return "Loamy Sand"
    if silt_pct >= 80.0 and clay_pct < 12.0:
        return "Silt Loam"
    if clay_pct >= 40.0:
        if silt_pct >= 40.0:
            return "Silty Clay"
        if sand_pct >= 45.0:
            return "Sandy Clay"
        return "Clay"
    if clay_pct >= 35.0:
        if sand_pct >= 45.0:
            return "Sandy Clay"
        if silt_pct >= 40.0:
            return "Silty Clay"
        return "Clay"
    if clay_pct >= 27.0:
        if sand_pct >= 45.0:
            return "Sandy Clay Loam"
        if silt_pct >= 40.0:
            return "Silty Clay Loam"
        return "Clay Loam"
    if clay_pct >= 20.0:
        if sand_pct >= 52.0:
            return "Sandy Clay Loam"
        if silt_pct >= 50.0:
            return "Silty Clay Loam"
        return "Clay Loam"
    if clay_pct >= 7.0:
        if sand_pct >= 70.0 and clay_pct < 15.0 and silt_pct <= 30.0:
            return "Loamy Sand"
        if sand_pct >= 52.0 and silt_pct < 50.0:
            return "Sandy Loam"
        if silt_pct >= 50.0:
            return "Silt Loam"
        if 23.0 <= sand_pct < 52.0 and 28.0 <= silt_pct < 50.0:
            return "Loam"
        return "Sandy Loam"
    if sand_pct >= 43.0 and silt_pct < 50.0:
        return "Sandy Loam"
    if silt_pct >= 50.0:
        return "Silt Loam"
    if 23.0 <= sand_pct < 52.0 and 28.0 <= silt_pct < 50.0:
        return "Loam"
    return "Loam"


def _harmonic_mean(values, weights) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    mask = (value_array > 0) & (weight_array > 0)
    if not np.any(mask):
        return float("nan")
    value_array = value_array[mask]
    weight_array = weight_array[mask]
    return float(weight_array.sum() / (weight_array / value_array).sum())


def _arith_mean(values, weights) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    total_weight = weight_array.sum()
    if total_weight <= 0:
        return float("nan")
    return float(np.nansum(weight_array * value_array) / total_weight)


def _top_texture(group) -> Optional[str]:
    if group.empty:
        return None
    ordered = group.sort_values("t_top", kind="mergesort")
    for _, row in ordered.iterrows():
        tex = row.get("tex_norm")
        if tex:
            return tex
    return None


def component_surface_params_us(
    horizons_tex, surface_top_cm: float = 0.0, surface_bot_cm: float = 10.0
):
    """Aggregate horizons within a surface window for each component."""

    pandas = require_pandas()
    df = pandas.DataFrame(horizons_tex).copy()
    if df.empty:
        return pandas.DataFrame(
            columns=[
                "mukey",
                "cokey",
                "Ks_inhr",
                "psi_in",
                "theta_s",
                "theta_fc",
                "theta_wp",
                "init_def",
                "texcl",
            ]
        )

    for column in ("mukey", "cokey"):
        if column in df.columns:
            df[column] = df[column].astype(str)

    df["hzdept_r"] = pandas.to_numeric(df.get("hzdept_r"), errors="coerce")
    df["hzdepb_r"] = pandas.to_numeric(df.get("hzdepb_r"), errors="coerce")

    df["t_top"] = df["hzdept_r"].clip(lower=surface_top_cm)
    df["t_bot"] = df["hzdepb_r"].clip(upper=surface_bot_cm)
    df["thick"] = (df["t_bot"] - df["t_top"]).clip(lower=0)
    df = df[df["thick"] > 0].copy()
    if df.empty:
        return pandas.DataFrame(
            columns=[
                "mukey",
                "cokey",
                "Ks_inhr",
                "psi_in",
                "theta_s",
                "theta_fc",
                "theta_wp",
                "init_def",
                "texcl",
            ]
        )

    df["tex_norm"] = df.get("texcl").apply(_norm_texcl)

    # Fallback: derive texture from sand/clay percentages if texcl is missing
    missing_texcl = df["tex_norm"].isna()
    if missing_texcl.any():
        derived_texcl = df.loc[missing_texcl].apply(
            lambda row: _derive_texcl_from_percentages(row.get("sandtotal_r"), row.get("claytotal_r")),
            axis=1,
        )
        df.loc[missing_texcl, "tex_norm"] = derived_texcl.apply(_norm_texcl)

    df = df[~df["tex_norm"].isna()].copy()
    if df.empty:
        return pandas.DataFrame(
            columns=[
                "mukey",
                "cokey",
                "Ks_inhr",
                "psi_in",
                "theta_s",
                "theta_fc",
                "theta_wp",
                "init_def",
                "texcl",
            ]
        )

    for column in ("ks_inhr", "psi_in", "theta_s", "theta_fc", "theta_wp", "init_def"):
        df[column] = df["tex_norm"].map(lambda name: GA_TABLE_US[name][column])

    records = []
    for (mukey, cokey), group in df.groupby(["mukey", "cokey"], sort=False):
        weights = group["thick"].to_numpy(dtype=float)
        record = {
            "mukey": mukey,
            "cokey": cokey,
            "Ks_inhr": _harmonic_mean(group["ks_inhr"].to_numpy(), weights),
            "psi_in": _arith_mean(group["psi_in"].to_numpy(), weights),
            "theta_s": _arith_mean(group["theta_s"].to_numpy(), weights),
            "theta_fc": _arith_mean(group["theta_fc"].to_numpy(), weights),
            "theta_wp": _arith_mean(group["theta_wp"].to_numpy(), weights),
            "init_def": _arith_mean(group["init_def"].to_numpy(), weights),
            "texcl": _top_texture(group),
        }
        records.append(record)

    return pandas.DataFrame.from_records(records)


def mapunit_params_us(component_params, components):
    pandas = require_pandas()
    comp = pandas.DataFrame(component_params).copy()
    if comp.empty:
        return pandas.DataFrame(
            columns=[
                "mukey",
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
                "texcl",
            ]
        )

    comp["mukey"] = comp["mukey"].astype(str)
    comp["cokey"] = comp["cokey"].astype(str)

    weights = pandas.DataFrame(components).copy()
    if weights.empty:
        return pandas.DataFrame(columns=comp.columns)

    weights["mukey"] = weights["mukey"].astype(str)
    weights["cokey"] = weights["cokey"].astype(str)
    weights["comppct_r"] = pandas.to_numeric(weights.get("comppct_r"), errors="coerce").fillna(0.0)

    weights = weights[weights["comppct_r"] > 0]
    if weights.empty:
        return pandas.DataFrame(columns=comp.columns)

    totals = weights.groupby("mukey", sort=False)["comppct_r"].transform(lambda series: series.sum() if series.sum() > 0 else 1.0)
    weights["w"] = weights["comppct_r"] / totals

    merged = comp.merge(weights[["mukey", "cokey", "w"]], on=["mukey", "cokey"], how="inner")
    if merged.empty:
        return pandas.DataFrame(columns=comp.columns)

    numeric_cols = ["Ks_inhr", "psi_in", "theta_s", "theta_fc", "theta_wp", "init_def"]
    for column in numeric_cols:
        merged[f"{column}_weighted"] = merged[column].astype(float) * merged["w"].astype(float)

    weighted_cols = [f"{column}_weighted" for column in numeric_cols]
    pandas = require_pandas()
    result = (
        merged.groupby("mukey", sort=False)[weighted_cols]
        .sum(min_count=1)
        .rename(columns={f"{column}_weighted": column for column in numeric_cols})
        .reset_index()
    )

    result["theta_i_design"] = result["theta_fc"]
    result["theta_i_cont"] = result["theta_s"] - result["init_def"]
    result["dtheta_design"] = result["theta_s"] - result["theta_i_design"]
    result["dtheta_cont"] = result["theta_s"] - result["theta_i_cont"]

    if "texcl" in merged.columns:
        dominant = (
            merged.sort_values("w", ascending=False, kind="mergesort")
            .drop_duplicates("mukey")
            .set_index("mukey")["texcl"]
        )
        result = result.merge(dominant, on="mukey", how="left")
    else:
        result["texcl"] = None

    return result


    return result


def build_hsg_parameters(components_df):
    """DEPRECATED: This function uses a simplified HSG mapping and will be removed."""
    pandas = require_pandas()
    from .processing import summarize_hsg
    
    components = pandas.DataFrame(components_df).copy()
    if components.empty:
        return pandas.DataFrame(
            columns=[
                "mukey",
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
            ]
        )
    
    # Get HSG summary
    hsg_summary = summarize_hsg(components)
    
    # Map HSG to representative texture for other parameters
    hsg_to_texture = {
        "A": "Sand",
        "B": "Loam",
        "C": "Clay Loam",
        "D": "Clay",
        "U": "Loam",  # Default to Loam for unknown
    }
    
    records = []
    for _, row in hsg_summary.iterrows():
        mukey = row["mukey"]
        hsg_dom = row["hsg_dom"]
        
        # Get Ksat from HSG table
        ks_inhr = HSG_KSAT_RANGES_INHR.get(hsg_dom, {"min": 0.10, "max": 0.10})["min"]
        
        # Get other parameters from texture table
        texture = hsg_to_texture.get(hsg_dom, "Loam")
        texture_params = GA_TABLE_US[texture]
        
        record = {
            "mukey": mukey,
            "Ks_inhr": ks_inhr,
            "psi_in": texture_params["psi_in"],
            "theta_s": texture_params["theta_s"],
            "theta_fc": texture_params["theta_fc"],
            "theta_wp": texture_params["theta_wp"],
            "init_def": texture_params["init_def"],
            "hsg_dom": row["hsg_dom"],
            "hsg_dry": row["hsg_dry"],
            "hsg_drained": row["hsg_drained"],
            "hsg_comp": row["hsg_comp"],
        }
        
        # Calculate initial moisture content and deficit
        record["theta_i_design"] = record["theta_fc"]
        record["theta_i_cont"] = record["theta_s"] - record["init_def"]
        record["dtheta_design"] = record["theta_s"] - record["theta_i_design"]
        record["dtheta_cont"] = record["theta_s"] - record["theta_i_cont"]
        
        records.append(record)
    
    return pandas.DataFrame.from_records(records)

