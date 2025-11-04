from __future__ import annotations

from pathlib import Path

from ._compat import gpd, require_geopandas, require_pandas
from .config import PipelineConfig
from .data_access import SSURGOData


def export_raw_ssurgo_data(data: SSURGOData, target_dir: Path) -> None:
    """Persist the raw SSURGO datasets for archival or inspection."""

    geopandas = require_geopandas()
    pandas = require_pandas()

    target_dir = Path(target_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    spatial_path = target_dir / "mupolygon_raw.shp"
    geopandas.GeoDataFrame(data.mupolygon).to_file(spatial_path, driver="ESRI Shapefile")

    data.mapunit.to_csv(target_dir / "mapunit_raw.txt", index=False, sep="|")
    data.component.to_csv(target_dir / "component_raw.txt", index=False, sep="|")
    data.chorizon.to_csv(target_dir / "chorizon_raw.txt", index=False, sep="|")


def export_parameter_vectors(vector: "gpd.GeoDataFrame", config: PipelineConfig) -> Path:
    """Write the parameterised GeoDataFrame to a shapefile for inspection."""

    geopandas = require_geopandas()
    output_path = config.build_vector_path()
    geopandas.GeoDataFrame(vector).to_file(output_path, driver="ESRI Shapefile")
    return output_path
