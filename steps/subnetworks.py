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

from PyQt5.QtCore import QVariant, QAbstractTableModel, QModelIndex, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView

from ..qgis_lib_mc import utils, abstract_model
from . import params

#stModel = None
         
class STItem(abstract_model.DictItem):

    def __init__(self,st,descr):
        dict = {"name" : st,
                "descr" : descr}
        self.name = st
        #assert(st_fields == dict.keys())
        super().__init__(dict)
        
    def checkItem(self):
        utils.debug(self.dict["name"])
        if self.dict["name"] == "":
            utils.user_error("Empty sous-trame name")
        
    def equals(self,other):
        return (self.dict["name"] == other.dict["name"])
                
    def getMergedPath(self,st_path):
        basename = self.name + "_merged.tif"
        return utils.joinPath(st_path,basename)
        
    def getRulesPath(self,st_path):
        basename = self.name + "_rules.txt"
        return utils.joinPath(st_path,basename)
        
    def getFrictionPath(self,st_path):
        basename = self.name + "_friction.tif"
        return utils.joinPath(st_path,basename)
        
    def getDispersionPath(self,st_path,cost):
        basename = self.name + "_dispersion_" + str(cost) + ".tif"
        return utils.joinPath(st_path,basename)
        
    def getDispersionTmpPath(self,st_path,cost):
        basename = self.name + "_dispersion_" + str(cost) + "_tmp.tif"
        return utils.joinPath(st_path,basename)
        
    def getStartLayerPath(self,st_path):
        basename = self.name + "_start.tif"
        return utils.joinPath(st_path,basename)
        
        
        
class STModel(abstract_model.DictModel):

    # stAdded = pyqtSignal('PyQt_PyObject')
    # stRemoved = pyqtSignal('PyQt_PyObject')
    
    ST_FIELDS = ["name","descr"]

    def __init__(self,bdModel):
        self.parser_name = "STModel"
        self.is_runnable = False
        self.bdModel = bdModel
        super().__init__(self,self.ST_FIELDS)
        
    def getSTByName(self,st_name):
        for st in self.items:
            if st.name == st_name:
                return st
        return None
        
    def getSTList(self):
        return [st.dict["name"] for st in self.items]
        
    def getSTPath(self,st_name):
        return self.bdModel.paramsModel.getSTPath(st_name)
        
    def getMergedPath(self,st_name):
        basename = st_name + "_merged.tif"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def getRulesPath(self,st_name):
        basename = st_name + "_rules.txt"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def getFrictionPath(self,st_name):
        basename = st_name + "_friction.tif"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def getDispersionPath(self,st_name,cost):
        basename = st_name + "_dispersion_" + str(cost) + ".tif"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def getDispersionTmpPath(self,st_name,cost):
        basename = st_name + "_dispersion_" + str(cost) + "_tmp.tif"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def getStartLayerPath(self,st_name):
        basename = st_name + "_start.tif"
        st_path = self.getSTPath(st_name)
        return utils.joinPath(st_path,basename)
        
    def mkItemFromDict(self,dict):
        utils.checkFields(self.ST_FIELDS,dict.keys())
        item = STItem(dict["name"],dict["descr"])
        return item
        
    def addItem(self,item):
        utils.debug("ST addItem1, items = " + str(self))
        super().addItem(item)
        utils.debug("ST addItem2, items = " + str(self))
        self.bdModel.addST(item)
        #self.stAdded.emit(item)
        utils.debug("ST addItem3, items = " + str(self))
        
    def removeItems(self,indexes):
        names = [self.items[idx.row()].dict["name"] for idx in indexes]
        utils.debug("names " + str(names))
        super().removeItems(indexes)
        for n in names:
            utils.debug("stRemoved " + str(n))
            self.bdModel.removeST(n)
            #self.stRemoved.emit(n)
            
    def flags(self, index):
        if index.column() == 0:
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return flags
        
class STConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg,stModel):
        self.dlg = dlg
        super().__init__(stModel,self.dlg.stView,
                         self.dlg.stAdd,self.dlg.stRemove)
        
    def initGui(self):
        pass
        
    def connectComponents(self):
        super().connectComponents()
        self.model.layoutChanged.emit()
        header = self.dlg.stView.horizontalHeader()     
        header.setStretchLastSection(True)

    def mkItem(self):
        name = self.dlg.stName.text()
        descr = self.dlg.stDescr.text()
        stItem = STItem(name,descr)
        return stItem
