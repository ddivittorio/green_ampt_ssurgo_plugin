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

__author__ = "Damien Di Vittorio"
__date__ = "2025-10-26"
__copyright__ = "(C) 2025 by Damien Di Vittorio"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import inspect
import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from green_ampt_plugin.green_ampt_processing import algorithms
from green_ampt_plugin.green_ampt_processing.green_ampt_algorithm import (
    GreenAmptAlgorithm,
)


class GreenAmptProvider(QgsProcessingProvider):
    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        # Import the algorithm class directly
        from green_ampt_plugin.green_ampt_processing.algorithms.green_ampt_ssurgo import GreenAmptSsurgo
        
        # Add the algorithm
        self.addAlgorithm(GreenAmptSsurgo())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return "greenampt"

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr("Green-Ampt Parameter Generator")

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.join(os.path.dirname(cmd_folder), "icon.png")))
        return icon

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
