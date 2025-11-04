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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = "Damien Di Vittorio"
__date__ = "2025-10-26"
__copyright__ = "(C) 2025 by Damien Di Vittorio"


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GreenAmptPlugin class from file GreenAmptPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from green_ampt_plugin.green_ampt_plugin import GreenAmptPlugin

    return GreenAmptPlugin(iface)
