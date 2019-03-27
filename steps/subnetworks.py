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

from PyQt5.QtCore import QVariant, QAbstractTableModel, QModelIndex, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView
#from .abstract_model import AbstractGroupModel, AbstractGroupItem, DictItem, DictModel, AbstractConnector
#from .utils import *

from ..qgis_lib_mc import utils, abstract_model
from . import params

# import params
# import abstract_model
# import utils
import os

st_fields = ["name","descr"]
stModel = None
         
def getSTByName(st_name):
    for st in stModel.items:
        if st.name == st_name:
            return st
    return None
         
def getSTList():
    return [st.dict["name"] for st in stModel.items]
         
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
        
    def getSTPath(self):
        params.checkWorkspaceInit()
        all_st_path = utils.joinPath(params.params.workspace,"SousTrames")
        if not os.path.isdir(all_st_path):
            utils.info("Creating ST directory '" + all_st_path + "'")
            os.makedirs(all_st_path)
        st_path = utils.joinPath(all_st_path,self.name)
        if not os.path.isdir(st_path):
            utils.info("Creating ST directory '" + st_path + "'")
            os.makedirs(st_path)
        return st_path
        
    def getMergedPath(self):
        basename = self.name + "_merged.tif"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
    def getRulesPath(self):
        basename = self.name + "_rules.txt"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
    def getFrictionPath(self):
        basename = self.name + "_friction.tif"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
    def getDispersionPath(self,cost):
        basename = self.name + "_dispersion_" + str(cost) + ".tif"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
    def getDispersionTmpPath(self,cost):
        basename = self.name + "_dispersion_" + str(cost) + "_tmp.tif"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
    def getStartLayerPath(self):
        basename = self.name + "_start.tif"
        st_path = self.getSTPath()
        return utils.joinPath(st_path,basename)
        
        
        
class STModel(abstract_model.DictModel):

    stAdded = pyqtSignal('PyQt_PyObject')
    stRemoved = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        self.parser_name = "STModel"
        super().__init__(self,st_fields)
        
    @staticmethod
    def mkItemFromDict(dict):
        utils.checkFields(st_fields,dict.keys())
        item = STItem(dict["name"],dict["descr"])
        return item
        
    def addItem(self,item):
        utils.debug("ST addItem1, items = " + str(self))
        super().addItem(item)
        utils.debug("ST addItem2, items = " + str(self))
        self.stAdded.emit(item)
        utils.debug("ST addItem3, items = " + str(self))
        
    def removeItems(self,indexes):
        names = [self.items[idx.row()].dict["name"] for idx in indexes]
        utils.debug("names " + str(names))
        super().removeItems(indexes)
        for n in names:
            utils.debug("stRemoved " + str(n))
            self.stRemoved.emit(n)
            
    def flags(self, index):
        if index.column() == 0:
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return flags
        
class STConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg):
        self.dlg = dlg
        self.stModel = STModel()
        super().__init__(self.stModel,self.dlg.stView,
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
