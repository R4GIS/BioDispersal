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

from PyQt5.QtSql import QSqlRecord, QSqlTableModel, QSqlField
from PyQt5.QtCore import QVariant, QAbstractTableModel, QModelIndex, pyqtSignal
from qgis.gui import QgsFileWidget

from ..qgis_lib_mc import utils, qgsUtils, qgsTreatments, abstract_model
from . import params, classes
         
groups_fields = ["name","descr","geom"]
#groupsConnector = None
groupsModel = None

# def getGroupLayer(grp):
    # groupItem = groupsModel.getGroupByName(out_name)
    # group_layer = groupItem.getLayer()
    # return group_layer
    
# def getGroupByName(groups_name):
    # for group in groupsModel.items:
        # if group.name == groups_name:
            # return group
    # return None

def copyGroupModel(model):
    new_model = GroupModel(None)
    for i in model.items:
        new_model.addItem(i)
    return new_model
    
# def getGroupStorage(grp):
    # groupItem = groupsModel.getGroupByName(out_name)
    # group_storage = groupItem.dict["layer"]
    # return group_storage
    
class GroupItem(abstract_model.DictItem):
    
    def __init__(self,group,descr,geom):
        if not geom:
            geom = "No geometry"
        dict = {"name" : group,
                "descr" : descr,
                "geom" : geom}
        #assert(groups_fields == dict.keys())
        self.name = group
        #self.in_layer = None
        self.vectorLayer = None
        self.rasterLayer = None
        super().__init__(dict)
        
    def checkItem(self):
        prefix="Group"
        utils.checkName(self,prefix)
        utils.checkDescr(self,prefix)
        
    def checkGeom(self,geom):
        if self.dict["geom"] != geom:
            utils.user_error("Incompatible geometries for group '"
                             + self.dict["name"] + "' : "
                             + self.dict["geom"] + " vs " + str(geom))
        
    def equals(self,other):
        return (self.dict["name"] == other.dict["name"])
        
    def getVectorPath(self,grp_path):
        basename = self.name + "_vector.shp"
        return utils.joinPath(grp_path,basename)
        
    def getRasterPath(selfgrp_path):
        basename = self.name + "_raster.tif"
        return utils.joinPath(grp_path,basename)
        
    def getRasterTmpPath(selfgrp_path):
        basename = self.name + "_raster_tmp.tif"
        return utils.joinPath(grp_path,basename)
        
    def saveVectorLayer(selfgrp_path):
        vector_path = self.getVectorPath(grp_path)
        qgsUtils.writeShapefile(self.vectorLayer,vector_path)
        
    # def getReclassDict(self):
        # reclass_dict = {}
        # group_name = self.dict["name"]
        # group_classes = [  ]
        # for cls_item in classes.classModel.items:
            # group_name = self.dict["name"]
            # if cls_item.dict["group"] == group_name:
                # class_name = cls_item.dict["name"]
                # if group_name not in class_name:
                    # utils.internal_error("Inconsistent class/group : " + str(class_name) + " - " + str(group_name))
                # len_grp = len(group_name)
                # assert(len(class_name) > len_grp)
                # val = class_name[len_grp+1:]
                # reclass_dict[val] = cls_item.dict["code"]
        # assert(len(reclass_dict) > 0)
        # return reclass_dict
            
    def applyRasterizationItem(self):
        utils.debug("[applyRasterizationItem]")
        field = "Code"
        group_name = self.dict["name"]
        in_path = self.getVectorPath()
        out_path = self.getRasterPath()
        params.checkInit()
        resolution = params.getResolution()
        extent_path = params.getExtentLayer()
        qgsTreatments.applyRasterizationCmd(in_path,field,out_path,extent_path,resolution,
                                         load_flag=True,to_byte=True)
        
