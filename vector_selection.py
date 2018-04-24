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

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import QVariant
from qgis.gui import QgsFileWidget
#from qgis.gui import *
from qgis.core import *

from .utils import *
from .qgsUtils import *

class VectorSelection:
    
    def __init__(self,id,in_layer,expr,group,out_layer):
        self.id = id
        self.in_layer = in_layer
        self.expr = expr
        self.group = group
        self.out_layer = out_layer
        self.out_name = os.path.basename(out_layer)
        
    def __str__(self):
        return ("Selection(layer = " + self.in_layer.name()
                + ", expr = " + str(self.expr)
                + ", group = " + self.group
                + ", out layer = " + self.out_layer)
        
    def equals(self,other):
        return (self.in_layer.name() == other.in_layer.name()
                and self.expr == other.expr
                and self.group == other.group
                and self.out_layer == other.out_layer)
        
    def checkParams(self):
        #checkFileExists(self.out_layer)
        outdir = os.path.dirname(self.out_layer)
        if not os.path.isdir(outdir):
            user_error("Directory '" + outdir + "' does not exist")
        if os.path.isfile(self.out_layer):
            user_error("File '" + self.out_layer + "' already exists")


class VectorSelections:

    def __init__(self,dlg):
        self.dlg = dlg
        self.selections = []
        self.displayedSelections = []
        self.filter = ""
        
    def connectComponents(self):
        self.dlg.groupVectMapLayer.layerChanged.connect(self.updateGroupVectLayer)
        self.dlg.groupVectAdd.clicked.connect(self.addSelection)
        self.dlg.groupVectRefresh.clicked.connect(self.refreshSelections)
        self.dlg.groupVectDelete.clicked.connect(self.deleteSelection)
        self.dlg.groupVectFilter.textChanged.connect(self.setFilter)
        self.dlg.groupVectGroupCombo.currentTextChanged.connect(self.setGroup)
        self.dlg.groupVectRun.clicked.connect(self.applySelections)
        
        self.dlg.groupVectOutLayerDir.setStorageMode(QgsFileWidget.GetDirectory)
        
    #def unload(self):
    #    self.selections = []
    #    self.displayedSelections = []
    #    self.filter = ""
    
    def getSelection(self,id):
        for s in self.selections:
            if s.id == id:
                return s
        return None
        
    def getSelectionsByOutLayer(self):
        res = {}
        for s in self.selections:
            if s.out_layer in res:
                res[s.out_layer].append(s)
            else:
                res[s.out_layer] = [s]
        return res
        
    def updateGroupVectLayer(self,layer):
        self.dlg.groupVectFieldExpr.setLayer(layer)
        
    def setFilter(self,text):
        self.filter = text
        self.refreshSelections()
        
    def setGroup(self,text):
        self.dlg.groupVectGroupLine.setText(text)
        
    def selectionExists(self,selection):
        for s in self.selections:
            if selection.equals(s):
                return True
        return False
        
    def addSelection(self):
        debug("[addSelection]")
        id = len(self.selections)
        layer = self.dlg.groupVectMapLayer.currentLayer()
        fieldExpr = self.dlg.groupVectFieldExpr.expression()
        group = self.dlg.groupVectGroupLine.text()
        outdir = self.dlg.groupVectOutLayerDir.filePath()
        outname = self.dlg.groupVectOutLayerName.text()
        outlayer = os.path.join(outdir,outname)
        selection = VectorSelection(id,layer,fieldExpr,group,outlayer)
        #selection.checkParams()
        if self.selectionExists(selection):
            warn("Selection already exists")
        else:
            debug("Adding selection " + str(selection))
            self.selections.append(selection)
            self.refreshSelections()
            
    def clearTable(self):
        debug("clearTable")
        self.dlg.groupVectTable.setRowCount(0)
            
    def refreshSelections(self):
        debug("[refreshSelections]")
        self.displayedSelections = []
        self.clearTable()
        for s in self.selections:
            debug("lauer " + s.in_layer.name())
            if self.filter in s.in_layer.name():
                debug("filter ok")
                n = self.dlg.groupVectTable.rowCount()
                self.displayedSelections.append(s)
                self.dlg.groupVectTable.insertRow(n)
                self.dlg.groupVectTable.setItem(n,0,QTableWidgetItem(str(s.id)))
                self.dlg.groupVectTable.setItem(n,1,QTableWidgetItem(s.in_layer.name()))
                self.dlg.groupVectTable.setItem(n,2,QTableWidgetItem(s.expr))
                self.dlg.groupVectTable.setItem(n,3,QTableWidgetItem(s.group))
                #self.dlg.groupVectTable.setItem(n,4,QTableWidgetItem(s.out_layer))
            else:
                debug("filter ko")
                
    def deleteSelection(self):
        debug("deleteSelection")
        row = self.dlg.groupVectTable.currentRow()
        if row >= 0:
            debug("Removing row " + str(row))
            id = int(self.dlg.groupVectTable.item(row,0).text())
            selection = self.getSelection(id)
            self.selections.remove(selection)
            self.displayedSelections.remove(selection)
            for s in self.selections:
                if s.id >= id:
                    s.id -= 1
            #self.dlg.groupVectTable.removeRow(row)
            self.refreshSelections()
        else:
            warn("No row selected")
        
    def applySelections(self):
        for k,selections in self.getSelectionsByOutLayer().items():
            debug("[applySelections] " + str(k))
            tmp_s = selections[0]
            oldattributeList = tmp_s.in_layer.dataProvider().fields().toList()
            debug(str(oldattributeList))
            k_layer = createLayerFromExisting(tmp_s.in_layer,tmp_s.out_name)
            pr = k_layer.dataProvider()
            group_field = QgsField("Group", QVariant.String)
            orig_field = QgsField("Origin", QVariant.String)
            new_fields = QgsFields()
            new_fields.append(group_field)
            new_fields.append(orig_field)
            #k_attributes = new_fields.allAttributesList()
            #pr.addAttributes(k_attributes)
            pr.addAttributes([group_field,orig_field])
            k_layer.updateFields()
            debug("fields = " + str(len(pr.fields())))
            for s in selections:
                debug("[applySelections] " + str(s.id))
                checkLayersCompatible(k_layer,s.in_layer)
                if s.expr:
                    features = s.in_layer.getFeatures(QgsFeatureRequest().setFilterExpression(s.expr))
                else:
                    features = s.in_layer.getFeatures(QgsFeatureRequest())
                new_f = QgsFeature(new_fields)
                for f in features:
                    new_f.setGeometry(f.geometry())
                    new_f["Group"] = s.group
                    new_f["Origin"] = s.in_layer.name()
                    res = pr.addFeature(new_f)
                    if not res:
                        internal_error("ko")
                    k_layer.updateExtents()
            #k_layer.commitChanges()
            #k_layer.updateExtents()
            debug("nb fields = " + str(len(pr.fields())))
            debug("nb features = " + str(pr.featureCount()))
            QgsProject.instance().addMapLayers([k_layer])
            #writeShapefile(k_layer,k)
            
            
    # def applySelections2(self):
        # tmp_s = self.selections[0]
        # in_layer = tmp_s.in_layer
        # in_geom_type=in_layer.wkbType()
        # debug("geom type = " + str(in_geom_type))
        # in_geom_type_str = QgsWkbTypes.displayString(in_geom_type)
        # debug("geom type = " + in_geom_type_str)
        # vl = QgsVectorLayer(in_geom_type_str, "temporary_points", "memory")
        # pr = vl.dataProvider()
        # pr.addAttributes([QgsField("name", QVariant.String),QgsField("age",  QVariant.Int),QgsField("size", QVariant.Double)])
        # vl.updateFields()
        # old_feats = in_layer.getFeatures()
        # for old_feat in old_feats:
            # old_f = old_feat
        # assert(old_f.hasGeometry())
        # assert(old_f.isValid())
        # fet = QgsFeature()
        # debug(str(old_f.geometry().asWkt()))
        # fet.setGeometry(old_f.geometry())
        # fet.setAttributes(["Johny", 2, 0.3])
        # pr.addFeatures([fet])
        # vl.updateExtents()
        # info ("fields: " + str(len(pr.fields())))
        # info ("features :" + str(pr.featureCount()))
        
