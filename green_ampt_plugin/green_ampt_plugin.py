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
import sys

from qgis.core import QgsApplication

from green_ampt_plugin.green_ampt_processing import GreenAmptProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class GreenAmptPlugin(object):
    def __init__(self, iface):
        self.provider = None
        self.iface = iface

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = GreenAmptProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
