"""Configuration file loading utilities for Green-Ampt pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .config import LocalSSURGOPaths, PipelineConfig


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file.
    
    Parameters
    ----------
    config_path : Path
        Path to configuration file (.yaml, .yml, or .json)
    
    Returns
    -------
    dict
        Configuration dictionary
    
    Raises
    ------
    ValueError
        If file format is not supported or YAML library is missing
    FileNotFoundError
        If config file does not exist
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    suffix = config_path.suffix.lower()
    
    if suffix in ('.yaml', '.yml'):
        if not HAS_YAML:
            raise ValueError(
                "YAML configuration requires PyYAML. Install with: pip install pyyaml"
            )
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    elif suffix == '.json':
        with open(config_path, 'r') as f:
            return json.load(f)
    
    else:
        raise ValueError(
            f"Unsupported configuration file format: {suffix}. "
            f"Supported formats: .yaml, .yml, .json"
        )


def build_config_from_dict(config_dict: Dict[str, Any]) -> PipelineConfig:
    """Build PipelineConfig from a configuration dictionary.
    
    Parameters
    ----------
    config_dict : dict
        Configuration dictionary with keys matching PipelineConfig attributes
    
    Returns
    -------
    PipelineConfig
        Initialized pipeline configuration
    """
    # Handle local SSURGO paths if provided
    local_ssurgo = None
    if 'local_ssurgo' in config_dict and config_dict['local_ssurgo']:
        local_dict = config_dict['local_ssurgo']
        local_ssurgo = LocalSSURGOPaths(
            mupolygon=Path(local_dict['mupolygon']),
            mapunit=Path(local_dict['mapunit']),
            component=Path(local_dict['component']),
            chorizon=Path(local_dict['chorizon']),
        )
    
    # Handle AOI path with potential layer specification
    aoi_spec = config_dict.get('aoi_path') or config_dict.get('aoi')
    if not aoi_spec:
        raise ValueError("Configuration must specify 'aoi_path' or 'aoi'")
    
    # Parse AOI path for layer specification
    from .data_access import parse_aoi_path
    aoi_path, aoi_layer = parse_aoi_path(str(aoi_spec))
    
    # Override with explicit aoi_layer if provided
    if 'aoi_layer' in config_dict:
        aoi_layer = config_dict['aoi_layer']
    
    # Build the configuration
    return PipelineConfig(
        aoi_path=aoi_path,
        aoi_layer=aoi_layer,
        output_dir=Path(config_dict.get('output_dir', 'outputs')),
        output_resolution=float(config_dict.get('output_resolution', 10.0)),
        output_crs=config_dict.get('output_crs'),
        output_prefix=config_dict.get('output_prefix', ''),
        data_source=config_dict.get('data_source', 'pysda'),
        local_ssurgo=local_ssurgo,
        pysda_timeout=int(config_dict.get('pysda_timeout', 300)),
        depth_limit_cm=float(config_dict.get('depth_limit_cm', 10.0)),
        export_raw_data=config_dict.get('export_raw_data', True),
        raw_data_dir=Path(config_dict['raw_data_dir']) if config_dict.get('raw_data_dir') else None,
        use_lookup_table=config_dict.get('use_lookup_table', True),
        use_hsg_lookup=config_dict.get('use_hsg_lookup', False),
    )


def load_config_from_file(config_path: Path) -> PipelineConfig:
    """Load PipelineConfig from a YAML or JSON file.
    
    Parameters
    ----------
    config_path : Path
        Path to configuration file
    
    Returns
    -------
    PipelineConfig
        Initialized pipeline configuration
    """
    config_dict = load_config_file(config_path)
    return build_config_from_dict(config_dict)
