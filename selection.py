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
from qgis.core import QgsMapLayerProxyModel, QgsCoordinateTransform, QgsProject, QgsGeometry
from PyQt5.QtGui import QIcon
from .abstract_model import AbstractGroupModel, AbstractGroupItem, DictItem, DictModel, AbstractConnector
from .utils import *
from .qgsUtils import *
import params
import classes
import groups
from .qgsTreatments import *

selection_fields = ["in_layer","expr","class","group"]

# SelectionItem implements DictItem and contains below fields :
#   - 'in_layer' : input layer from which features are selected
#   - 'expr' : expression on which selection is performerd
#                (all features are selected if empty expression)
#   - 'class' : class assigned to selection item
#   - 'group' : group assigned to selection item
class SelectionItem(DictItem):

    def __init__(self,in_layer,expr,cls,group):#,class_descr="",group_descr="",code=None):
        dict = {"in_layer" : in_layer,
                "expr" : expr,
                "class" : cls,
                "group" : group}
        self.is_vector = isVectorPath(in_layer)
        self.is_raster = isRasterPath(in_layer)
        super().__init__(dict)
        
    def checkItem(self):
        pass
        
    def applyItem(self):
        if self.is_vector:
            self.applyVectorItem()
            #self.applyRasterItem()
        elif self.is_raster:
            self.applyRasterItem()
        else:
            user_error("Unkown format for file '" + str(self.dict["in_layer"]))
        
    # Selection is performed in 3 steps :
    #   1) creates group layer (group_vector.shp) if not existing with below fields :
    #       - 'Origin' : source layer name
    #       - 'Class' : class assigned to this selection
    #       - 'Code' : code assigned to this class
    #   2) select features
    #   3) add features to group layer
    def applyVectorItem(self):
        debug("classModel = " + str(classes.classModel))
        in_layer_path = params.getOrigPath(self.dict["in_layer"])
        checkFileExists(in_layer_path)
        in_layer = loadVectorLayer(in_layer_path)
        expr = self.dict["expr"]
        class_name = self.dict["class"]
        class_item = classes.getClassByName(class_name)
        if not class_item:
            utils.user_error("No class named '" + class_name + "'")
        group_name = self.dict["group"]
        group_item = groups.getGroupByName(group_name)
        if not group_item:
            utils.user_error("No group named '" + group_name + "'")
        out_vector_layer_path = group_item.getVectorPath()
        if os.path.isfile(out_vector_layer_path):
            out_vector_layer = group_item.vectorLayer
        else:
            # group layer creation
            out_vector_layer = createLayerFromExisting(in_layer,class_name + "_vector",
                                                       geomType=None,crs=params.params.getCrsStr())
            group_item.vectorLayer = out_vector_layer
            orig_field = QgsField("Origin", QVariant.String)
            class_field = QgsField("Class", QVariant.String)
            code_field = QgsField("Code", QVariant.String)
            out_vector_layer.dataProvider().addAttributes([orig_field,class_field,code_field])
            out_vector_layer.updateFields()
        pr = out_vector_layer.dataProvider()
        in_crs = in_layer.sourceCrs()
        out_crs = out_vector_layer.sourceCrs()
        debug("in_crs : " + str(in_crs.description()))
        debug("out_crs : " + str(out_crs.description()))
        debug("in_crsid : " + str(in_crs.authid()))
        debug("out_crsid : " + str(out_crs.authid()))
        if in_crs.authid() == out_crs.authid():
            transform_flag = False
        else:
            transform_flag = True
            transformator = QgsCoordinateTransform(in_crs,out_crs,QgsProject.instance())
        if expr:
            feats = in_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))
        else:
            feats = in_layer.getFeatures(QgsFeatureRequest())
        fields = out_vector_layer.fields()
        new_f = QgsFeature(fields)
        tmp_cpt = 0
        for f in feats:
            tmp_cpt += 1
            geom = f.geometry()
            if transform_flag:
                transf_res = geom.transform(transformator)#,QgsCoordinateTransform.ForwardTransform)
                if transf_res != QgsGeometry.Success:
                    internal_error("Could not transform geometry : " + str(trasf_res))
            new_f.setGeometry(geom)
            new_f["Origin"] = in_layer.name()
            new_f["Class"] = class_name
            new_f["Code"] = class_item.dict["code"]
            res = pr.addFeature(new_f)
            if not res:
                internal_error("addFeature failed")
            out_vector_layer.updateExtents()
        debug("length(feats) = " + str(tmp_cpt))
        group_item.vectorLayer = out_vector_layer
        if tmp_cpt == 0:
            warn("No entity selected from '" + str(self) + "'")
        group_item.saveVectorLayer()
        
        
