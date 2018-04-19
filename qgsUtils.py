# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Utils
                                 A QGIS plugin
 Computes ecological continuities based on environments permeability
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by IRSTEA
        email                : mathieu.chailloux@irstea.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.gui import *
from qgis.core import *
from .utils import *

def createLayerFromExisting(inLayer,outName):
    crs=inLayer.crs().authid()
    geomType=inLayer.geometryType()
    outLayer=QgsVectorLayer(geomType + '?crs='+crs, outName, "memory")

def writeShapefile(layer,outfname):
    crs = QgsCoordinateReferenceSystem("EPSG:2154")
    #params = 
    (error, error_msg) = QgsVectorFileWriter.writeAsVectorFormat(layer,outfname,'utf-8',destCRS=crs,driverName='ESRI Shapefile')
    if error == QgsVectorFileWriter.NoError:
        info("Shapefile '" + outfname + "' succesfully created")
    else:
        user_error("Unable to create shapefile '" + outfname + "' : " + str(error_msg))