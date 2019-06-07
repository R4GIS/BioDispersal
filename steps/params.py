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

import os.path
import pathlib

from qgis.core import (QgsCoordinateReferenceSystem, QgsRectangle, QgsProject,
                       QgsCoordinateTransform, QgsProcessingUtils)
from qgis.gui import QgsFileWidget
from PyQt5.QtCore import QVariant, QAbstractTableModel, QModelIndex, Qt, QCoreApplication
from PyQt5.QtWidgets import QAbstractItemView, QFileDialog, QHeaderView

from ..qgis_lib_mc import utils, qgsUtils, qgsTreatments, abstract_model
from ..algs import BioDispersal_algs

# BioDispersal global parameters

# ParamsModel from which parameters are retrieved
paramsModel = None

# Default CRS is set to epsg:2154 (France area, metric system)
defaultCrs = QgsCoordinateReferenceSystem("EPSG:2154")

# Returns normalized path from QgsMapLayerComboBox
# def getPathFromLayerCombo(combo):
    # layer = combo.currentLayer()
    # layer_path = normalizePath(qgsUtils.pathOfLayer(layer))
    # return layer_path
            
# def checkWorkspaceInit():
    # paramsModel.checkWorkspaceInit()
        
# def normalizePath(path):
    # return paramsModel.normalizePath(path)
        
# def getOrigPath(path):
    # return paramsModel.getOrigPath(path)
        
# def checkInit():
    # utils.debug("paramsModel : " + str(paramsModel))
    # utils.debug("paramsModel : " + str(paramsModel is None))
    # utils.debug("paramsModel : " + str(paramsModel.extentLayer))
    # paramsModel.checkInit()
        
# def getResolution():
    # return paramsModel.getResolution()
    
# def getExtentLayer():
    # return paramsModel.getExtentLayer()
    
# Return bounding box coordinates of extent layer
# def getExtentCoords():
    # return paramsModel.getExtentCoords()
        
# Checks that given layer matches extent layer coordinates
# def equalsParamsExtent(path):
    # return paramsModel.equalsParamsExtent(path)
        
# Returns extent layer bounding box as a QgsRectangle
# def getExtentRectangle():
    # return paramsModel.getExtentRectangle()
    
# Normalize given raster layer to match global extent and resolution
# def normalizeRaster(path,resampling_mode="near"):
    # return paramsModel.normalizeRaster(path,resampling_mode)
        
