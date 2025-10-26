from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ._compat import gpd, require_geopandas

try:  # pragma: no cover - import guard for environments lacking rasterio
    import rasterio  # type: ignore
    from rasterio.features import rasterize  # type: ignore
    from rasterio.transform import from_bounds  # type: ignore
except ImportError as exc:  # pragma: no cover
    rasterio = None  # type: ignore
    rasterize = None  # type: ignore
    from_bounds = None  # type: ignore
    _RASTERIO_IMPORT_ERROR = exc
else:  # pragma: no cover
    _RASTERIO_IMPORT_ERROR = None

from .config import PipelineConfig


@dataclass
class RasterGrid:
    transform: object
    width: int
    height: int


def prepare_grid(vector: "gpd.GeoDataFrame", resolution: float, output_crs: str) -> RasterGrid:
    require_geopandas()

    if rasterio is None or from_bounds is None:  # pragma: no cover - runtime guard
        raise ModuleNotFoundError("rasterio is required for rasterisation") from _RASTERIO_IMPORT_ERROR

    projected = vector.to_crs(output_crs)
    xmin, ymin, xmax, ymax = projected.total_bounds
    width = max(1, int((xmax - xmin) / resolution))
    height = max(1, int((ymax - ymin) / resolution))
    transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
    return RasterGrid(transform=transform, width=width, height=height)


def rasterize_parameters(
    vector: "gpd.GeoDataFrame",
    parameters: Iterable[str],
    config: PipelineConfig,
) -> None:
    require_geopandas()

    if rasterio is None or rasterize is None or from_bounds is None:  # pragma: no cover
        raise ModuleNotFoundError("rasterio is required for rasterisation") from _RASTERIO_IMPORT_ERROR

    grid = prepare_grid(vector, config.output_resolution, config.output_crs)
    projected = vector.to_crs(config.output_crs)

    for parameter in parameters:
        if parameter not in projected.columns:
            continue

        shapes = (
            (geom, float(value) if value is not None else float("nan"))
            for geom, value in zip(projected.geometry, projected[parameter])
        )
        array = rasterize(
            shapes=shapes,
            out_shape=(grid.height, grid.width),
            transform=grid.transform,
            fill=float("nan"),
            dtype="float32",
        )

        output_path = config.build_raster_path(parameter)
        with rasterio.open(
            output_path,
            "w",
            driver="GTiff",
            height=grid.height,
            width=grid.width,
            count=1,
            dtype="float32",
            crs=config.output_crs,
            transform=grid.transform,
            nodata=float("nan"),
        ) as dst:
            dst.write(array, 1)
            dst.update_tags(parameter=parameter, source="green_ampt_tool")