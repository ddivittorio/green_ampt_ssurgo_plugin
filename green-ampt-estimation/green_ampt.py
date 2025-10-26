from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

from green_ampt_tool.config import LocalSSURGOPaths, PipelineConfig
from green_ampt_tool.parameters import emit_units_summary
from green_ampt_tool.workflow import run_pipeline


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Green-Ampt parameter rasters from SSURGO data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Configuration file support
    parser.add_argument(
        "--config",
        help="Path to configuration file (YAML or JSON). If provided, other arguments override config file values.",
    )
    
    parser.add_argument(
        "--aoi",
        help=(
            "Path to an AOI vector file. Supports various formats: "
            "Shapefile (.shp), GeoPackage (.gpkg), Geodatabase (.gdb), KML/KMZ (.kml/.kmz), GeoJSON. "
            "For multi-layer formats, append layer name with ':' (e.g., 'file.gpkg:layer_name')"
        ),
    )
    parser.add_argument(
        "--aoi-layer",
        help="Layer name or feature class for multi-layer AOI formats (alternative to ':layer' syntax)",
    )
    parser.add_argument("--output-dir", help="Directory where output rasters will be written")
    
    # Resolution: go finer by default (10 m)
    parser.add_argument(
        "--output-resolution",
        type=float,
        default=10.0,
        help="Raster resolution in target CRS units (default: 10.0)",
    )
    
    # CRS: let it inherit from AOI unless explicitly set
    parser.add_argument(
        "--output-crs",
        default=None,
        help="Output raster CRS; if omitted, AOI CRS is used (default: AOI CRS)",
    )
    
    parser.add_argument("--output-prefix", default="", help="Optional prefix for generated filenames")
    
    # Prefer live Soil Data Access by default
    parser.add_argument(
        "--data-source",
        choices=["local", "pysda"],
        default="pysda",
        help="Source of SSURGO data (default: pysda)",
    )
    
    parser.add_argument("--mupolygon", default=None, help="Path to local SSURGO mupolygon shapefile")
    parser.add_argument("--mapunit", default=None, help="Path to local SSURGO mapunit.txt file")
    parser.add_argument("--component", default=None, help="Path to local SSURGO component.txt file")
    parser.add_argument("--chorizon", default=None, help="Path to local SSURGO chorizon.txt file")
    
    # Surface window: 0-10 cm by default for infiltration-excess modeling
    parser.add_argument(
        "--depth-limit-cm",
        type=float,
        default=10.0,
        help="Depth limit for horizon aggregation (default: 10.0)",
    )
    
    parser.add_argument("--pysda-timeout", type=int, default=300, help="Timeout (seconds) for PySDA requests")
    
    # Persist raw fetches for QA/repro by default
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument(
        "--export-raw-data",
        dest="export_raw_data",
        action="store_true",
        help="Persist the fetched SSURGO datasets (spatial + tabular) to disk (default: True)",
    )
    export_group.add_argument(
        "--no-export-raw-data",
        dest="export_raw_data",
        action="store_false",
        help="Do not persist the fetched SSURGO datasets",
    )
    parser.set_defaults(export_raw_data=True)
    
    parser.add_argument(
        "--raw-data-dir",
        default=None,
        help="Directory to store raw SSURGO datasets; defaults to <output-dir>/raw_data",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
        help="Logging verbosity",
    )
    
    # Parameter estimation method: mutually exclusive
    param_group = parser.add_mutually_exclusive_group()
    param_group.add_argument(
        "--use-lookup-table",
        dest="param_method",
        action="store_const",
        const="lookup",
        help="Use US-units texture lookup (Rawls/SWMM) - default method",
    )
    param_group.add_argument(
        "--use-hsg-lookup",
        dest="param_method",
        action="store_const",
        const="hsg",
        help="Use HSG-based Ksat lookup (NRCS hydrologic soil groups)",
    )
    param_group.add_argument(
        "--use-pedotransfer",
        dest="param_method",
        action="store_const",
        const="pedotransfer",
        help="Use pedotransfer functions (sand/clay percentages)",
    )
    parser.set_defaults(param_method="lookup")

    args = parser.parse_args(argv)

    # Check that either config or required args are provided
    if not args.config and (not args.aoi or not args.output_dir):
        parser.error("Either --config or both --aoi and --output-dir are required")

    if args.data_source == "local":
        missing = [
            name
            for name in ("mupolygon", "mapunit", "component", "chorizon")
            if getattr(args, name) is None
        ]
        if missing:
            parser.error(
                "the following arguments are required when --data-source=local: "
                + ", ".join(f"--{name}" for name in missing)
            )
    
    # Handle output_crs inheritance from AOI
    if args.output_crs in (None, "", "None"):
        args.output_crs = None  # Will be resolved in workflow
    
    # Default raw_data_dir under output-dir if not provided
    # Only set if output_dir is provided (not when using config file only)
    if not args.raw_data_dir and args.output_dir:
        import os
        args.raw_data_dir = os.path.join(args.output_dir, "raw_data")

    return args


