# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GreenAmptPlugin
                                 A QGIS plugin
    Generates spatially distributed Green-Ampt infiltration parameters from SSURGO soil data
                                 -------------------
        begin                : 2025-10-26
        copyright            : (C) 2025 by Damien Di Vittorio
        email                : damien.divittorio@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Note: VS Code linting may show import errors for QGIS modules because it doesn't
# have access to the QGIS Python environment. These imports are correct for QGIS runtime.

import inspect
import os
import sys
import tempfile
from pathlib import Path

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
)
from qgis.PyQt.QtGui import QIcon

from green_ampt_plugin.green_ampt_processing.green_ampt_algorithm import GreenAmptAlgorithm

__author__ = "Damien Di Vittorio"
__date__ = "2025-10-26"
__copyright__ = "(C) 2025 by Damien Di Vittorio"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"


class GreenAmptSsurgo(GreenAmptAlgorithm):
    """
    Algorithm to generate Green-Ampt infiltration parameters from SSURGO data
    """

    # Constants for parameters
    AOI = "AOI"
    OUTPUT_DIR = "OUTPUT_DIR"
    OUTPUT_RESOLUTION = "OUTPUT_RESOLUTION"
    OUTPUT_CRS = "OUTPUT_CRS"
    OUTPUT_PREFIX = "OUTPUT_PREFIX"
    DATA_SOURCE = "DATA_SOURCE"
    PARAM_METHOD = "PARAM_METHOD"
    DEPTH_LIMIT = "DEPTH_LIMIT"
    PYSDA_TIMEOUT = "PYSDA_TIMEOUT"
    EXPORT_RAW_DATA = "EXPORT_RAW_DATA"
    LOAD_VECTOR = "LOAD_VECTOR"
    LOAD_RASTERS = "LOAD_RASTERS"
    
    # Local SSURGO parameters
    MUPOLYGON = "MUPOLYGON"
    MAPUNIT = "MAPUNIT"
    COMPONENT = "COMPONENT"
    CHORIZON = "CHORIZON"

    def _import_green_ampt_modules(self):
        """
        Lazy import of green_ampt_tool modules to avoid import errors at plugin load time
        """
        # Add the green-ampt-estimation directory to the path
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        plugin_folder = os.path.dirname(os.path.dirname(cmd_folder))

        # Try embedded location first (for deployed plugin), then development location
        green_ampt_estimation_paths = [
            plugin_folder,  # Plugin folder itself (where symlink is)
            os.path.join(plugin_folder, "green_ampt_estimation"),  # Embedded in plugin
            os.path.join(os.path.dirname(os.path.dirname(plugin_folder)), "green-ampt-estimation")  # Development
        ]

        green_ampt_estimation_path = None
        for path in green_ampt_estimation_paths:
            if os.path.exists(os.path.join(path, "green_ampt_tool")):
                green_ampt_estimation_path = path
                break

        if green_ampt_estimation_path and green_ampt_estimation_path not in sys.path:
            sys.path.insert(0, green_ampt_estimation_path)
        
        try:
            from green_ampt_tool.config import LocalSSURGOPaths, PipelineConfig
            from green_ampt_tool.workflow import run_pipeline
            from green_ampt_tool.parameters import emit_units_summary
            return LocalSSURGOPaths, PipelineConfig, run_pipeline, emit_units_summary
        except ImportError as e:
            raise ImportError(f"Failed to import green_ampt_tool modules: {e}. Make sure green-ampt-estimation is available.")

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm
        """
        
        # Area of Interest (required)
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.AOI,
                self.tr("Area of Interest (AOI)"),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        
        # Output directory (required)
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIR,
                self.tr("Output Directory"),
                defaultValue=None,
            )
        )
        
        # Data source selection
        self.addParameter(
            QgsProcessingParameterEnum(
                self.DATA_SOURCE,
                self.tr("Data Source"),
                options=[
                    self.tr("PySDA (live SSURGO queries)"),
                    self.tr("Local SSURGO files")
                ],
                defaultValue=0,
            )
        )
        
        # Parameter estimation method
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PARAM_METHOD,
                self.tr("Parameter Estimation Method"),
                options=[
                    self.tr("Texture Lookup (Rawls/SWMM)"),
                    self.tr("HSG Lookup (Hydrologic Soil Groups)"),
                    self.tr("Pedotransfer Functions")
                ],
                defaultValue=0,
            )
        )
        
        # Output resolution
        self.addParameter(
            QgsProcessingParameterNumber(
                self.OUTPUT_RESOLUTION,
                self.tr("Output Resolution (in CRS units)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.1,
            )
        )
        
        # Output CRS (optional - inherits from AOI if not set)
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_CRS,
                self.tr("Output CRS (EPSG code or leave empty to use AOI CRS)"),
                defaultValue="",
                optional=True,
            )
        )
        
        # Output prefix (optional)
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_PREFIX,
                self.tr("Output Filename Prefix (optional)"),
                defaultValue="",
                optional=True,
            )
        )
        
        # Depth limit
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DEPTH_LIMIT,
                self.tr("Depth Limit (cm) for horizon aggregation"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.1,
            )
        )
        
        # PySDA timeout
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PYSDA_TIMEOUT,
                self.tr("PySDA Timeout (seconds)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=300,
                minValue=30,
            )
        )
        
        # Export raw data option
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.EXPORT_RAW_DATA,
                self.tr("Export Raw SSURGO Data"),
                defaultValue=True,
            )
        )
        
        # Local SSURGO file parameters (optional, shown when Local is selected)
        self.addParameter(
            QgsProcessingParameterFile(
                self.MUPOLYGON,
                self.tr("SSURGO mupolygon shapefile (for local source)"),
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Shapefiles (*.shp)",
                optional=True,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.MAPUNIT,
                self.tr("SSURGO mapunit.txt file (for local source)"),
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Text files (*.txt)",
                optional=True,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.COMPONENT,
                self.tr("SSURGO component.txt file (for local source)"),
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Text files (*.txt)",
                optional=True,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.CHORIZON,
                self.tr("SSURGO chorizon.txt file (for local source)"),
                behavior=QgsProcessingParameterFile.File,
                fileFilter="Text files (*.txt)",
                optional=True,
            )
        )
        
        # Map loading options
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOAD_VECTOR,
                self.tr("Load vector output in map"),
                defaultValue=True,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOAD_RASTERS,
                self.tr("Load raster outputs in map"),
                defaultValue=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Main algorithm processing
        """
        
        # Import green_ampt_tool modules (lazy loading)
        LocalSSURGOPaths, PipelineConfig, run_pipeline, emit_units_summary = self._import_green_ampt_modules()
        
        # Create multi-step feedback for progress reporting
        feedback = QgsProcessingMultiStepFeedback(5, feedback)
        
        feedback.pushInfo("Starting Green-Ampt parameter generation...")
        
        # Get parameters
        aoi_layer = self.parameterAsVectorLayer(parameters, self.AOI, context)
        output_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
        output_resolution = self.parameterAsDouble(parameters, self.OUTPUT_RESOLUTION, context)
        output_crs = self.parameterAsString(parameters, self.OUTPUT_CRS, context)
        output_prefix = self.parameterAsString(parameters, self.OUTPUT_PREFIX, context)
        data_source_idx = self.parameterAsEnum(parameters, self.DATA_SOURCE, context)
        param_method_idx = self.parameterAsEnum(parameters, self.PARAM_METHOD, context)
        depth_limit = self.parameterAsDouble(parameters, self.DEPTH_LIMIT, context)
        pysda_timeout = self.parameterAsInt(parameters, self.PYSDA_TIMEOUT, context)
        export_raw_data = self.parameterAsBool(parameters, self.EXPORT_RAW_DATA, context)
        load_vector = self.parameterAsBool(parameters, self.LOAD_VECTOR, context)
        load_rasters = self.parameterAsBool(parameters, self.LOAD_RASTERS, context)
        
        feedback.setCurrentStep(1)
        feedback.pushInfo(f"AOI Layer: {aoi_layer.name()}")
        feedback.pushInfo(f"Output Directory: {output_dir}")
        
        # Map indices to values
        data_source = "pysda" if data_source_idx == 0 else "local"
        param_methods = ["lookup", "hsg", "pedotransfer"]
        param_method = param_methods[param_method_idx]
        
        use_lookup_table = param_method == "lookup"
        use_hsg_lookup = param_method == "hsg"
        
        feedback.pushInfo(f"Data Source: {data_source}")
        feedback.pushInfo(f"Parameter Method: {param_method}")
        
        # Export AOI to temporary shapefile
        feedback.setCurrentStep(2)
        feedback.pushInfo("Exporting AOI layer to temporary file...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            aoi_path = os.path.join(temp_dir, "aoi.shp")
            
            feedback.pushInfo(f"Temporary directory: {temp_dir}")
            feedback.pushInfo(f"AOI will be exported to: {aoi_path}")
            feedback.pushInfo(f"AOI layer is valid: {aoi_layer.isValid()}")
            feedback.pushInfo(f"AOI layer feature count: {aoi_layer.featureCount()}")
            
            # Configure save options for Shapefile format
            save_options = QgsVectorFileWriter.SaveVectorOptions()
            save_options.driverName = "ESRI Shapefile"
            save_options.fileEncoding = "UTF-8"
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                aoi_layer,
                aoi_path,
                context.transformContext(),
                save_options
            )
            
            feedback.pushInfo(f"Export error code: {error[0]}")
            if len(error) > 1:
                feedback.pushInfo(f"Export error message: {error[1]}")
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise QgsProcessingException(f"Failed to export AOI: {error[1]}")
            
            feedback.pushInfo(f"AOI exported to: {aoi_path}")
            
            # List files in temp directory
            temp_files = os.listdir(temp_dir)
            feedback.pushInfo(f"Files in temp directory: {temp_files}")
            
            # Verify the file was created and exists
            if not os.path.exists(aoi_path):
                raise QgsProcessingException(f"AOI file was not created: {aoi_path}")
            
            feedback.pushInfo(f"AOI file verified, size: {os.path.getsize(aoi_path)} bytes")
            
            # Handle local SSURGO files if needed
            local_paths = None
            if data_source == "local":
                feedback.pushInfo("Preparing local SSURGO file paths...")
                
                mupolygon = self.parameterAsFile(parameters, self.MUPOLYGON, context)
                mapunit = self.parameterAsFile(parameters, self.MAPUNIT, context)
                component = self.parameterAsFile(parameters, self.COMPONENT, context)
                chorizon = self.parameterAsFile(parameters, self.CHORIZON, context)
                
                if not all([mupolygon, mapunit, component, chorizon]):
                    raise QgsProcessingException(
                        "When using local data source, all SSURGO files must be provided: "
                        "mupolygon, mapunit, component, chorizon"
                    )
                
                local_paths = LocalSSURGOPaths(
                    mupolygon=Path(mupolygon),
                    mapunit=Path(mapunit),
                    component=Path(component),
                    chorizon=Path(chorizon),
                )
            
            # Build configuration
            feedback.setCurrentStep(3)
            feedback.pushInfo("Building pipeline configuration...")
            
            # Final check that AOI file still exists before creating config
            if not os.path.exists(aoi_path):
                raise QgsProcessingException(f"AOI file disappeared before config creation: {aoi_path}")
            
            # Handle output CRS
            if output_crs and output_crs.strip():
                # User provided a CRS
                config_crs = output_crs.strip()
            else:
                # Use AOI CRS
                config_crs = None
            
            config = PipelineConfig(
                aoi_path=Path(aoi_path),
                aoi_layer=None,
                output_dir=Path(output_dir),
                output_resolution=output_resolution,
                output_crs=config_crs,
                output_prefix=output_prefix,
                data_source=data_source,
                local_ssurgo=local_paths,
                pysda_timeout=pysda_timeout,
                depth_limit_cm=depth_limit,
                export_raw_data=export_raw_data,
                raw_data_dir=None,  # Will use default: output_dir/raw_data
                use_lookup_table=use_lookup_table,
                use_hsg_lookup=use_hsg_lookup,
            )
            
            # Run the pipeline
            feedback.setCurrentStep(4)
            feedback.pushInfo("Running Green-Ampt parameter generation pipeline...")
            feedback.pushInfo("This may take several minutes depending on AOI size and data source...")
            
            try:
                run_pipeline(config)
            except Exception as e:
                raise QgsProcessingException(f"Pipeline execution failed: {str(e)}")
            
            feedback.setCurrentStep(5)
            feedback.pushInfo("Pipeline completed successfully!")
            
            # Report output units
            feedback.pushInfo("\nOutput attribute units:")
            for key, description in emit_units_summary().items():
                feedback.pushInfo(f"  - {key}: {description}")
            
            feedback.pushInfo(f"\nOutputs saved to: {output_dir}")
            feedback.pushInfo(f"  - Rasters: {output_dir}/rasters/")
            feedback.pushInfo(f"  - Vectors: {output_dir}/vectors/")
            if export_raw_data:
                feedback.pushInfo(f"  - Raw SSURGO data: {output_dir}/raw_data/")
        
        # Load output layers in map if requested
        feedback.pushInfo("\nLoading resulting layers")
        self._load_output_layers(output_dir, output_prefix, load_vector, load_rasters, feedback, context)
        
        return {self.OUTPUT_DIR: output_dir}
    
    def _load_output_layers(self, output_dir, output_prefix, load_vector, load_rasters, feedback, context):
        """Load output layers into the QGIS map"""
        import glob
        from pathlib import Path
        
        # Build prefix for file matching
        prefix = f"{output_prefix}_" if output_prefix else ""
        
        # Load vector outputs
        if load_vector:
            vector_dir = Path(output_dir) / "vectors"
            if vector_dir.exists():
                # Look for Green-Ampt parameter shapefile
                pattern = f"{prefix}green_ampt_params*.shp"
                vector_files = list(vector_dir.glob(pattern))
                
                for vector_file in vector_files:
                    layer_name = f"Green-Ampt Parameters ({vector_file.stem})"
                    vector_layer = QgsVectorLayer(str(vector_file), layer_name, "ogr")
                    
                    if vector_layer.isValid():
                        QgsProject.instance().addMapLayer(vector_layer)
                        feedback.pushInfo(f"  ✓ Loaded vector: {layer_name}")
                    else:
                        feedback.pushInfo(f"  ⚠ Failed to load vector: {vector_file}")
        
        # Load raster outputs
        if load_rasters:
            raster_dir = Path(output_dir) / "rasters"
            if raster_dir.exists():
                # Define expected raster parameters (actual output names)
                raster_params = {
                    "Ks_inhr": "Hydraulic Conductivity (Ks)",
                    "psi_in": "Suction Head (ψ)",
                    "theta_s": "Porosity (θs)",
                    "theta_i": "Initial Moisture (θi)",
                    "theta_fc": "Field Capacity (θfc)",
                    "theta_wp": "Wilting Point (θwp)"
                }
                
                for param_key, display_name in raster_params.items():
                    pattern = f"{prefix}{param_key}_green_ampt.tif"
                    raster_files = list(raster_dir.glob(pattern))
                    
                    for raster_file in raster_files:
                        layer_name = f"{display_name} ({raster_file.stem})"
                        raster_layer = QgsRasterLayer(str(raster_file), layer_name)
                        
                        if raster_layer.isValid():
                            QgsProject.instance().addMapLayer(raster_layer)
                            feedback.pushInfo(f"  ✓ Loaded raster: {layer_name}")
                        else:
                            feedback.pushInfo(f"  ⚠ Failed to load raster: {raster_file}")

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "generate_green_ampt_parameters"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Generate Green-Ampt Parameters from SSURGO")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Infiltration Parameters")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "infiltration"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it.
        """
        return self.tr(
            """This algorithm generates spatially distributed Green-Ampt infiltration parameters from SSURGO soil data.
            
            <b>Inputs:</b>
            <ul>
            <li><b>Area of Interest (AOI):</b> Polygon vector layer defining the study area</li>
            <li><b>Data Source:</b> Choose between live PySDA queries or local SSURGO files</li>
            <li><b>Parameter Method:</b> Choose estimation method:
                <ul>
                <li>Texture Lookup: Uses USDA texture classes with Rawls/SWMM lookup table</li>
                <li>HSG Lookup: Uses NRCS Hydrologic Soil Groups</li>
                <li>Pedotransfer Functions: Calculates from sand/clay percentages</li>
                </ul>
            </li>
            </ul>
            
            <b>Outputs:</b>
            <ul>
            <li>Raster GeoTIFFs for hydraulic conductivity (Ks), suction head (psi), porosity (theta_s), and initial moisture (theta_i)</li>
            <li>Vector parameters with all derived fields</li>
            <li>Optional raw SSURGO data (spatial and tabular)</li>
            </ul>
            
            <b>Note:</b> For PySDA data source, internet access is required. Processing time varies based on AOI size.
            """
        )
