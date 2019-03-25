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

import copy
import subprocess
import os.path
import xml.etree.ElementTree as ET

from qgis.core import QgsProject
from PyQt5.QtCore import QModelIndex, pyqtSlot
from PyQt5.QtGui import QIcon

from ..qgis_lib_mc import utils, qgsUtils, xmlUtils, qgsTreatments, progress, config_parsing
from . import params, subnetworks, groups
# import abstract_model
# import utils
# import xmlUtils
# import qgsUtils
# import params
# import sous_trames
# import groups
# import progress
# import qgsTreatments
# import config_parsing

fusionModel = None
fusion_fields = ["name","descr"]
        
@pyqtSlot()
def catchSTRemoved(name):
    fusionModel.removeSTFromName(name)
        
@pyqtSlot()
def catchSTAdded(item):
    fusionModel.setCurrentST(item.dict["name"])
    utils.debug("ST addItem4, items = " + str(subnetworks.stModel))
        
@pyqtSlot()
def catchGroupRemoved(name):
    global fusionModel
    for st, grp_model in fusionModel.st_groups.items():
        grp_model.removeGroupFromName(name)
        
# @pyqtSlot()
# def catchGroupAdded(item):
    # fusionModel.addGroup(item.dict["name"])
        
class FusionModel(abstract_model.AbstractGroupModel):
    
    def __init__(self):
        self.st_groups = {}
        self.current_st = None
        self.current_model = None
        super().__init__(self,fusion_fields)
        
    def __str__(self):
        res = ""
        for st, grp_model in self.st_groups.items():
            res += st + " : "
            for g in grp_model.items:
                res += g.dict["name"] + ", "
            res += "\n"
        return res
        
    def getItems(self):
        return self.current_model.items
        
    def getCurrModel(self):
        return self.st_groups[self.st_current_st]
        
    def setCurrentST(self,st):
        utils.debug("setCurrentST " + str(st))
        utils.debug(str(self))
        self.current_st = st
        if st not in self.st_groups: 
            self.loadAllGroups()
        else:
            self.current_model = self.st_groups[st]
            self.current_model.layoutChanged.emit()
        utils.debug(str(self))
        utils.debug("ST addItem, items = " + str(self))
        
    def loadAllGroups(self):
        utils.debug("[loadAllGroups]")
        if self.current_st:
            utils.debug("Current st = " + str(self.current_st))
            if self.current_st not in self.st_groups:
                self.st_groups[self.current_st] = groups.copyGroupModel(groups.groupsModel)
                self.current_model = self.st_groups[self.current_st]
            for grp_item in groups.groupsModel.items:
                utils.debug("grp_item = " + str(grp_item))
                if not self.current_model.groupExists(grp_item):
                    utils.debug("Adding group " + str(grp_item.dict["name"])
                                + " to " + str(self.current_st))
                    self.current_model.addItem(grp_item)
            #self.st_groups[self.current_st] = groups.copyGroupModel(groups.groupsModel)
            #self.current_model = self.st_groups[self.current_st]
        else:
            utils.user_error("No sous-trame selected")
        
    def toXML(self,indent=""):
        xmlStr = indent + "<" + self.__class__.__name__ + ">\n"
        for st, grp in self.st_groups.items():
            xmlStr += indent + " <ST name=\"" + st + "\">\n"
            xmlStr += grp.toXML(indent=indent + "  ")
            xmlStr += indent + " </ST>"
        xmlStr += indent + "</" + self.__class__.__name__ + ">"
        return xmlStr
    
    def fromXMLRoot(self,root):
        #checkFields(fusion_fields,dict.keys())
        utils.debug("[fromXMLRoot] FusionModel")
        # utils.debug("config_models " + str(config_parsing.config_models))
        eraseFlag = xmlUtils.getNbChildren(root) == 0
        if eraseFlag:
            utils.warn("Nothing to do for FusionModel")
            pass#self.items = []
        for st_root in root:
            st_name = st_root.attrib["name"]
            utils.debug("parsing '" + str(st_name) + "' sous trame")
            # utils.debug("config_models " + str(config_parsing.config_models))
            self.current_st = st_name
            nb_groups = xmlUtils.getNbChildren(st_root)
            if nb_groups == 0:
                utils.warn("No groups for st " + str(st_name))
            for grp in st_root:
                # utils.debug("coucou")
                # utils.debug("config_models " + str(config_parsing.config_models))
                #grp_model = config_parsing.parseModel(grp,new_model=True)
                grp_model = groups.GroupModel()
                for grp_item in grp:
                    item = grp_model.mkItemFromDict(grp_item.attrib)
                    grp_model.addItem(item)
                if not grp_model:
                    utils.internal_error("Could not parse group model for " + st_name)
                utils.debug("Setting groups for st " + str(st_name))
                self.st_groups[st_name] = grp_model
                self.current_model = grp_model
                self.current_model.layoutChanged.emit()
                grp_model.layoutChanged.emit()
        self.layoutChanged.emit()
        
    def testFunc(self,root):
        utils.debug("[testFunc]")
        utils.debug("config_models " + str(config_parsing.config_models))
        
        
    def applyItems(self,indexes):
        utils.info("Applying merge")
        progress.progressConnector.clear()
        params.checkInit()
        res = str(params.getResolution())
        extent_coords = params.getExtentCoords()
        #for st in reversed(list(self.st_groups.keys())):
        progress_section = progress.ProgressSection("Fusion",len(self.st_groups))
        progress_section.start_section()
        for st in self.st_groups.keys():
            st_item = subnetworks.getSTByName(st)
            groups = self.st_groups[st]
            if not groups.items:
                utils.warn("No layer for group for subnetwork '" + str(st) + "', ignoring.")
                continue
            else:
                utils.info("groups = " + str(groups.items))
            utils.debug("apply fusion to " + st)
            utils.debug(str([g.dict["name"] for g in groups.items]))
            grp_args = [g.getRasterPath() for g in reversed(groups.items)]
            utils.debug(str(grp_args))
            out_path = st_item.getMergedPath()
            if os.path.isfile(out_path):
                qgsUtils.removeRaster(out_path)
            qgsTreatments.applyGdalMerge(grp_args,out_path,load_flag=True)
            #cmd_args = ['gdal_merge.bat',
            #            '-o', out_path,
            #            '-of', 'GTiff',
            #            '-ot','Int32',
            #            '-n', qgsTreatments.nodata_val,
            #            '-a_nodata', qgsTreatments.nodata_val]
            #cmd_args = cmd_args + grp_args
            #utils.executeCmd(cmd_args)
            #p = subprocess.Popen(cmd_args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            #res_layer = qgsUtils.loadRasterLayer(out_path)
            #QgsProject.instance().addMapLayer(res_layer)
            progress_section.next_step()
        progress_section.end_section()
        utils.info("Merge succesfully applied")
            
    # def updateItems(self,i1,i2):
        # k = self.current_st
        # self.current_model.items[i1], self.current_model.items[i2] = self.current_model.items[i2], self.current_model.items[i1]
        # self.current_model.layoutChanged.emit()
        
    # def upgradeElem(self,idx):
        # row = idx.row()
        # utils.debug("upgradeElem " + str(row))
        # if row > 0:
            # self.swapItems(row -1, row)
            
            
    def removeSTFromName(self,name):
        st_groups = self.st_groups.pop(name,None)
        if not st_groups:
            utils.warn("Deleting sous-trame '" + name + "' in fusion model but could not find it")
        
    def downgradeElem(self,row):
        #row = idx.row()
        utils.debug("downgradeElem " + str(row))
        if row < len(self.current_model.items) - 1:
            self.swapItems(row, row + 1)
            
    def swapItems(self,i1,i2):
        self.current_model.swapItems(i1,i2)
        #self.current_model.layoutChanged.emit()
        self.layoutChanged.emit()
        
    def removeItems(self,index):
        utils.debug("[removeItems] nb of items = " + str(len(self.current_model.items))) 
        self.current_model.removeItems(index)
        self.current_model.layoutChanged.emit()
        
    def addItem(self,item):
        utils.debug("[addItemFusion]")
        self.current_model.addItem(item)
        self.current_model.layoutChanged.emit()
        
    def data(self,index,role):
        #utils.debug("[dataFusionModel]")
        return self.current_model.data(index,role)
        
    def rowCount(self,parent=QModelIndex()):
        if self.current_model:
            return self.current_model.rowCount(parent)
        else:
            return 0
        
    def columnCount(self,parent=QModelIndex()):
        if self.current_model:
            return self.current_model.columnCount(parent)
        else:
            return 0
        

