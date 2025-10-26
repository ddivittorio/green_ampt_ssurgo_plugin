from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable, List, Tuple

from ._compat import gpd, pd, require_geopandas, require_pandas

from .config import LocalSSURGOPaths


@dataclass
class SSURGOData:
    """Container for the spatial and tabular SSURGO datasets used downstream."""

    mupolygon: "gpd.GeoDataFrame"
    mapunit: "pd.DataFrame"
    component: "pd.DataFrame"
    chorizon: "pd.DataFrame"


def parse_aoi_path(aoi_spec: str) -> Tuple[Path, str]:
    """Parse an AOI path specification that may include a layer name.
    
    Supports formats:
    - "path/to/file.gpkg" -> (Path("path/to/file.gpkg"), None)
    - "path/to/file.gpkg:layer_name" -> (Path("path/to/file.gpkg"), "layer_name")
    - "path/to/file.gdb:feature_class" -> (Path("path/to/file.gdb"), "feature_class")
    
    Parameters
    ----------
    aoi_spec : str
        Path to AOI file, optionally with layer/feature class appended after ':'
    
    Returns
    -------
    tuple of (Path, str or None)
        File path and optional layer name
    """
    if ':' in aoi_spec:
        # Check if this is a Windows path (e.g., C:\path\to\file)
        parts = aoi_spec.split(':')
        if len(parts) == 2 and len(parts[0]) == 1:
            # Likely Windows drive letter, no layer specified
            return Path(aoi_spec), None
        elif len(parts) == 2:
            # Layer specified: "path:layer"
            return Path(parts[0]), parts[1]
        elif len(parts) == 3 and len(parts[0]) == 1:
            # Windows path with layer: "C:\path\to\file:layer"
            return Path(':'.join(parts[:2])), parts[2]
        else:
            # Multiple colons - unusual, treat as path without layer
            return Path(aoi_spec), None
    else:
        return Path(aoi_spec), None


def read_aoi(aoi_path: Path, layer: str = None) -> "gpd.GeoDataFrame":
    """Load the Area of Interest and normalise to WGS84 (SSURGO native CRS).
    
    Parameters
    ----------
    aoi_path : Path
        Path to the AOI file. Supports various formats:
        - Shapefile (.shp)
        - GeoPackage (.gpkg) - optionally with layer specification
        - File Geodatabase (.gdb) - optionally with feature class specification
        - KML/KMZ (.kml, .kmz)
        - GeoJSON (.geojson, .json)
        - And other formats supported by GeoPandas/Fiona
    layer : str, optional
        Layer name or feature class to read from multi-layer formats.
        For GeoPackage: layer name
        For Geodatabase: feature class name
        If None, reads the first layer.
    
    Returns
    -------
    gpd.GeoDataFrame
        AOI in WGS84 (EPSG:4326) coordinate system.
    """
    geopandas = require_geopandas()

    # Read the file with optional layer specification
    kwargs = {}
    if layer is not None:
        kwargs['layer'] = layer
    
    try:
        aoi = geopandas.read_file(aoi_path, **kwargs)
    except Exception as e:
        # Provide helpful error message for common issues
        if "layer" in str(e).lower() and layer is None:
            raise ValueError(
                f"The file '{aoi_path}' contains multiple layers. "
                f"Please specify a layer using the layer parameter or "
                f"by appending ':layer_name' to the path."
            ) from e
        raise
    
    if aoi.empty:
        raise ValueError(f"AOI geometry is empty: {aoi_path}")
    if aoi.crs is None:
        raise ValueError("AOI file is missing a Coordinate Reference System (CRS)")
    return aoi.to_crs("EPSG:4326")


def load_ssurgo_local(paths: LocalSSURGOPaths) -> SSURGOData:
    """Read previously downloaded SSURGO extracts from disk."""

    geopandas = require_geopandas()
    pandas = require_pandas()

    mupolygon = geopandas.read_file(paths.mupolygon)
    mapunit = _read_pipe_delimited(paths.mapunit)
    component = _read_pipe_delimited(paths.component)
    chorizon = _read_pipe_delimited(paths.chorizon)

    expected_columns = {
        "mapunit": {"mukey"},
        "component": {"mukey", "cokey"},
        "chorizon": {"cokey", "hzdept_r", "hzdepb_r", "ksat_r", "sandtotal_r", "claytotal_r", "dbthirdbar_r"},
    }
    _check_columns(mapunit, expected_columns["mapunit"], paths.mapunit)
    _check_columns(component, expected_columns["component"], paths.component)
    _check_columns(chorizon, expected_columns["chorizon"], paths.chorizon)

    chorizon = chorizon.merge(
        component[["cokey", "mukey"]].drop_duplicates(),
        on="cokey",
        how="left",
    )

    return SSURGOData(
        mupolygon=mupolygon,
        mapunit=mapunit,
        component=component,
        chorizon=chorizon,
    )


