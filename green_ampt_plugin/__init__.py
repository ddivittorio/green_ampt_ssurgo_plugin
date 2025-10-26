# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GreenAmptPlugin
                                 A QGIS plugin
 Generates spatially distributed Green-Ampt infiltration parameters from SSURGO soil data
                              -------------------
        begin                : 2024-10-26
        copyright            : (C) 2024 by Daniel DiVittorio
        email                : ddivittorio@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = "Daniel DiVittorio"
__date__ = "2024-10-26"
__copyright__ = "(C) 2024 by Daniel DiVittorio"


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GreenAmptPlugin class from file GreenAmptPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from green_ampt_plugin.green_ampt_plugin import GreenAmptPlugin

    return GreenAmptPlugin(iface)
