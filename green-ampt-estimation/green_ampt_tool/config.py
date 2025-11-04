from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


@dataclass
class LocalSSURGOPaths:
    """File system locations for SSURGO datasets previously downloaded by the user."""

    mupolygon: Path
    mapunit: Path
    component: Path
    chorizon: Path

    def resolve(self) -> "LocalSSURGOPaths":
        self.mupolygon = self._ensure_path(self.mupolygon)
        self.mapunit = self._ensure_path(self.mapunit)
        self.component = self._ensure_path(self.component)
        self.chorizon = self._ensure_path(self.chorizon)
        return self

    @staticmethod
    def _ensure_path(value: Path) -> Path:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"SSURGO file not found: {path}")
        return path


@dataclass
class PipelineConfig:
    """Runtime configuration for the Green-Ampt pipeline."""

    aoi_path: Path
    output_dir: Path
    output_resolution: float = 10.0
    output_crs: Optional[str] = None
    output_prefix: str = ""
    data_source: Literal["local", "pysda"] = "pysda"
    local_ssurgo: Optional[LocalSSURGOPaths] = None
    pysda_timeout: int = 300
    depth_limit_cm: float = 10.0
    export_raw_data: bool = True
    raw_data_dir: Optional[Path] = None
    use_lookup_table: bool = True
    use_hsg_lookup: bool = False
    aoi_layer: Optional[str] = None  # Layer name for multi-layer formats
    raster_dir: Path = field(init=False)
    vector_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.aoi_path = Path(self.aoi_path).expanduser().resolve()
        if not self.aoi_path.exists():
            raise FileNotFoundError(f"AOI file not found: {self.aoi_path}")

        self.output_dir = Path(self.output_dir).expanduser().resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.data_source == "local":
            if self.local_ssurgo is None:
                raise ValueError("local_ssurgo paths must be provided when data_source='local'")
            self.local_ssurgo = self.local_ssurgo.resolve()

        if self.output_resolution <= 0:
            raise ValueError("output_resolution must be positive")

        if self.depth_limit_cm <= 0:
            raise ValueError("depth_limit_cm must be positive")

        self.output_prefix = self.output_prefix.strip()

        self.raster_dir = (self.output_dir / "rasters").resolve()
        self.raster_dir.mkdir(parents=True, exist_ok=True)

        self.vector_dir = (self.output_dir / "vectors").resolve()
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        if self.export_raw_data:
            if self.raw_data_dir is not None:
                self.raw_data_dir = Path(self.raw_data_dir).expanduser().resolve()
            else:
                self.raw_data_dir = (self.output_dir / "raw_data").resolve()
            self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.raw_data_dir = None
        
        # Handle AOI CRS inheritance
        if self.output_crs in (None, "", "None", "AOI"):
            # Will be resolved in workflow after AOI is loaded
            self.output_crs = None

    @property
    def use_pysda(self) -> bool:
        return self.data_source == "pysda"

    def build_raster_path(self, parameter_name: str) -> Path:
        prefix = f"{self.output_prefix}_" if self.output_prefix else ""
        filename = f"{prefix}{parameter_name}_green_ampt.tif"
        return self.raster_dir / filename

    def build_vector_path(self, base_name: str = "green_ampt_params.shp") -> Path:
        prefix = f"{self.output_prefix}_" if self.output_prefix else ""
        return self.vector_dir / f"{prefix}{base_name}"