class FusionConnector(abstract_model.AbstractConnector):
    
    def __init__(self,dlg):
        self.dlg = dlg
        self.models = {}
        fusionModel = FusionModel()
        self.onlySelection = False
        super().__init__(fusionModel,self.dlg.fusionView,
                         None,self.dlg.fusionRemove,
                         self.dlg.fusionRun,self.dlg.fusionRunOnlySelection)
                         
    def initGui(self):
        pass
                         
    def connectComponents(self):
        super().connectComponents()
        subnetworks.stModel.stRemoved.connect(catchSTRemoved)
        subnetworks.stModel.stAdded.connect(catchSTAdded)
        groups.groupsModel.groupRemoved.connect(catchGroupRemoved)
        self.dlg.fusionST.setModel(subnetworks.stModel)
        #self.dlg.fusionGroup.setModel(groups.groupsModel)
        self.dlg.fusionST.currentTextChanged.connect(self.changeST)
        #self.dlg.fusionLoadGroups.clicked.connect(self.model.loadAllGroups)
        self.dlg.fusionLoadGroups.clicked.connect(self.loadAllGroups)
        #self.dlg.fusionRun.clicked.connect(self.model.applyItems)
        self.dlg.fusionUp.clicked.connect(self.upgradeItem)
        self.dlg.fusionDown.clicked.connect(self.downgradeItem)
        
    def loadAllGroups(self):
        utils.debug("connector loadAllGroups")
        self.model.loadAllGroups()
        self.changeST(self.model.current_st)
        #self.model.current_model.layoutChanged.emit()
        #self.dlg.fusionView.setModel(self.model.current_model)
        
    def changeST(self,st):
        self.model.setCurrentST(st)
        self.dlg.fusionView.setModel(self.model.current_model)
        