def fetch_ssurgo_with_pysda(aoi: "gpd.GeoDataFrame", timeout: int = 300) -> SSURGOData:
    """Fetch SSURGO data from NRCS Soil Data Access using the PySDA helpers.
    
    This function uses PySDA (https://github.com/ncss-tech/pysda), a Python library
    by Charles Ferguson that provides programmatic access to USDA-NRCS Soil Data Access.
    PySDA is vendored in external/pysda/ and licensed under GPL-3.0.
    """

    geopandas = require_geopandas()
    pandas = require_pandas()

    sdapoly, sdatab = _import_pysda_modules()

    # Ensure AOI is in WGS84 and then get bounds, which is more reliable for PySDA
    aoi_wgs84 = aoi.to_crs("EPSG:4326")
    soils = sdapoly.gdf(aoi_wgs84)
    if soils is None or soils.empty:
        raise RuntimeError(
            "PySDA returned no spatial records for the AOI. This can happen if:\n"
            "1. The AOI is too small (try drawing a larger area).\n"
            "2. The AOI is outside the United States.\n"
            "3. There is a temporary issue with the Soil Data Access service."
        )

    soils = geopandas.GeoDataFrame(soils)
    if soils.crs is None:
        soils.set_crs("EPSG:4326", inplace=True)
    elif soils.crs.to_string() != "EPSG:4326":
        soils = soils.to_crs("EPSG:4326")

    if "geom" in soils.columns:
        soils = soils.drop(columns=["geom"])

    soils["mukey"] = soils["mukey"].astype(str)

    mukeys: List[str] = soils["mukey"].dropna().unique().tolist()
    if not mukeys:
        raise RuntimeError("No mukey identifiers returned from SDA query")

    component = _fetch_component_records(sdatab, mukeys)
    if component.empty:
        raise RuntimeError("PySDA returned no component records for the AOI")

    horizons = _fetch_chorizon_records(sdatab, mukeys)
    if horizons.empty:
        raise RuntimeError("PySDA returned no horizon records for the AOI")

    component = component.astype({"mukey": str, "cokey": str}, errors="ignore")
    horizons = horizons.astype({"mukey": str, "cokey": str}, errors="ignore")

    mapunit = pandas.DataFrame({"mukey": mukeys})

    return SSURGOData(
        mupolygon=soils,
        mapunit=mapunit,
        component=component,
        chorizon=horizons,
    )


def _import_pysda_modules():
    """Import PySDA modules for accessing NRCS Soil Data Access.
    
    PySDA (https://github.com/ncss-tech/pysda) by Charles Ferguson is vendored
    in external/pysda/. This function first attempts to import from an installed
    version, then falls back to the vendored copy.
    
    Returns
    -------
    tuple
        (sdapoly, sdatab) modules for spatial and tabular queries
    """
    try:
        from pysda import sdapoly, sdatab  # type: ignore

        return sdapoly, sdatab
    except ImportError:
        fallback = Path(__file__).resolve().parent.parent / "external" / "pysda"
        if fallback.exists():
            parent = fallback.parent
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))

            import importlib

            sdapoly = importlib.import_module("pysda.sdapoly")  # type: ignore
            sdatab = importlib.import_module("pysda.sdatab")  # type: ignore

            return sdapoly, sdatab
        raise


def _fetch_component_records(sdatab_module, mukeys: Iterable[str]) -> "pd.DataFrame":
    pandas = require_pandas()
    frames = []
    for chunk in _chunk_sequence(list(mukeys), 100):
        keys = ",".join(f"'{key}'" for key in chunk)
        query = f"""
        SELECT mukey, cokey, comppct_r, hydgrp, majcompflag
        FROM component
        WHERE mukey IN ({keys})
        """
        frame = sdatab_module.tabular(" ".join(query.split()))
        if frame is not None and not frame.empty:
            frames.append(frame)
    if not frames:
        return pandas.DataFrame(columns=["mukey", "cokey", "comppct_r", "hydgrp", "majcompflag"])
    component = pandas.concat(frames, ignore_index=True)
    return component


def _fetch_chorizon_records(sdatab_module, mukeys: Iterable[str]) -> "pd.DataFrame":
    pandas = require_pandas()
    frames = []
    for chunk in _chunk_sequence(list(mukeys), 50):
        keys = ",".join(f"'{key}'" for key in chunk)
        query = f"""
        SELECT c.mukey, ch.cokey, ch.hzdept_r, ch.hzdepb_r, ch.ksat_r,
               ch.sandtotal_r, ch.claytotal_r, ch.dbthirdbar_r, ch.texcl
        FROM component AS c
        INNER JOIN chorizon AS ch ON ch.cokey = c.cokey
        WHERE c.mukey IN ({keys})
        """
        frame = sdatab_module.tabular(" ".join(query.split()))
        if frame is not None and not frame.empty:
            frames.append(frame)
    if not frames:
        return pandas.DataFrame(
            columns=[
                "mukey",
                "cokey",
                "hzdept_r",
                "hzdepb_r",
                "ksat_r",
                "sandtotal_r",
                "claytotal_r",
                "dbthirdbar_r",
                "texcl",
            ]
        )
    horizons = pandas.concat(frames, ignore_index=True)
    return horizons


def _chunk_sequence(values: Iterable[str], size: int) -> Iterable[Tuple[str, ...]]:
    batch: List[str] = []
    for value in values:
        batch.append(value)
        if len(batch) == size:
            yield tuple(batch)
            batch = []
    if batch:
        yield tuple(batch)
def _read_pipe_delimited(path: Path) -> "pd.DataFrame":
    pandas = require_pandas()
    return pandas.read_csv(path, delimiter="|", dtype=str)


def _check_columns(df: "pd.DataFrame", required: set[str], path: Path) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Required columns {missing} missing from {path}")
