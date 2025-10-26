from __future__ import annotations

import math
from typing import Callable, Dict, Iterable, Literal, Optional

from ._compat import gpd, require_geopandas, require_pandas
from .lookup import component_surface_params_us, mapunit_params_us, build_hsg_parameters
from .processing import summarize_hsg

InitialDeficitMode = Literal["design", "continuous"]


def default_wetting_front_suction(sand_percentage: float, clay_percentage: float) -> float:
    """Simple pedotransfer approximation for the wetting front suction head."""

    sand = _clamp_percentage(sand_percentage)
    clay = _clamp_percentage(clay_percentage)
    return float(20.0 * (sand / 100.0) + 10.0 * (clay / 100.0))


def enrich_with_green_ampt_parameters(
    soils: "gpd.GeoDataFrame",
    suction_fn: Callable[[float, float], float] = default_wetting_front_suction,
    initial_theta: float = 0.2,
) -> "gpd.GeoDataFrame":
    geopandas = require_geopandas()
    frame = soils.copy()

    _ensure_column(frame, "ksat", ["ksat_avg"], default_value=0.0)
    _ensure_column(frame, "theta_s", ["porosity_avg"], default_value=0.45)
    _ensure_column(frame, "sand_pct", ["sand_avg"], default_value=0.0)
    _ensure_column(frame, "clay_pct", ["clay_avg"], default_value=0.0)

    frame["theta_s"] = [
        max(0.0, min(0.9, value if value is not None else 0.45))
        for value in (_safe_float(v) for v in frame["theta_s"])
    ]

    frame["psi"] = frame.apply(
        lambda row: suction_fn(
            _clamp_percentage(row.get("sand_pct", 0.0)),
            _clamp_percentage(row.get("clay_pct", 0.0)),
        ),
        axis=1,
    )
    frame["theta_i"] = initial_theta

    return geopandas.GeoDataFrame(frame, crs=soils.crs)


def build_lookup_parameters(
    components_df,
    horizons_df,
    surface_top_cm: float = 0.0,
    surface_bot_cm: float = 10.0,
):
    pandas = require_pandas()
    components = pandas.DataFrame(components_df).copy()
    horizons = pandas.DataFrame(horizons_df).copy()

    if components.empty or horizons.empty:
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
                "hsg_dom",
                "hsg_dry",
                "hsg_drained",
                "hsg_comp",
            ]
        )

    components = components.dropna(subset=["mukey", "cokey"])
    components["mukey"] = components["mukey"].astype(str)
    components["cokey"] = components["cokey"].astype(str)

    horizons = horizons.dropna(subset=["cokey"])
    horizons["cokey"] = horizons["cokey"].astype(str)
    if "mukey" not in horizons.columns:
        horizons = horizons.merge(
            components[["cokey", "mukey"]].drop_duplicates(),
            on="cokey",
            how="left",
        )

    comp_params = component_surface_params_us(
        horizons,
        surface_top_cm=surface_top_cm,
        surface_bot_cm=surface_bot_cm,
    )
    mu_params = mapunit_params_us(comp_params, components)
    hsg = summarize_hsg(components)
    return mu_params.merge(hsg, on="mukey", how="left")


def build_hsg_lookup_parameters(components_df, horizons_df, surface_top_cm: float = 0.0, surface_bot_cm: float = 10.0):
    """Build Green-Ampt parameters using HSG-based Ksat lookup.
    
    This method calculates Green-Ampt parameters from the soil texture
    using the Rawls/SWMM lookup table for suction, porosity, etc., but
    uses HSG-based representative Ksat values instead of texture-based ones.
    This provides more conservative estimates aligned with NRCS guidance.
    """
    # First, get the texture-based parameters
    texture_params = build_lookup_parameters(
        components_df,
        horizons_df,
        surface_top_cm=surface_top_cm,
        surface_bot_cm=surface_bot_cm,
    )
    
    if texture_params.empty:
        return texture_params
        
    # Now, replace Ksat with HSG-based values
    from .lookup import HSG_KSAT_TABLE

    def get_hsg_ksat(row):
        hsg = row.get("hsg_dom")
        if hsg and hsg in HSG_KSAT_TABLE:
            return HSG_KSAT_TABLE[hsg]["ks_inhr"]
        # Keep texture-based value if no HSG mapping
        return row.get("Ks_inhr")

    texture_params["Ks_inhr"] = texture_params.apply(get_hsg_ksat, axis=1)
    
    return texture_params



