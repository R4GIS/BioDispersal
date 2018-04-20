# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Vector_selection
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

from .utils import *

class VectorSelection:
    
    def __init__(self,layer,expr,group):
        self.layer = layer
        self.expr = expr
        self.group = group
        
    def __str__(self):
        return ("Selection(layer = " + self.layer.name() + ", expr = " + str(self.expr) + ", group " + self.group)
        
    def equals(self,other):
        return (self.layer.name() == other.layer.name() and self.expr == other.expr and self.group == other.group)

        

class VectorSelections:

    def __init__(self,dlg):
        self.dlg = dlg
        self.selections = []
        
    def connectComponents(self):
        self.dlg.groupVectMapLayer.layerChanged.connect(self.updateGroupVectLayer)
        self.dlg.groupVectRun.clicked.connect(self.addSelection)
        
    def updateGroupVectLayer(self,layer):
        self.dlg.groupVectFieldExpr.setLayer(layer)
        
    def selectionExists(self,selection):
        for s in self.selections:
            if selection.equals(s):
                return True
        return False
        
    def addSelection(self):
        layer = self.dlg.groupVectMapLayer.currentLayer()
        fieldExpr = self.dlg.groupVectFieldExpr.expression()
        group = self.dlg.groupVectGroup.currentText()
        selection = VectorSelection(layer,fieldExpr,group)
        if self.selectionExists(selection):
            warn("Selection already exists")
        else:
            debug("Adding selection " + str(selection))
            self.selections.insert(0,selection)
            
        