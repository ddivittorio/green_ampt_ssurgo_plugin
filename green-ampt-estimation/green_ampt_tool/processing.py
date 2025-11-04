from __future__ import annotations

import json
from typing import Dict, List, Tuple

import numpy as np
from ._compat import gpd, pd, require_geopandas, require_pandas


def clip_to_aoi(mupolygon: "gpd.GeoDataFrame", aoi: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    geopandas = require_geopandas()

    if mupolygon.crs is None:
        raise ValueError("mupolygon dataset lacks a CRS; unable to clip")

    target_crs = aoi.crs or "EPSG:4326"
    if mupolygon.crs != target_crs:
        mupolygon = mupolygon.to_crs(target_crs)

    clipped = geopandas.clip(mupolygon, aoi)
    if clipped.empty:
        raise ValueError("Clipping mupolygon to AOI produced an empty GeoDataFrame")
    return clipped

def summarize_mapunit_properties(
    component: "pd.DataFrame",
    chorizon: "pd.DataFrame",
    depth_limit_cm: float = 30.0,
) -> "pd.DataFrame":
    pandas = require_pandas()

    comp = component.copy()
    horiz = chorizon.copy()

    if "mukey" in comp.columns:
        comp["mukey"] = comp["mukey"].astype(str)
    if "cokey" in comp.columns:
        comp["cokey"] = comp["cokey"].astype(str)
    if "mukey" in horiz.columns:
        horiz["mukey"] = horiz["mukey"].astype(str)
    if "cokey" in horiz.columns:
        horiz["cokey"] = horiz["cokey"].astype(str)

    if comp.empty or horiz.empty:
        return pandas.DataFrame(columns=["mukey", "ksat", "sand_pct", "clay_pct", "theta_s"])

    comp["comppct_r"] = pandas.to_numeric(comp.get("comppct_r"), errors="coerce")
    comp = comp.dropna(subset=["mukey", "cokey"])

    numeric_cols = [
        "hzdept_r",
        "hzdepb_r",
        "ksat_r",
        "sandtotal_r",
        "claytotal_r",
        "dbthirdbar_r",
    ]
    for column in numeric_cols:
        horiz[column] = pandas.to_numeric(horiz.get(column), errors="coerce")

    if "mukey" not in horiz.columns:
        horiz = horiz.merge(comp[["cokey", "mukey"]].drop_duplicates(), on="cokey", how="left")

    horiz = horiz.dropna(subset=["cokey", "mukey"])

    horiz["hzdept_r"] = horiz["hzdept_r"].fillna(0)
    horiz["hzdepb_r"] = horiz["hzdepb_r"].fillna(horiz["hzdept_r"])

    horiz["upper"] = horiz["hzdept_r"].clip(lower=0, upper=depth_limit_cm)
    horiz["lower"] = horiz["hzdepb_r"].clip(lower=0, upper=depth_limit_cm)
    horiz["thickness"] = (horiz["lower"] - horiz["upper"]).clip(lower=0)
    horiz = horiz[horiz["thickness"] > 0]

    if horiz.empty:
        return pandas.DataFrame(columns=["mukey", "ksat", "sand_pct", "clay_pct", "theta_s"])

    particle_density = 2.65
    horiz["theta_s_hz"] = 1 - (horiz["dbthirdbar_r"] / particle_density)
    horiz.loc[horiz["theta_s_hz"] < 0, "theta_s_hz"] = float("nan")
    horiz.loc[horiz["theta_s_hz"] > 0.9, "theta_s_hz"] = 0.9

    component_summaries: List[Dict[str, float]] = []
    grouped = horiz.groupby("cokey", sort=False)
    for cokey, group in grouped:
        weights = group["thickness"].fillna(0)
        if weights.sum() == 0:
            continue

        summary = {
            "cokey": cokey,
            "mukey": group["mukey"].iloc[0],
            "ksat": _weighted_mean(group["ksat_r"], weights),
            "sand_pct": _weighted_mean(group["sandtotal_r"], weights),
            "clay_pct": _weighted_mean(group["claytotal_r"], weights),
            "theta_s": _weighted_mean(group["theta_s_hz"], weights),
        }
        component_summaries.append(summary)

    if not component_summaries:
        return pandas.DataFrame(columns=["mukey", "ksat", "sand_pct", "clay_pct", "theta_s"])

    component_frame = pandas.DataFrame(component_summaries)
    component_frame = component_frame.merge(comp[["cokey", "comppct_r"]], on="cokey", how="left")
    component_frame["weight"] = pandas.to_numeric(component_frame.get("comppct_r"), errors="coerce").clip(lower=0)

    mapunit_records: List[Dict[str, float]] = []
    for mukey, group in component_frame.groupby("mukey", sort=False):
        weight = group["weight"].fillna(0)
        record = {
            "mukey": mukey,
            "ksat": _weighted_mean(group["ksat"], weight, normalize=True),
            "sand_pct": _weighted_mean(group["sand_pct"], weight, normalize=True),
            "clay_pct": _weighted_mean(group["clay_pct"], weight, normalize=True),
            "theta_s": _weighted_mean(group["theta_s"], weight, normalize=True),
        }
        mapunit_records.append(record)

    result = pandas.DataFrame(mapunit_records)
    if "mukey" in result.columns:
        result["mukey"] = result["mukey"].astype(str)
    return result


def attach_properties(
    mupolygon_clipped: "gpd.GeoDataFrame",
    aggregated: "pd.DataFrame",
) -> "gpd.GeoDataFrame":
    geopandas = require_geopandas()
    frame = mupolygon_clipped.copy()
    if "mukey" in frame.columns:
        frame["mukey"] = frame["mukey"].astype(str)
    if "mukey" in aggregated.columns:
        aggregated = aggregated.copy()
        aggregated["mukey"] = aggregated["mukey"].astype(str)
    frame = frame.merge(aggregated, on="mukey", how="left")
    return geopandas.GeoDataFrame(frame, crs=mupolygon_clipped.crs)


def _weighted_mean(series, weights, normalize: bool = False) -> float:
    pandas = require_pandas()
    values = pandas.to_numeric(series, errors="coerce")
    weights = pandas.to_numeric(weights, errors="coerce").fillna(0)

    if normalize and weights.sum() > 0:
        weights = weights / weights.sum()

    mask = values.notna() & weights.gt(0)
    if mask.any():
        return float((values[mask] * weights[mask]).sum() / weights[mask].sum())

    values = values.dropna()
    if not values.empty:
        return float(values.mean())

    return float("nan")


def _arith_mean(values, weights) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    total_weight = weight_array.sum()
    if total_weight <= 0:
        return float("nan")
    return float(np.nansum(weight_array * value_array) / total_weight)


def _parse_dual_hsg(value: str) -> Tuple[str, str]:
    pandas = require_pandas()
    if value is None or (isinstance(value, float) and pandas.isna(value)):
        return ("U", "U")
    text = str(value).strip().upper().replace("\\", "/")
    if "/" in text:
        dry, drained = text.split("/", 1)
        dry = dry.strip() or "U"
        drained = drained.strip() or "U"
        return (dry, drained)
    if text:
        return (text, text)
    return ("U", "U")


def summarize_hsg(components_df: "pd.DataFrame") -> "pd.DataFrame":
    pandas = require_pandas()
    frame = pandas.DataFrame(components_df).copy()
    if frame.empty:
        return pandas.DataFrame(
            columns=["mukey", "hsg_dom", "hsg_dry", "hsg_drained", "hsg_comp"]
        )

    frame["mukey"] = frame["mukey"].astype(str)
    frame["comppct_r"] = pandas.to_numeric(frame.get("comppct_r"), errors="coerce").fillna(0.0)
    frame["majcompflag"] = frame.get("majcompflag", "NO")

    groups = []
    for mukey, group in frame.groupby("mukey", sort=False):
        working = group.copy()
        working["maj_rank"] = working["majcompflag"].astype(str).str.upper() != "YES"
        working = working.sort_values(["comppct_r", "maj_rank"], ascending=[False, True])
        hydgrp = working["hydgrp"].iloc[0] if not working.empty else None
        dry, drained = _parse_dual_hsg(hydgrp)

        totals = float(working["comppct_r"].sum() or 0.0)
        comp_totals: Dict[str, float] = {}
        for _, row in working.iterrows():
            dry_code, _ = _parse_dual_hsg(row.get("hydgrp"))
            comp_totals[dry_code] = comp_totals.get(dry_code, 0.0) + float(row.get("comppct_r", 0.0))

        if totals > 0:
            comp_pct = {key: round(100.0 * value / totals) for key, value in comp_totals.items()}
        else:
            comp_pct = {}

        groups.append(
            {
                "mukey": mukey,
                "hsg_dom": dry,
                "hsg_dry": dry,
                "hsg_drained": drained,
                "hsg_comp": json.dumps(comp_pct),
            }
        )

    return pandas.DataFrame(groups)