def apply_initial_deficit_mode(
    soils: "gpd.GeoDataFrame", mode: InitialDeficitMode = "design"
) -> "gpd.GeoDataFrame":
    geopandas = require_geopandas()
    frame = soils.copy()
    if mode == "continuous":
        source = "theta_i_cont"
        delta_source = "dtheta_cont"
    else:
        source = "theta_i_design"
        delta_source = "dtheta_design"

    if source in frame.columns:
        frame["theta_i"] = frame[source]
    if delta_source in frame.columns:
        frame["dtheta"] = frame[delta_source]

    return geopandas.GeoDataFrame(frame, crs=soils.crs)


def enrich_with_lookup_parameters(
    soils: "gpd.GeoDataFrame", mode: InitialDeficitMode = "design"
) -> "gpd.GeoDataFrame":
    return apply_initial_deficit_mode(soils, mode=mode)


def emit_units_summary() -> Dict[str, str]:
    return {
        "Ks_inhr": "in/hr (saturated hydraulic conductivity)",
        "psi_in": "in (wetting-front suction head)",
        "theta_s": "fraction (porosity)",
        "theta_fc": "fraction (field capacity)",
        "theta_wp": "fraction (wilting point)",
        "init_def": "fraction (porosity - wilting; long-term)",
        "theta_i_design": "fraction (theta_fc)",
        "theta_i_cont": "fraction (theta_s - init_def)",
        "dtheta_design": "fraction",
        "dtheta_cont": "fraction",
        "hsg_dom": "A/B/C/D/U (dominant, undrained)",
        "hsg_dry": "first letter of dual",
        "hsg_drained": "second letter of dual",
        "hsg_comp": "JSON % by HSG (dry)",
        "texcl": "USDA texture class (top window)",
    }


def _clamp_percentage(value: float) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return max(0.0, min(100.0, numeric))


def _ensure_column(frame: "gpd.GeoDataFrame", target: str, fallbacks: Iterable[str], default_value: float) -> None:
    if target in frame.columns:
        series = frame[target]
    else:
        series = _first_available_series(frame, fallbacks)
    if series is None:
        frame[target] = default_value
        return

    frame[target] = [
        value if value is not None else default_value
        for value in (_safe_float(v) for v in series)
    ]


def _first_available_series(frame: "gpd.GeoDataFrame", fallbacks: Iterable[str]):
    for name in fallbacks:
        if name in frame.columns:
            return frame[name]
    return None


def _safe_float(value: Optional[float]) -> Optional[float]:
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def _calculate_hsg_ksat_stats(components_df):
    """Calculate min, max, and weighted average Ksat based on HSG composition."""
    pandas = require_pandas()
    from .lookup import HSG_KSAT_RANGES_INHR
    from .processing import _parse_dual_hsg
    from .lookup import _arith_mean

    components = pandas.DataFrame(components_df).copy()
    if components.empty:
        return pandas.DataFrame(columns=["mukey", "ksat_hsg_min", "ksat_hsg_max", "ksat_hsg_avg"])

    components["mukey"] = components["mukey"].astype(str)
    components["comppct_r"] = pandas.to_numeric(components.get("comppct_r"), errors="coerce").fillna(0.0)
    
    records = []
    for mukey, group in components.groupby("mukey"):
        hsg_info = []
        for _, row in group.iterrows():
            hsg, _ = _parse_dual_hsg(row.get("hydgrp"))
            if hsg in HSG_KSAT_RANGES_INHR:
                hsg_range = HSG_KSAT_RANGES_INHR[hsg]
                hsg_info.append({
                    "min_ksat": hsg_range["min"],
                    "max_ksat": hsg_range["max"],
                    "avg_ksat": (hsg_range["min"] + hsg_range["max"]) / 2.0 if hsg_range["max"] != float("inf") else hsg_range["min"],
                    "weight": row["comppct_r"]
                })
        
        if not hsg_info:
            records.append({
                "mukey": mukey,
                "ksat_hsg_min": float("nan"),
                "ksat_hsg_max": float("nan"),
                "ksat_hsg_avg": float("nan"),
            })
            continue

        hsg_df = pandas.DataFrame(hsg_info)
        
        # Normalize weights
        total_weight = hsg_df["weight"].sum()
        if total_weight > 0:
            weights = hsg_df["weight"] / total_weight
        else:
            weights = pandas.Series([1/len(hsg_df)] * len(hsg_df))

        # Calculate max Ksat, handling infinite values
        max_ksat_values = hsg_df["max_ksat"].copy()
        # Replace inf with the corresponding min_ksat value for that row
        inf_mask = max_ksat_values == float("inf")
        if inf_mask.any():
            max_ksat_values[inf_mask] = hsg_df.loc[inf_mask, "min_ksat"]
        
        records.append({
            "mukey": mukey,
            "ksat_hsg_min": hsg_df["min_ksat"].min(),
            "ksat_hsg_max": max_ksat_values.max(),
            "ksat_hsg_avg": _arith_mean(hsg_df["avg_ksat"], weights),
        })
        
    return pandas.DataFrame.from_records(records)
