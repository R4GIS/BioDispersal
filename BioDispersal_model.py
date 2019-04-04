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

from .qgis_lib_mc import utils
from .steps import (params, subnetworks, groups, classes, selection,
                    fusion, friction, ponderation, cost)

class BioDispersalModel:

    def __init__(self,context,feedback):
        self.parser_name = "ModelConfig"
        self.context = None
        self.feedback = feedback
        utils.debug("feedback bd = " + str(feedback))
        self.paramsModel = params.ParamsModel(self)
        self.stModel = subnetworks.STModel(self)
        self.selectionModel = selection.SelectionModel(self)
        self.classesModel = classes.ClassModel(self)
        self.groupsModel = groups.GroupModel(self)
        self.fusionModel = fusion.FusionModel(self)
        self.frictionModel = friction.FrictionModel(self)
        self.ponderationModel = ponderation.PonderationModel(self)
        self.costModel = cost.CostModel(self)
        self.models = [self.paramsModel, self.stModel, self.selectionModel,
                       self.fusionModel, self.frictionModel, self.ponderationModel,
                       self.costModel]
        self.parser_name = "BioDispersalModel"
        
    def checkWorkspaceInit(self):
        self.paramsModel.checkWorkspaceInit()
            
    # Returns relative path w.r.t. workspace directory.
    # File separator is set to common slash '/'.
    def normalizePath(self,path):
        return self.paramsModel.normalizePath(path)
            
    # Returns absolute path from normalized path (cf 'normalizePath' function)
    def getOrigPath(self,path):
        return self.paramsModel.getOrigPath(path)
    
    def mkOutputFile(self,name):
        return self.paramsModel.mkOutputFile(name)
        
    def runModel(self):
        utils.debug("feedback fs rm = " + str(self.feedback))
        for model in self.models:
            if model.isRunnable:
                model.applyItemsWithContext(self.context,self.feedback)
                
    """ Model update """
    
    def addST(self,item):
        self.frictionModel.addSTItem(item)
        self.fusionModel.setCurrentST(item.dict["name"])
        
    def deleteST(self,name):
        self.frictionModel.removeSTFromName(name)
        self.fusionModel.removeSTFromName(name)
        
    def addClass(self,item):
        self.frictionModel.addClassItem(item)        
        
    def deleteClass(self,name):
        self.frictionModel.removeClassFromName(name)
        
    def addGroup(self,item):
        pass
        
    def deleteGroup(self,name):
        for st, grp_model in self.fusionModel.st_groups.items():
            grp_model.removeGroupFromName(name)
        
    """ XML functions """
        
    def toXML(self,indent=""):
        xmlStr = indent + "<" + self.parser_name + ">"
        new_indent = " "
        for model in models:
            xmlStr += "\n" + indent + "</" + self.parser_name + ">"
        return xmlStr
        
    def getModelFromParserName(self,name):
        for model in self.models:
            if model.parser_name == name:
                return model
        return None
        
    def fromXMLRoot(self,root):
        for child in root:
            utils.debug("tag = " + str(child.tag))
            model = self.getModelFromParserName(child.tag)
            if model:
                model.fromXMLRoot(child)
                model.layoutChanged.emit()