#class ParamsModel(abstract_model.AbstractGroupModel):
class ParamsModel(QAbstractTableModel):

    def __init__(self,bdModel):
        self.parser_name = "ParamsModel"
        self.is_runnable = False
        self.bdModel = bdModel
        self.workspace = None
        self.extentLayer = None
        self.resolution = 0.0
        self.projectFile = ""
        self.crs = defaultCrs
        self.fields = ["workspace","extentLayer","resolution","projectFile","crs"]
        QAbstractTableModel.__init__(self)
        
    def setExtentLayer(self,path):
        path = self.normalizePath(path)
        utils.info("Setting extent layer to " + str(path))
        self.extentLayer = path
        self.layoutChanged.emit()
        
    def setResolution(self,resolution):
        utils.info("Setting resolution to " + str(resolution))
        self.resolution = resolution
        self.layoutChanged.emit()
        
    def setCrs(self,crs):
        utils.info("Setting extent CRS to " + crs.description())
        self.crs = crs
        self.layoutChanged.emit()
        
    def getCrsStr(self):
        return self.crs.authid().lower()

    def getTransformator(self,in_crs):
        transformator = QgsCoordinateTransform(in_crs,self.crs,QgsProject.instance())
        return transformator
    
    def getBoundingBox(self,in_extent_rect,in_crs):
        transformator = self.getTransformator(in_crs)
        out_extent_rect = transformator.transformBoundingBox(in_extent_rect)
        return out_extent_rect
        
    def setWorkspace(self,path):
        norm_path = utils.normPath(path)
        self.workspace = norm_path
        utils.info("Workspace directory set to '" + norm_path)
        if not os.path.isdir(norm_path):
            utils.user_error("Directory '" + norm_path + "' does not exist")
            
    def getGroupsPath(self):
        self.checkWorkspaceInit()
        return utils.joinPath(self.workspace,"Groups")
            
    def getGroupPath(self,name):
        groups_path = self.getGroupsPath()
        if not os.path.isdir(groups_path):
            utils.info("Creating groups directory '" + groups_path + "'")
            os.makedirs(groups_path)
        group_path = utils.joinPath(groups_path,name)
        if not os.path.isdir(group_path):
            utils.info("Creating group directory '" + group_path + "'")
            os.makedirs(group_path)
        return group_path
        
    def getSTPath(self,name):
        self.checkWorkspaceInit()
        all_st_path = utils.joinPath(self.workspace,"Subnetworks")
        if not os.path.isdir(all_st_path):
            utils.info("Creating ST directory '" + all_st_path + "'")
            os.makedirs(all_st_path)
        st_path = utils.joinPath(all_st_path,name)
        if not os.path.isdir(st_path):
            utils.info("Creating ST directory '" + st_path + "'")
            os.makedirs(st_path)
        return st_path
            
    def fromXMLRoot(self,root):
        dict = root.attrib
        utils.debug("params dict = " + str(dict))
        return self.fromXMLDict(dict)
    
    def fromXMLDict(self,dict):
        if "workspace" in dict:
            if os.path.isdir(dict["workspace"]) and not self.workspace:
                self.setWorkspace(dict["workspace"])
        if "extent" in dict:
            self.setExtentLayer(dict["extent"])
        if "resolution" in dict:
            self.setResolution(dict["resolution"])
        self.layoutChanged.emit()
    
    def toXML(self,indent=""):
        xmlStr = indent + "<" + self.parser_name
        if self.workspace:
            xmlStr += " workspace=\"" + str(self.workspace) + "\""
        if self.resolution:
            xmlStr += " resolution=\"" + str(self.resolution) + "\""
        if self.extentLayer:
            xmlStr += " extent=\"" + str(self.extentLayer) + "\""
        xmlStr += "/>"
        return xmlStr
        
    def rowCount(self,parent=QModelIndex()):
        return len(self.fields)
        
    def columnCount(self,parent=QModelIndex()):
        return 1
              
    def getNItem(self,n):
        items = [self.workspace,
                 self.extentLayer,
                 self.resolution,
                 self.projectFile,
                 self.crs.description(),
                 ""]
        return items[n]
            
    def data(self,index,role):
        if not index.isValid():
            return QVariant()
        row = index.row()
        item = self.getNItem(row)
        if role != Qt.DisplayRole:
            return QVariant()
        elif row < self.rowCount():
            return(QVariant(item))
        else:
            return QVariant()
            
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        
    def headerData(self,col,orientation,role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant("value")
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(self.fields[col])
        return QVariant()
        
    # Checks that workspace is intialized and is an existing directory.
    def checkWorkspaceInit(self):
        if not self.workspace:
            utils.user_error("Workspace parameter not initialized")
        if not os.path.isdir(self.workspace):
            utils.user_error("Workspace directory '" + self.workspace + "' does not exist")
            
    # Returns relative path w.r.t. workspace directory.
    # File separator is set to common slash '/'.
    def normalizePath(self,path):
        self.checkWorkspaceInit()
        if not path:
            utils.user_error("Empty path")
        norm_path = utils.normPath(path)
        if os.path.isabs(norm_path):
            rel_path = os.path.relpath(norm_path,self.workspace)
        else:
            rel_path = norm_path
        final_path = utils.normPath(rel_path)
        return final_path
            
    # Returns absolute path from normalized path (cf 'normalizePath' function)
    def getOrigPath(self,path):
        self.checkWorkspaceInit()
        if path is None or path == "":
            utils.user_error("Empty path")
        elif os.path.isabs(path):
            return path
        else:
            join_path = utils.joinPath(self.workspace,path)
            norm_path = os.path.normpath(join_path)
            return norm_path
            
    # Checks that all parameters are initialized
    def checkInit(self):
        self.checkWorkspaceInit()
        if not self.extentLayer:
            utils.user_error("Extent layer parameter not initialized")
        extent_path = self.getOrigPath(self.extentLayer)
        utils.debug("extent_path = " + str(extent_path))
        utils.checkFileExists(extent_path,"Extent layer ")
        if not self.resolution:
            utils.user_error("Resolution parameter not initialized")
        if self.resolution == 0.0:
            utils.user_error("Null resolution")
        if not self.crs:
            utils.user_error("CRS parameter not initialized")
        if not self.crs.isValid():
            utils.user_error("Invalid CRS")
            
    def getResolution(self):
        return float(self.resolution)
        
    def getExtentLayer(self):
        return self.getOrigPath(self.extentLayer)
        
    def getExtentString(self):
        extent_path = self.getOrigPath(self.extentLayer)
        extent_layer = qgsUtils.loadLayer(extent_path)
        extent = extent_layer.extent()
        transformed_extent = self.getBoundingBox(extent,extent_layer.crs())
        res = str(transformed_extent.xMinimum())
        res += ',' + str(transformed_extent.xMaximum())
        res += ',' + str(transformed_extent.yMinimum())
        res += ',' + str(transformed_extent.yMaximum())
        res += '[' + str(self.crs) + ']'
        return res
        
    # Return bounding box coordinates of extent layer
    def getExtentCoords(self):
        extent_path = self.getOrigPath(self.extentLayer)
        if extent_path:
            return qgsUtils.coordsOfExtentPath(extent_path)
        else:
            utils.user_error("Extent layer not initialized")
            
    # Checks that given layer matches extent layer coordinates
    def equalsParamsExtent(self,path):
        params_coords = self.getExtentCoords()
        path_coords = qgsUtils.coordsOfExtentPath(path)
        return (params_coords == path_coords)
            
    # Returns extent layer bounding box as a QgsRectangle
    def getExtentRectangle(self):
        coords = self.getExtentCoords()
        rect = QgsRectangle(float(coords[0]),float(coords[1]),
                            float(coords[2]),float(coords[3]))
        return rect 
                
    # Normalize given raster layer to match global extent and resolution
    def normalizeRaster(self,path,out_path=None,resampling_mode="near"):
        layer = qgsUtils.loadRasterLayer(path)
        # extent
        extent_path = self.getExtentLayer()
        extent_layer, extent_layer_type = qgsUtils.loadLayerGetType(extent_path)
        utils.debug("extent_layer_type = " + str(extent_layer_type))
        params_coords = self.getExtentCoords()
        layer_coords = qgsUtils.coordsOfExtentPath(path)
        same_extent = self.equalsParamsExtent(path)
        resolution = self.getResolution()
        # layer_res_x = layer.rasterUnitsPerPixelX()
        # layer_res_y = layer.rasterUnitsPerPixelX()
        # same_res = (layer_res_x == resolution and layer_res_y == resolution)
        # if not same_extent:
            # utils.debug("Diff coords : '" + str(params_coords) + "' vs '" + str(layer_coords))
        # if not same_res:
            # utils.debug("Diff resolution : '(" + str(resolution) + ")' vs '("
                        # + str(layer_res_x) + "," + str(layer_res_y) + ")'")
        if extent_layer_type == 'Vector':
            clipped_path = QgsProcessingUtils.generateTempFilename('clipped.tif')
            qgsTreatments.clipRasterFromVector(path,extent_path,out_path,resolution=resolution)
        # elif not (same_extent and same_res):
        else:
            warped_path = QgsProcessingUtils.generateTempFilename('warped.tif')
            utils.warn("Normalizing raster '" + str(path)+ "' to '" + str(warped_path) + "'")
            qgsTreatments.applyWarpGdal(path,out_path,resampling_mode,self.crs,
                                        resolution,extent_path,
                                        load_flag=False,to_byte=False)

class ParamsConnector:

    def __init__(self,dlg,paramsModel):
        self.dlg = dlg
        self.model = paramsModel
        
    def initGui(self):
        #self.dlg.paramsView.setHorizontalScrollBarMode(QAbstractItemView.ScrollPerPixel)
        self.dlg.paramsView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        #self.dlg.extentLayer.setFilter("*.shp;*.tif")
        self.dlg.paramsCrs.setCrs(defaultCrs)
        #self.model.setResolution(25)
        #self.dlg.rasterResolution.setValue(25)
        
    def connectComponents(self):
        self.dlg.paramsView.setModel(self.model)
        self.dlg.rasterResolution.valueChanged.connect(self.model.setResolution)
        self.dlg.extentLayer.setStorageMode(QgsFileWidget.GetFile)
        self.dlg.extentLayer.fileChanged.connect(self.model.setExtentLayer)
        self.dlg.workspace.setStorageMode(QgsFileWidget.GetDirectory)
        self.dlg.workspace.fileChanged.connect(self.model.setWorkspace)
        self.dlg.paramsCrs.crsChanged.connect(self.model.setCrs)
        header = self.dlg.paramsView.horizontalHeader()     
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.model.layoutChanged.emit()
        
    def tr(self, message):
        return QCoreApplication.translate('BioDispersal', message)
        
    def refreshProjectName(self):
        fname = self.model.projectFile
        basename = os.path.basename(fname)
        if basename:
            self.dlg.projectName.setText(self.tr("Projet BioDispersal : ") + basename)
        else:
            self.dlg.projectName.setText(self.tr("Pas de projet BioDispersal"))
        
        
    def setProjectFile(self,fname):
        self.model.projectFile = fname
        self.refreshProjectName()
        # basename = os.path.basename(fname)
        # if basename:
            # self.dlg.projectName.setText(self.tr("Current project : ") + basename)