def build_config(args: argparse.Namespace) -> PipelineConfig:
    # If config file provided, load it first
    if args.config:
        from green_ampt_tool.config_loader import load_config_from_file
        config = load_config_from_file(Path(args.config))
        
        # Override config file values with CLI arguments if provided
        if args.aoi:
            from green_ampt_tool.data_access import parse_aoi_path
            aoi_path, aoi_layer = parse_aoi_path(args.aoi)
            config.aoi_path = aoi_path
            if aoi_layer:
                config.aoi_layer = aoi_layer
        if args.aoi_layer:
            config.aoi_layer = args.aoi_layer
        if args.output_dir:
            config.output_dir = Path(args.output_dir)
        if hasattr(args, 'output_resolution') and args.output_resolution is not None:
            config.output_resolution = args.output_resolution
        if hasattr(args, 'output_crs') and args.output_crs is not None:
            config.output_crs = args.output_crs
        if hasattr(args, 'output_prefix') and args.output_prefix:
            config.output_prefix = args.output_prefix
        if hasattr(args, 'data_source') and args.data_source:
            config.data_source = args.data_source
        if hasattr(args, 'depth_limit_cm') and args.depth_limit_cm is not None:
            config.depth_limit_cm = args.depth_limit_cm
        if hasattr(args, 'pysda_timeout') and args.pysda_timeout is not None:
            config.pysda_timeout = args.pysda_timeout
        if hasattr(args, 'export_raw_data'):
            config.export_raw_data = args.export_raw_data
        if hasattr(args, 'raw_data_dir') and args.raw_data_dir:
            config.raw_data_dir = Path(args.raw_data_dir)
        if hasattr(args, 'param_method') and args.param_method:
            config.use_lookup_table = args.param_method == "lookup"
            config.use_hsg_lookup = args.param_method == "hsg"
        
        # Re-run post_init to ensure directories are created
        config.__post_init__()
        return config
    
    # Build config from CLI arguments only
    from green_ampt_tool.data_access import parse_aoi_path
    aoi_path, aoi_layer = parse_aoi_path(args.aoi)
    
    # Override with explicit --aoi-layer if provided
    if args.aoi_layer:
        aoi_layer = args.aoi_layer
    
    local_paths = None
    if args.data_source == "local":
        local_paths = LocalSSURGOPaths(
            mupolygon=Path(args.mupolygon),
            mapunit=Path(args.mapunit),
            component=Path(args.component),
            chorizon=Path(args.chorizon),
        )

    # Map param_method to config flags
    use_lookup_table = args.param_method == "lookup"
    use_hsg_lookup = args.param_method == "hsg"

    return PipelineConfig(
        aoi_path=aoi_path,
        aoi_layer=aoi_layer,
        output_dir=Path(args.output_dir),
        output_resolution=args.output_resolution,
        output_crs=args.output_crs,
        output_prefix=args.output_prefix,
        data_source=args.data_source,
        local_ssurgo=local_paths,
        pysda_timeout=args.pysda_timeout,
        depth_limit_cm=args.depth_limit_cm,
        export_raw_data=args.export_raw_data,
        raw_data_dir=Path(args.raw_data_dir) if args.raw_data_dir else None,
        use_lookup_table=use_lookup_table,
        use_hsg_lookup=use_hsg_lookup,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    config = build_config(args)
    run_pipeline(config)

    print("\nOutput attribute units:")
    for key, description in emit_units_summary().items():
        print(f"  - {key}: {description}")


if __name__ == "__main__":  # pragma: no cover
    main()

