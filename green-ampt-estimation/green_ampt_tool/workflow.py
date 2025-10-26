from __future__ import annotations

import logging

from .config import PipelineConfig
from .data_access import SSURGOData, fetch_ssurgo_with_pysda, load_ssurgo_local, parse_aoi_path, read_aoi
from .export import export_parameter_vectors, export_raw_ssurgo_data
from .parameters import (
    build_lookup_parameters,
    build_hsg_lookup_parameters,
    enrich_with_green_ampt_parameters,
    enrich_with_lookup_parameters,
)
from .processing import attach_properties, clip_to_aoi, summarize_mapunit_properties
from .rasterization import rasterize_parameters

logger = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig):
    logger.info("Starting Green-Ampt pipeline")

    aoi = read_aoi(config.aoi_path, layer=config.aoi_layer)
    logger.debug("AOI loaded with %d feature(s)", len(aoi))
    
    # Inherit AOI CRS if output_crs is None
    if config.output_crs is None:
        config.output_crs = aoi.crs.to_string() if hasattr(aoi.crs, 'to_string') else str(aoi.crs)
        logger.info("Using AOI CRS for output: %s", config.output_crs)

    ssurgo: SSURGOData
    if config.use_pysda:
        logger.info("Fetching SSURGO data using PySDA")
        ssurgo = fetch_ssurgo_with_pysda(aoi, timeout=config.pysda_timeout)
    else:
        logger.info("Loading SSURGO data from local files")
        assert config.local_ssurgo is not None
        ssurgo = load_ssurgo_local(config.local_ssurgo)

    if config.export_raw_data and config.raw_data_dir is not None:
        logger.info("Saving raw SSURGO datasets to %s", config.raw_data_dir)
        export_raw_ssurgo_data(ssurgo, config.raw_data_dir)

    final_vector = _prepare_green_ampt_vector(aoi, ssurgo, config)
    
    if config.use_hsg_lookup:
        parameterised = enrich_with_lookup_parameters(final_vector)
        raster_fields = [
            "Ks_inhr",
            "psi_in",
            "theta_s",
            "theta_fc",
            "theta_wp",
            "theta_i",
        ]
    elif config.use_lookup_table:
        parameterised = enrich_with_lookup_parameters(final_vector)
        raster_fields = [
            "Ks_inhr",
            "psi_in",
            "theta_s",
            "theta_fc",
            "theta_wp",
            "theta_i",
        ]
    else:
        parameterised = enrich_with_green_ampt_parameters(final_vector)
        raster_fields = ["ksat", "theta_s", "psi", "theta_i"]

    vector_path = export_parameter_vectors(parameterised, config)
    logger.info("Vector parameters saved to %s", vector_path)

    logger.info("Rasterising parameters")
    rasterize_parameters(parameterised, raster_fields, config)
    logger.info("Pipeline complete; rasters written to %s", config.raster_dir)
    return parameterised


def _prepare_green_ampt_vector(aoi, ssurgo: SSURGOData, config: PipelineConfig):
    logger.debug("Clipping mupolygon to AOI bounds")
    clipped = clip_to_aoi(ssurgo.mupolygon, aoi)

    logger.debug("Summarising soil properties (depth_limit_cm=%.1f)", config.depth_limit_cm)
    if config.use_hsg_lookup:
        aggregated = build_hsg_lookup_parameters(
            ssurgo.component,
            ssurgo.chorizon,
            surface_top_cm=0.0,
            surface_bot_cm=min(10.0, config.depth_limit_cm),
        )
    elif config.use_lookup_table:
        aggregated = build_lookup_parameters(
            ssurgo.component,
            ssurgo.chorizon,
            surface_top_cm=0.0,
            surface_bot_cm=min(10.0, config.depth_limit_cm),
        )
    else:
        aggregated = summarize_mapunit_properties(
            ssurgo.component, ssurgo.chorizon, depth_limit_cm=config.depth_limit_cm
        )

    if aggregated.empty:
        raise RuntimeError("No soil properties could be derived for the provided AOI")

    logger.debug("Attaching aggregated properties to spatial data")
    final_vector = attach_properties(clipped, aggregated)
    return final_vector
