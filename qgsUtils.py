# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BioDispersal
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

import os

from qgis.gui import *
from qgis.core import *
import pathlib
from PyQt5.QtCore import QVariant, pyqtSignal

from . import utils

# QgsUtils gathers pyQgs utilitary functions

def typeIsInteger(t):
    return (t == QVariant.Int
            or t == QVariant.UInt
            or t == QVariant.LongLong
            or t == QVariant.ULongLong)
            
def typeIsFloat(t):
    return (t == QVariant.Double)
    
def typeIsNumeric(t):
    return (typeIsInteger(t) or typeIsFloat(t))

# Delete raster file and associated xml file
def removeRaster(path):
    utils.removeFile(path)
    aux_name = path + ".aux.xml"
    utils.removeFile(aux_name)
    
# Returns path from QgsMapLayer
def pathOfLayer(l):
    utils.debug("pathOfLayer")
    uri = l.dataProvider().dataSourceUri()
    utils.debug(str(uri))
    if l.type() == QgsMapLayer.VectorLayer:
        path = uri[:uri.rfind('|')]
    else:
        path = uri
    utils.debug(str(path))
    return path
      
def layerNameOfPath(p):
    bn = os.path.basename(p)
    res = os.path.splitext(bn)[0]
    return res
    
def getVectorFilters():
    return QgsProviderRegistry.instance().fileVectorFilters()
    
def getRasterFilters():
    return QgsProviderRegistry.instance().fileRasterFilters()
    
# def isVectorPath(fname):
    # vector_extensions = [".shp"]
    # extension = pathlib.Path(fname).suffix
    # return (extension in vector_extensions)
    
# def isRasterPath(fname):
    # raster_extensions = [".tif"]
    # extension = pathlib.Path(fname).suffix
    # return (extension in raster_extensions)
    
# Opens vector layer from path.
# If loadProject is True, layer is added to QGIS project
def loadVectorLayer(fname,loadProject=False):
    utils.checkFileExists(fname)
    layer = QgsVectorLayer(fname, layerNameOfPath(fname), "ogr")
    extension = os.path.splitext(fname)[1]
    if layer == None:
        utils.user_error("Could not load vector layer '" + fname + "'")
    if not layer.isValid():
        utils.user_error("Invalid vector layer '" + fname + "'")
    if extension == ".shp" and utils.platform_sys == "Linux":
        layer.dataProvider().setEncoding('Latin-1')
    else:
        layer.dataProvider().setEncoding('System')
    if loadProject:
        QgsProject.instance().addMapLayer(layer)
    return layer
    
# Opens raster layer from path.
# If loadProject is True, layer is added to QGIS project
def loadRasterLayer(fname,loadProject=False):
    utils.checkFileExists(fname)
    rlayer = QgsRasterLayer(fname, layerNameOfPath(fname))
    if not rlayer.isValid():
        utils.user_error("Invalid raster layer '" + fname + "'")
    if loadProject:
        QgsProject.instance().addMapLayer(rlayer)
    return rlayer

# Opens layer from path.
# If loadProject is True, layer is added to QGIS project
def loadLayer(fname,loadProject=False):
    try:
        return (loadVectorLayer(fname,loadProject))
    except CustomException:
        try:
            return (loadRasterLayer(fname,loadProject))
        except CustomException:
            utils.user_error("Could not load layer '" + fname + "'")
    
# Retrieve layer loaded in QGIS project from name
def getLoadedLayerByName(name):
    layers = QgsProject.instance().mapLayersByName('my layer name')
    nb_layers = len(layers)
    if nb_layers == 0:
        utils.warn("No layer named '" + name + "' found")
        return None
    elif nb_layers > 1:
        utils.user_error("Several layers named '" + name + "' found")
    else:
        return layers[0]
        
        
# LAYER PARAMETERS

# Returns CRS code in lowercase (e.g. 'epsg:2154')
def getLayerCrsStr(layer):
    return str(layer.crs().authid().lower())
    
# Returns geometry type string (e.g. 'MultiPolygon')
def getLayerGeomStr(layer):
    return QgsWkbTypes.displayString(layer.wkbType())
    
# Returns simple geometry type string (e.g. 'Polygon', 'Line', 'Point')
def getLayerSimpleGeomStr(layer):
    type = layer.wkbType()
    geom_type = QgsWkbTypes.geometryType(type)
    return QgsWkbTypes.geometryDisplayString(geom_type)
    
# Checks layers geometry compatibility (raise error if not compatible)
def checkLayersCompatible(l1,l2):
    crs1 = l1.crs().authid()
    crs2 = l2.crs().authid()
    if crs1 != crs2:
        utils.user_error("Layer " + l1.name() + " SRID '" + str(crs1)
                    + "' not compatible with SRID '" + str(crs2)
                    + "' of layer " + l2.name())
    geomType1 = l1.geometryType()
    geomType2 = l1.geometryType()
    if geomType1 != geomType2:
        utils.user_error("Layer " + l1.name() + " geometry '" + str(geomType1)
                    + "' not compatible with geometry '" + str(geomType2)
                    + "' of layer " + l2.name())
    
# Initialize new layer from existing one, importing CRS and geometry
def createLayerFromExisting(inLayer,outName,geomType=None,crs=None):
    utils.debug("[createLayerFromExisting]")
    # crs=str(inLayer.crs().authid()).lower()
    # geomType=QgsWkbTypes.displayString(inLayer.wkbType())
    if not crs:
        crs=getLayerCrsStr(inLayer)
    if not geomType:
        geomType=getLayerGeomStr(inLayer)
    layerStr = geomType + '?crs='+crs
    utils.debug(layerStr)
    outLayer=QgsVectorLayer(geomType + '?crs='+crs, outName, "memory")
    return outLayer
    
# DEPRECATED
def applyBuffer(in_layer,buffer_val,out_layer):
    utils.debug("[applyBuffer]")
    #writeShapefile(in_layer,"D:/MChailloux/tmp/tmp_buf.shp")
    in_pr = in_layer.dataProvider()
    out_pr = out_layer.dataProvider()
    new_fields = QgsFields()
    out_layer.updateFields()
    out_f = QgsFeature(new_fields)
    for in_f in in_layer.getFeatures():
        #out_f = QgsFeature(in_f)
        buf_geom = in_f.geometry().buffer(buffer_val,8)
        poly = buf_geom.asPolygon()
        out_f.setGeometry(QgsGeometry.fromPolygonXY(poly))
        res = out_pr.addFeature(out_f)
        #if not res:
        #    utils.internal_error("ko")
        out_layer.updateExtents()
    return out_layer

# Writes file from existing QgsMapLayer
def writeShapefile(layer,outfname):
    utils.debug("[writeShapefile] " + outfname + " from " + str(layer))
    if os.path.isfile(outfname):
        os.remove(outfname)
    (error, error_msg) = QgsVectorFileWriter.writeAsVectorFormat(layer,outfname,'utf-8',destCRS=layer.sourceCrs(),driverName='ESRI Shapefile')
    if error == QgsVectorFileWriter.NoError:
        utils.info("Shapefile '" + outfname + "' succesfully created")
    else:
        utils.user_error("Unable to create shapefile '" + outfname + "' : " + str(error_msg))
    
# Return bounding box coordinates as a list
def coordsOfExtentPath(extent_path):
    layer = loadLayer(extent_path)
    extent = layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()
    return [str(x_min),str(y_min),str(x_max),str(y_max)]
    
