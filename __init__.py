# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryWrapper
                                 A QGIS plugin
 Converts geometry longitude from [-180,180] to [0,360]
                             -------------------
        begin                : 2017-03-16
        copyright            : (C) 2017 by Jonah Sullivan
        email                : jonahsullivan79@gmail.com
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeometryWrapper class from file GeometryWrapper.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geometry_wrapper import GeometryWrapper
    return GeometryWrapper(iface)
