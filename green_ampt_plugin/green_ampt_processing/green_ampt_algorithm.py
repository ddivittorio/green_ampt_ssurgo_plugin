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
import inspect
import os
import sys

from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
sys.path.append(cmd_folder)

__author__ = "Damien Di Vittorio"
__date__ = "2025-10-26"
__copyright__ = "(C) 2025 by Damien Di Vittorio"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"


class GreenAmptAlgorithm(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT = "INPUT"

    def __init__(self):
        super().__init__()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()

    def icon(self):
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.dirname(cmd_folder), "icon.png"))
        return icon

    def flags(self):
        return super().flags()
