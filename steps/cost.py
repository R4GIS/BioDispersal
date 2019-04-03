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

from PyQt5.QtGui import QIcon
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget

from ..qgis_lib_mc import (utils, qgsUtils, abstract_model, qgsTreatments, feedbacks)
from . import params, subnetworks

import time

cost_fields = ["st_name","start_layer","perm_layer","cost","out_layer"]

# CostItem implements DictItem and contains below fields :
#   - 'st_name' : sous-trame name
#   - 'start_layer' : vector layer containing starting points
#   - 'perm_layer' : raster layer containing cost for each pixel
#   - 'cost' : maximal cost
class CostItem(abstract_model.DictItem):

    def __init__(self,st_name,start_layer,perm_layer,cost,out_layer):
        dict = {"st_name" : st_name,
                "start_layer" : start_layer,
                "perm_layer" : perm_layer,
                "cost" : cost,
                "out_layer" : out_layer}
        super().__init__(dict)
        
    def equals(self,other):
        same_start = self.dict["start_layer"] == other.dict["start_layer"]
        same_perm = self.dict["perm_layer"] == other.dict["perm_layer"]
        same_cost = self.dict["cost"] == other.dict["cost"]
        return (same_start and same_perm and same_cost)
        
    def applyItem(self):
        utils.debug("Start runCost")
        feedbacks.progressFeedback.focusLogTab()
        st_name = self.dict["st_name"]
        st_item = subnetworks.getSTByName(st_name)
        startLayer = params.getOrigPath(self.dict["start_layer"])
        utils.checkFileExists(startLayer,"Dispersion Start Layer ")
        startRaster = st_item.getStartLayerPath()
        params.checkInit()
        extent_layer_path = params.getExtentLayer()
        qgsTreatments.applyRasterization(startLayer,"geom",startRaster,
                           resolution=params.getResolution(),
                           extent_path=extent_layer_path,load_flag=False,to_byte=False,
                           more_args=['-ot','Byte','-a_nodata','0'])
        permRaster = params.getOrigPath(self.dict["perm_layer"])
        cost = self.dict["cost"]
        tmpPath = st_item.getDispersionTmpPath(cost)
        #outPath = st_item.getDispersionPath(cost)
        outPath = params.getOrigPath(self.dict["out_layer"])
        if os.path.isfile(outPath):
            qgsUtils.removeRaster(outPath)
        qgsTreatments.applyRCost(startRaster,permRaster,cost,tmpPath)
        qgsTreatments.applyFilterGdalFromMaxVal(tmpPath,outPath,cost)
        #removeRaster(tmpPath)
        res_layer = qgsUtils.loadRasterLayer(outPath)
        QgsProject.instance().addMapLayer(res_layer)
        utils.debug("End runCost")
            
    def checkItem(self):
        pass
        
class CostModel(abstract_model.DictModel):
    
    def __init__(self):
        self.parser_name = "CostModel"
        super().__init__(self,cost_fields)
    
    @staticmethod
    def mkItemFromDict(dict):
        if "out_layer" in dict:
            utils.checkFields(cost_fields,dict.keys())
            item = CostItem(dict["st_name"],dict["start_layer"],dict["perm_layer"],
                            dict["cost"],dict["out_layer"])
        else:
            st_name = dict["st_name"]
            st_item = subnetworks.getSTByName(st_name)
            out_path = st_item.getDispersionPath(dict["cost"])
            item = CostItem(dict["st_name"],dict["start_layer"],dict["perm_layer"],
                            dict["cost"],out_path)
        return item
        
    def applyItems(self,indexes):
        utils.debug("[applyItems]")
        feedbacks.progressFeedback.focusLogTab()
        if not indexes:
            utils.internal_error("No indexes in Cost applyItems")
        progress_section = feedbacks.ProgressFeedback("Cost",len(indexes))
        progress_section.start_section()
        params.checkInit()
        for n in indexes:
            i = self.items[n]
            i.applyItem()
            progress_section.next_step()
        progress_section.end_section()
        
        
class CostConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg):
        self.dlg = dlg
        costModel = CostModel()
        self.onlySelection = False
        super().__init__(costModel,self.dlg.costView,
                         self.dlg.costAdd,self.dlg.costRemove,
                         self.dlg.costRun,self.dlg.costRunOnlySelection)
        
    def initGui(self):
        self.dlg.costStartLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.costStartLayer.setFilter(qgsUtils.getVectorFilters())
        self.dlg.costPermRasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.costPermRaster.setFilter("*.tif")
        self.dlg.costOutLayer.setFilter("*.tif")
        self.dlg.costOutLayer.setStorageMode(QgsFileWidget.SaveFile)
        
    def connectComponents(self):
        super().connectComponents()
        self.dlg.costSTCombo.setModel(subnetworks.stModel)
        self.dlg.costStartLayer.fileChanged.connect(self.setStartLayer)
        self.dlg.costPermRaster.fileChanged.connect(self.setPermRaster)
        
    def switchST(self,text):
        st_item = subnetworks.getSTByName(text)
        st_friction_path = st_item.getFrictionPath()
        self.dlg.costPermRaster.lineEdit().setValue(st_friction_path)
        
    def setStartLayer(self,path):
        layer = qgsUtils.loadVectorLayer(path,loadProject=True)
        self.dlg.costStartLayerCombo.setLayer(layer)
        
    def setPermRaster(self,path):
        layer = qgsUtils.loadRasterLayer(path,loadProject=True)
        self.dlg.costPermRasterCombo.setLayer(layer)
        
    def setStartLayerFromCombo(self,layer):
        utils.debug("setStartLayerFromCombo")
        if layer:
            path = qgsUtils.pathOfLayer(layer)
            self.dlg.costStartLayer.lineEdit().setValue(path)
        
    def setPermRasterFromCombo(self,layer):
        utils.debug("setPermRasterFromCombo")
        if layer:
            path = qgsUtils.pathOfLayer(layer)
            self.dlg.costPermRaster.lineEdit().setValue(path)
        
    def mkItem(self):
        st_name = self.dlg.costSTCombo.currentText()
        if not st_name:
            utils.user_error("No Sous-Trame selected")
        start_layer = self.dlg.costStartLayerCombo.currentLayer()
        if not start_layer:
            utils.user_error("No start layer selected")
        start_layer_path = params.normalizePath(qgsUtils.pathOfLayer(start_layer))
        perm_layer = self.dlg.costPermRasterCombo.currentLayer()
        if not perm_layer:
            utils.user_error("No permability layer selected")
        perm_layer_path = params.normalizePath(qgsUtils.pathOfLayer(perm_layer))
        cost = str(self.dlg.costMaxVal.value())
        out_layer_path = params.normalizePath(self.dlg.costOutLayer.filePath())
        cost_item = CostItem(st_name,start_layer_path,perm_layer_path,cost,out_layer_path)
        return cost_item
        