class GroupModel(abstract_model.DictModel):

    # groupAdded = pyqtSignal('PyQt_PyObject')
    # groupRemoved = pyqtSignal('PyQt_PyObject')

    def __init__(self,bdModel):
        self.parser_name = "GroupModel"
        self.is_runnable = False
        self.bdModel = bdModel
        super().__init__(self,groups_fields)
        
    def mkItemFromDict(self,dict):
        utils.checkFields(groups_fields,dict.keys())
        item = GroupItem(dict["name"],dict["descr"],dict["geom"])
        return item
        
    def getGroupByName(self,name):
        for i in self.items:
            if i.dict["name"] == name:
                return i
        None
        #utils.internal_error("Could not find groups '" + name + "'")
             
    def groupExists(self,name):
        grp_item = self.getGroupByName(name)
        return (grp_item != None)
             
    def addItem(self,item):
        super().addItem(item)
        if self.bdModel:
            self.bdModel.addGroup(item)
        #self.groupAdded.emit(item)
        
    def removeItems(self,indexes):
        super().removeItems(indexes)
        if self.bdModel:
            names = [self.items[idx.row()].dict["name"] for idx in indexes]
            for n in names:
                self.bdModel.removeGroup(g)
            # self.groupRemoved.emit(n)
            # classes.classModel.removeFromGroupName(n)
            
    def removeGroupFromName(self,name):
        self.items = [item for item in self.items if item.dict["name"] != name]
        self.layoutChanged.emit()
            
    def getGroupPath(self,name):
        return self.bdModel.paramsModel.getGroupPath(name)
        
    def getVectorPath(self,name):
        basename = name + "_vector.shp"
        grp_path = self.getGroupPath(name)
        return utils.joinPath(grp_path,basename)
        
    def getRasterPath(self,name):
        basename = name + "_raster.tif"
        grp_path = self.getGroupPath(name)
        return utils.joinPath(grp_path,basename)
        
    def getRasterTmpPath(self,name):
        basename = name + "_raster_tmp.tif"
        grp_path = self.getGroupPath(name)
        return utils.joinPath(grp_path,basename)
            
    # def applyRasterizationItem(self,item,context=None,feedback=None):
        # feedback.pushDebugInfo("[applyRasterizationItem]")
        # field = "Code"
        # group_name = item.dict["name"]
        # in_path = self.getVectorPath(item)
        # out_path = self.getRasterPath(item)
        # self.bdModel.paramsModel.checkInit()
        # resolution = self.bdModel.paramsModel.getResolution()
        # extent = self.bdModel.paramsModel.getExtentCoords()
        # qgsTreatments.applyRasterization(in_path,field,out_path,extent,resolution,
                                         # field=field,out_type=Qgis.UInt16,all_touch=True,
                                         # context=context,feedback=feedback)

class GroupConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg,groupsModel):
        self.dlg = dlg
        super().__init__(groupsModel,self.dlg.groupsView,
                        self.dlg.selectionGroupAdd,self.dlg.groupsRemove)
        # super().__init__(groupsModel,self.dlg.groupsView,
                        # self.dlg.groupsAdd,self.dlg.groupsRemove)
        
    def initGui(self):
        pass#self.dlg.groupFrame.hide()
        
    def connectComponents(self):
        super().connectComponents()
        self.dlg.selectionGroupCombo.currentTextChanged.connect(self.setGroupName)

    def mkItem(self):
        name = self.dlg.selectionGroupName.text()
        self.dlg.selectionGroupCombo.setCurrentText(name)
        descr = self.dlg.selectionGroupDescr.text()
        selection_in_layer = self.dlg.selectionInLayerCombo.currentLayer()
        if selection_in_layer:
            if self.dlg.selectionLayerFormatVector.isChecked():
                geom = qgsUtils.getLayerSimpleGeomStr(selection_in_layer)
            else:
                geom = "Raster"
            groupsItem = GroupItem(name,descr,geom)
            return groupsItem
        utils.user_error("No layer selected")
        
    def addItem(self,item):
        super().addItem()
        self.dlg.selectionGroupCombo.setCurrentIndex(len(self.model.items)-1)
        
    def setGroupName(self,text):
        utils.debug("setGroupName " + str(text))
        grp_item = self.model.getGroupByName(text)
        self.dlg.selectionGroupName.setText(grp_item.dict["name"])
        self.dlg.selectionGroupDescr.setText(grp_item.dict["descr"])
        