class SelectionModel(DictModel):
    
    def __init__(self):
        super().__init__(self,selection_fields)
        
    @staticmethod
    def mkItemFromDict(dict):
        checkFields(selection_fields,dict.keys())
        item = SelectionItem(dict["in_layer"],dict["expr"],dict["class"],dict["group"])
        return item

    # Selections are performed group by group.
    # Group vector layers are then rasterized (group_vector.shp to group_raster.tif)
    def applyItems(self,indexes):
        utils.debug("applyItems " + str(indexes))
        params.checkInit()
        selectionsByGroup = {}
        for n in indexes:
            i = self.items[n]
            grp = i.dict["group"]
            if grp in selectionsByGroup:
                selectionsByGroup[grp].append(i)
            else:
                selectionsByGroup[grp] = [i]
        for g, selections in selectionsByGroup.items():
            grp_item = groups.getGroupByName(g)
            if not grp_item:
                utils.user_error("Group '" + g + "' does not exist")
            grp_vector_path = grp_item.getVectorPath()
            if os.path.isfile(grp_vector_path):
                removeFile(grp_vector_path)
            for s in selections:
                s.applyVectorItem()
            grp_item.applyRasterizationItem()
        
class SelectionConnector(AbstractConnector):

    def __init__(self,dlg):
        self.dlg = dlg
        selectionModel = SelectionModel()
        self.onlySelection = False
        super().__init__(selectionModel,self.dlg.selectionView,
                        None,self.dlg.selectionRemove)
                        
    def initGui(self):
        upIcon = QIcon(':plugins/eco_cont/icons/up-arrow.png')
        downIcon = QIcon(':plugins/eco_cont/icons/down-arrow.png')
        self.dlg.selectionUp.setIcon(upIcon)
        self.dlg.selectionDown.setIcon(downIcon)
        self.activateFieldMode()
        self.activateClassDisplay()
        self.dlg.selectionInLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        
    def connectComponents(self):
        super().connectComponents()
        # In layer
        self.dlg.selectionInLayerCombo.layerChanged.connect(self.setInLayerFromCombo)
        self.dlg.selectionInLayer.fileChanged.connect(self.setInLayer)
        # Expr
        self.dlg.fieldSelectionMode.stateChanged.connect(self.switchFieldMode)
        self.dlg.exprSelectionMode.stateChanged.connect(self.switchExprMode)
        # Class
        self.dlg.selectionClassCombo.setModel(classes.classModel)
        self.dlg.selectionClassCombo.currentTextChanged.connect(self.setClass)
        self.dlg.classDisplay.stateChanged.connect(self.switchClassDisplay)
        # Group
        self.dlg.selectionGroupCombo.setModel(groups.groupsModel)
        self.dlg.groupDisplay.stateChanged.connect(self.switchGroupDisplay)
        # Selections
        self.dlg.selectionAdd.clicked.connect(self.addItems)
        self.dlg.selectionUp.clicked.connect(self.upgradeItem)
        self.dlg.selectionDown.clicked.connect(self.downgradeItem)
        self.dlg.selectionRunSelectionMode.stateChanged.connect(self.switchOnlySelection)
        self.dlg.selectionRun.clicked.connect(self.applyItems)
        
    def applyItems(self):
        if self.onlySelection:
            indexes = list(set([i.row() for i in self.view.selectedIndexes()]))
        else:
            indexes = range(0,len(self.model.items))
        utils.debug(str(indexes))
        self.model.applyItems(indexes)
        
    def switchOnlySelection(self):
        new_val = not self.onlySelection
        utils.debug("setting onlySelection to " + str(new_val))
        self.onlySelection = new_val
        
    def setClass(self,text):
        cls_item = classes.getClassByName(text)
        self.dlg.selectionClassName.setText(cls_item.dict["name"])
        self.dlg.selectionClassDescr.setText(cls_item.dict["descr"])
        
    def setGroup(self,text):
        grp_item = groups.getGroupByName(text)
        self.dlg.selectionGroupName.setText(grp_item.dict["name"])
        self.dlg.selectionGroupDescr.setText(grp_item.dict["descr"])
                        
    def setInLayerFromCombo(self,layer):
        debug("setInLayerFromCombo")
        debug(str(layer.__class__.__name__))
        if layer:
            path=pathOfLayer(layer)
            self.dlg.selectionExpr.setLayer(layer)
            self.dlg.selectionField.setLayer(layer)
        else:
            warn("Could not load selection in layer")
        
    def setInLayer(self,path):
        debug("setInLayer " + path)
        loaded_layer = loadVectorLayer(path,loadProject=True)
        if loaded_layer == None:
            user_error("Could not load layer '" + path + "'")
        if not loaded_layer.isValid():
            user_error("Invalid layer '" + path + "'")
        self.dlg.selectionInLayerCombo.setLayer(loaded_layer)
        self.dlg.selectionExpr.setLayer(loaded_layer)
        self.dlg.selectionField.setLayer(loaded_layer)
        debug("selectionField layer : " + str(self.dlg.selectionField.layer().name()))
        debug(str(self.dlg.selectionField.layer().fields().names()))
        
    def setInLayerField(self,path):
        debug("[setInLayerField]")
        layer = QgsVectorLayer(path, "test", "ogr")
        self.dlg.selectionField.setLayer(layer)
                
    def getOrCreateGroup(self):
        group = self.dlg.selectionGroupCombo.currentText()
        if not group:
            user_error("No group selected")
        group_item = groups.getGroupByName(group)
        if not group_item:
            group_descr = self.dlg.selectionGroupDescr.text()
            in_layer = self.dlg.selectionInLayerCombo.currentLayer()
            in_geom = getLayerSimpleGeomStr(in_layer)
            group_item = groups.GroupItem(group,group_descr,in_geom)
            groups.groupsModel.addItem(group_item)
            groups.groupsModel.layoutChanged.emit()
        return group_item
        
        
    def getOrCreateClass(self):
        cls = self.dlg.selectionClassCombo.currentText()
        if not cls:
            user_error("No class selected")
        class_item = classes.getClassByName(cls)
        if not class_item:
            class_descr = self.dlg.selectionClassName.text()
            class_item = classes.ClassItem(cls,class_descr,None)
            classes.classModel.addItem(class_item)
            classes.classModel.layoutChanged.emit()
        return class_item
        
        
    def mkItemFromExpr(self):
        in_layer = self.dlg.selectionInLayerCombo.currentLayer()
        in_layer_path = params.normalizePath(pathOfLayer(in_layer))
        in_geom = getLayerSimpleGeomStr(in_layer)
        expr = self.dlg.selectionExpr.expression()
        grp_item = self.getOrCreateGroup()
        grp_item.checkGeom(in_geom)
        grp_name = grp_item.dict["name"]
        class_item = self.getOrCreateClass()
        cls_name = class_item.dict["name"]
        selection = SelectionItem(in_layer_path,expr,cls_name,grp_name)
        return selection
        
        
    def mkItemsFromField(self):
        in_layer = self.dlg.selectionInLayerCombo.currentLayer()
        in_layer_path = params.normalizePath(pathOfLayer(in_layer))
        in_geom = getLayerSimpleGeomStr(in_layer)
        field_name = self.dlg.selectionField.currentField()
        if not field_name:
            user_error("No field selected")
        grp_item = self.getOrCreateGroup()
        grp_item.checkGeom(in_geom)
        group = grp_item.dict["name"]
        if not group:
            user_error("No group selected")
        field_values = set()
        for f in in_layer.getFeatures():
            field_values.add(f[field_name])
        debug(str(field_values))
        items = []
        for fv in field_values:
            class_name = group + "_" + str(fv)
            class_descr = "Class " + str(fv) + " of group " + group
            class_item = classes.ClassItem(class_name,class_descr,None)
            classes.classModel.addItem(class_item)
            classes.classModel.layoutChanged.emit()
            expr = "\"" + field_name + "\" = '" + str(fv) + "'"
            item = SelectionItem(in_layer_path,expr,class_name,group)#,class_descr,group_descr)
            items.append(item)
        return items
        
    def addItems(self):
        debug("[addItemsFromField]")
        if self.dlg.fieldSelectionMode.checkState() == 0:
            items = [self.mkItemFromExpr()]
        elif self.dlg.fieldSelectionMode.checkState() == 2:
            items = self.mkItemsFromField()
        else:
            assert False
        for item in items:
            self.model.addItem(item)
            self.model.layoutChanged.emit()
            
    def switchFieldMode(self,checked):
        if checked:
            self.activateFieldMode()
        else:
            self.activateExprMode()
            
    def switchExprMode(self,checked):
        if checked:
            self.activateExprMode()
        else:
            self.activateFieldMode()
        
    def activateExprMode(self):
        self.dlg.fieldSelectionMode.setCheckState(0)
        self.dlg.exprSelectionMode.setCheckState(2)
        self.dlg.selectionField.hide()
        self.dlg.selectionFieldLabel.hide()
        self.dlg.selectionExpr.show()
        self.dlg.selectionExprLabel.show()
        self.dlg.selectionFieldClassLabel.hide()
        self.dlg.selectionClassAddLabel.show()
        self.dlg.selectionClassAdd.show()
        self.dlg.selectionClassNewLabel.show()
        self.dlg.selectionClassCombo.show()
        self.dlg.selectionClassName.show()
        self.dlg.selectionClassDescr.show()
        
    def activateFieldMode(self):
        self.dlg.exprSelectionMode.setCheckState(0)
        self.dlg.fieldSelectionMode.setCheckState(2)
        self.dlg.selectionExpr.hide()
        self.dlg.selectionExprLabel.hide()
        self.dlg.selectionField.show()
        self.dlg.selectionFieldLabel.show()
        self.dlg.selectionFieldClassLabel.show()
        self.dlg.selectionClassAddLabel.hide()
        self.dlg.selectionClassAdd.hide()
        self.dlg.selectionClassNewLabel.hide()
        self.dlg.selectionClassCombo.hide()
        self.dlg.selectionClassName.hide()
        self.dlg.selectionClassDescr.hide()
        
    def switchGroupDisplay(self,checked):
        if checked:
            self.activateGroupDisplay()
        else:
            self.activateClassDisplay()
            
    def switchClassDisplay(self,checked):
        if checked:
            self.activateClassDisplay()
        else:
            self.activateGroupDisplay()
            
    def activateGroupDisplay(self):
        self.dlg.classDisplay.setCheckState(0)
        self.dlg.groupDisplay.setCheckState(2)
        self.dlg.classFrame.hide()
        self.dlg.groupFrame.show()
        
    def activateClassDisplay(self):
        self.dlg.groupDisplay.setCheckState(0)
        self.dlg.classDisplay.setCheckState(2)
        self.dlg.groupFrame.hide()
        self.dlg.classFrame.show()
    