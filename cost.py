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
import processing

from PyQt5.QtGui import QIcon

import utils
import params
from .qgsUtils import *
import progress
import sous_trames
from .abstract_model import *
from .qgsTreatments import *

cost_fields = ["st_name","start_layer","perm_layer","cost"]

# CostItem implements DictItem and contains below fields :
#   - 'st_name' : sous-trame name
#   - 'start_layer' : vector layer containing starting points
#   - 'perm_layer' : raster layer containing cost for each pixel
#   - 'cost' : maximal cost
class CostItem(DictItem):

    def __init__(self,st_name,start_layer,perm_layer,cost):
        dict = {"st_name" : st_name,
                "start_layer" : start_layer,
                "perm_layer" : perm_layer,
                "cost" : cost}
        super().__init__(dict)
        
    def equals(self,other):
        if self.dict["st_name"] == other.dict["st_name"]:
            return False
        elif self.dict["cost"] == other.dict["cost"]:
            return False
        
    def applyItem(self):
        utils.debug("Start runCost")
        st_name = self.dict["st_name"]
        st_item = sous_trames.getSTByName(st_name)
        startLayer = params.getOrigPath(self.dict["start_layer"])
        utils.checkFileExists(startLayer,"Dispersion Start Layer ")
        startRaster = st_item.getStartLayerPath()
        params.checkInit()
        extent_layer_path = params.getExtentLayer()
        applyRasterization(startLayer,"geom",startRaster,
                           params.getResolution(),extent_layer_path)
        permRaster = params.getOrigPath(self.dict["perm_layer"])
        cost = self.dict["cost"]
        tmpPath = st_item.getDispersionTmpPath(cost)
        outPath = st_item.getDispersionPath(cost)
        applyRCost(startRaster,permRaster,cost,tmpPath)
        applyFilterGdalFromMaxVal(tmpPath,outPath,cost)
        removeRaster(tmpPath)
        res_layer = qgsUtils.loadRasterLayer(outPath)
        QgsProject.instance().addMapLayer(res_layer)
        utils.debug("End runCost")
            
    def checkItem(self):
        pass
        
class CostModel(DictModel):
    
    def __init__(self):
        super().__init__(self,cost_fields)
    
    @staticmethod
    def mkItemFromDict(dict):
        utils.checkFields(cost_fields,dict.keys())
        item = CostItem(dict["st_name"],dict["start_layer"],dict["perm_layer"],dict["cost"])
        return item
        
    def applyItems(self,indexes):
        utils.debug("[applyItems]")
        if not indexes:
            internal_error("No indexes in Cost applyItems")
        progress_section = progress.ProgressSection("Cost",len(indexes))
        progress_section.start_section()
        for n in indexes:
            i = self.items[n]
            i.applyItem()
            progress_section.next_step()
        progress_section.end_section()
        
    def fromXMLRoot(self,root):
        pass
        
class CostConnector(AbstractConnector):

    def __init__(self,dlg):
        self.dlg = dlg
        costModel = CostModel()
        self.onlySelection = False
        super().__init__(costModel,self.dlg.costView,
                         self.dlg.costAdd,self.dlg.costRemove,
                         self.dlg.costRun,self.dlg.costRunOnlySelection)
        
    def initGui(self):
        self.dlg.costRemove.setToolTip("Supprimer les dispersions sélectionnées")
        self.dlg.costStartLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.costPermRasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        
    def connectComponents(self):
        self.dlg.costSTCombo.setModel(sous_trames.stModel)
        #self.dlg.costStartLayerCombo.layerChanged.connect(self.setStartLayerFromCombo)
        self.dlg.costStartLayer.fileChanged.connect(self.setStartLayer)
        self.dlg.costPermRaster.fileChanged.connect(self.setPermRaster)
        #self.dlg.costPermRasterCombo.layerChanged.connect(self.setPermRasterFromCombo)
        #self.dlg.costRun.clicked.connect(self.applyItems)
        super().connectComponents()
        # self.dlg.costRunSelectionMode.stateChanged.connect(self.switchOnlySelection)
        
    # def applyItems(self):
        # if self.onlySelection:
            # indexes = list(set([i.row() for i in self.view.selectedIndexes()]))
        # else:
            # indexes = range(0,len(self.model.items))
        # utils.debug(str(indexes))
        # self.model.applyItems(indexes)
        
    # def switchOnlySelection(self):
        # new_val = not self.onlySelection
        # utils.debug("setting onlySelection to " + str(new_val))
        # self.onlySelection = new_val
        
    def switchST(self,text):
        st_item = sous_trames.getSTByName(text)
        st_friction_path = st_item.getFrictionPath()
        self.dlg.costPermRaster.lineEdit().setValue(st_friction_path)
        
    def setStartLayer(self,path):
        layer = loadVectorLayer(path,loadProject=True)
        self.dlg.costStartLayerCombo.setLayer(layer)
        
    def setPermRaster(self,path):
        layer = loadRasterLayer(path)
        self.dlg.costPermRasterCombo.setLayer(layer)
        
    def setStartLayerFromCombo(self,layer):
        utils.debug("setStartLayerFromCombo")
        if layer:
            path=pathOfLayer(layer)
            self.dlg.costStartLayer.lineEdit().setValue(path)
        
    def setPermRasterFromCombo(self,layer):
        utils.debug("setPermRasterFromCombo")
        if layer:
            path=pathOfLayer(layer)
            self.dlg.costPermRaster.lineEdit().setValue(path)
        
    def mkItem(self):
        st_name = self.dlg.costSTCombo.currentText()
        if not st_name:
            utils.user_error("No Sous-Trame selected")
        start_layer = self.dlg.costStartLayerCombo.currentLayer()
        if not start_layer:
            utils.user_error("No start layer selected")
        start_layer_path = params.normalizePath(pathOfLayer(start_layer))
        perm_layer = self.dlg.costPermRasterCombo.currentLayer()
        if not perm_layer:
            utils.user_error("No permability layer selected")
        perm_layer_path = params.normalizePath(pathOfLayer(perm_layer))
        cost = str(self.dlg.costMaxVal.value())
        cost_item = CostItem(st_name,start_layer_path,perm_layer_path,cost)
        return cost_item
        