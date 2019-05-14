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

from qgis.core import (Qgis,
                       QgsMapLayerProxyModel,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsGeometry,
                       QgsField,
                       QgsFeature,
                       QgsFeatureRequest)
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView

from ..qgis_lib_mc import utils, qgsUtils, qgsTreatments, abstract_model, feedbacks
from ..algs import BioDispersal_algs
from . import params, classes, groups

from osgeo import gdal
import os

selection_fields = ["in_layer","mode","mode_val","group"]

resampling_modes = ["near","average"]
        
# Selection modes :
#   - VField (Vector by field)
#   - VExpr (Vector by expression)
#   - RClasses (Raster by classes)
#   - RResample (Raster by resampling)
vfield = "VField"
vexpr = "VExpr"
rclasses = "RClasses"
rresample = "RResample"

# SelectionItem implements DictItem and contains below fields :
#   - 'in_layer' : input layer from which features are selected
#   - 'expr' : expression on which selection is performerd
#                (all features are selected if empty expression)
#   - 'class' : class assigned to selection item
#   - 'group' : group assigned to selection item
class SelectionItem(abstract_model.DictItem):

    def __init__(self,in_layer,mode,mode_val,group):
        dict = {"in_layer" : in_layer,
                "mode" : mode,
                "mode_val" : mode_val,
                "group" : group}
        self.is_vector = (mode == vfield) or (mode == vexpr)
        utils.debug("is_vector = " + str(self.is_vector))
        self.is_raster = (mode == rclasses) or (mode == rresample)
        utils.debug("is_raster = " + str(self.is_raster))
        super().__init__(dict)
        
    def checkItem(self):
        pass
        
        
class SelectionModel(abstract_model.DictModel):
    
    def __init__(self,bdModel):
        self.parser_name = "SelectionModel"
        self.is_runnable = True
        self.bdModel = bdModel
        super().__init__(self,selection_fields)
        
    def mkItemFromDict(self,dict):
        utils.checkFields(selection_fields,dict.keys())
        mode = dict["mode"]
        mode_val = dict["mode_val"]
        item = SelectionItem(dict["in_layer"],mode,mode_val,dict["group"])
        return item
        
    # Returns absolute path of 'item' input layer
    def getItemInPath(self,item):
        return self.bdModel.getOrigPath(item.dict["in_layer"])
        
    # Returns absolute path of 'item' output layer
    def getItemOutPath(self,item):
        grp_name = item.dict["group"]
        if item.is_vector:
            return self.bdModel.groupsModel.getVectorPath(grp_name)
        else:
            return self.bdModel.groupsModel.getRasterPath(grp_name)
            
    # Override to remove classes meaningless after items deletion
    def removeItems(self,indexes):
        super().removeItems(indexes)
        for grp_item in self.bdModel.groupsModel.items:
            grp_name = grp_item.dict["name"]
            if not self.groupAlreadyUsed(grp_name):
                self.bdModel.classModel.removeFromGroupName(grp_name)
            
    # Remove SelectionItem matching group 'grp_name' from model
    def removeFromGroupName(self,grp_name):
        indexes = []
        for cpt, item in enumerate(self.items):
            if item.dict["group"] == grp_name:
                indexes.append(cpt)
        self.removeItemsFromRows(indexes)
        
    # Returns True if group 'grp_name' is already assigned to a selection item
    def groupAlreadyUsed(self,grp_name):
        for i in self.items:
            if i.dict["group"] == grp_name:
                return True
        return False

    # Raises an exception if group 'grp_name' is already assigned to a selection item
    def checkGroupNotUsed(self,grp_name):
        if self.groupAlreadyUsed(grp_name):
            utils.user_error("Group '" + grp_name + "' is already assigned to another selection item")
        
    # Performs selection by expression according to 'item'.
    def applySelectionVExpr(self,item,grp_item,out_path,context,feedback):
        grp_name = grp_item.dict["name"]
        class_item = self.bdModel.classModel.getClassByName(grp_name)
        parameters = { BioDispersal_algs.SelectVExprAlg.INPUT : self.getItemInPath(item),
                       BioDispersal_algs.SelectVExprAlg.EXPR : item.dict["mode_val"],
                       BioDispersal_algs.SelectVExprAlg.CLASS : grp_name,
                       BioDispersal_algs.SelectVExprAlg.CODE : class_item.dict["code"],
                       BioDispersal_algs.SelectVExprAlg.OUTPUT : out_path }
        qgsTreatments.applyProcessingAlg("BioDispersal","selectvexpr",parameters,
                                         context=context,feedback=feedback)
        
    # Performs selection by field according to 'item'.
    def applySelectionVField(self,item,grp_name,out_path,context,feedback):
        matrix = self.bdModel.classModel.getMatrixOfGroup(grp_name)
        parameters = { BioDispersal_algs.SelectVFieldAlg.INPUT : self.getItemInPath(item),
                       BioDispersal_algs.SelectVFieldAlg.FIELD : item.dict["mode_val"],
                       BioDispersal_algs.SelectVFieldAlg.GROUP : grp_name,
                       BioDispersal_algs.SelectVFieldAlg.ASSOC : matrix,
                       BioDispersal_algs.SelectVFieldAlg.OUTPUT : out_path }
        qgsTreatments.applyProcessingAlg("BioDispersal","selectvfield",parameters,
                                         context=context,feedback=feedback)
        
    # Performs selection according to 'item' parameters
    def applyItemWithContext(self,item,grp_item,context,feedback):
        mode = item.dict["mode"]
        grp_name = grp_item.dict["name"]
        out_path = self.getItemOutPath(item)
        input = self.getItemInPath(item)
        step_feedback = feedbacks.ProgressMultiStepFeedback(2,feedback)
        step_feedback.setCurrentStep(0)
        if mode == vexpr:
            self.applySelectionVExpr(item,grp_item,out_path,context,step_feedback)
        elif mode == vfield:
            self.applySelectionVField(item,grp_name,out_path,context,step_feedback)
        elif mode == rclasses:
            out_tmp_path = utils.mkTmpPath(out_path)
            matrix = self.bdModel.classModel.getReclassifyMatrixOfGroup(grp_name)
            # Call to native:reclassifybytable.
            # Output type set to Int16 to keep -9999 nodata value and ensure wide range of classes.
            # Boundaries mode = 2 to build reclassify intervals with one single value : [input_val,input_val].
            # Input values not covered by 'matrix' are reclassified to nodata.
            qgsTreatments.applyReclassifyByTable(input,matrix,out_tmp_path,
                                                 out_type = Qgis.Int16,
                                                 boundaries_mode=2,nodata_missing=True,
                                                 context=context,feedback=step_feedback)
            to_warp = out_tmp_path
        elif mode == rresample:
            to_warp = input
        else:
            utils.user_error("Unexpected mode : " + str(mode))
        step_feedback.setCurrentStep(1)
        if item.is_raster:
            # If selection is applied to raster layer, resampling is performed to match project parameters.
            resampling_mode = item.dict["mode_val"]
            crs, extent, resolution = self.bdModel.getRasterParams()
            # Output type set to Int16.
            qgsTreatments.applyWarpReproject(to_warp,out_path,resampling_mode,crs.authid(),
                                             extent=extent,extent_crs=crs,resolution=resolution,
                                             out_type=2,
                                             overwrite=True,context=context,feedback=step_feedback)
            qgsUtils.removeRaster(to_warp)
        step_feedback.setCurrentStep(2)
            
        
    # Selections are performed group by group.
    # Group vector layers are then rasterized (group_vector.shp to group_raster.tif)
    def applyItemsWithContext(self,indexes,context,feedback):
        self.bdModel.paramsModel.checkInit()
        selectionsByGroup = {}
        nb_items = len(indexes)
        step_feedback = feedbacks.ProgressMultiStepFeedback(nb_items,feedback)
        curr_step = 0
        feedback.setProgressText("Gathering selections by group")
        for n in indexes:
            i = self.items[n]
            grp = i.dict["group"]
            if grp in selectionsByGroup:
                selectionsByGroup[grp].append(i)
            else:
                selectionsByGroup[grp] = [i]
        # Iteration on groups
        for grp_name, selections in selectionsByGroup.items():
            step_feedback.setProgressText("Selection of group " + str(grp_name))
            grp_item = self.bdModel.groupsModel.getGroupByName(grp_name)
            if not grp_item:
                step_feedback.reportError("Group '" + grp_name + "' does not exist.")
                utils.user_error("Group '" + grp_name + "' does not exist.")
            grp_vector_path = self.bdModel.groupsModel.getVectorPath(grp_name)
            if os.path.isfile(grp_vector_path):
                qgsUtils.removeVectorLayer(grp_vector_path)
            from_raster = False
            for s in selections:
                self.applyItemWithContext(s,grp_item,context,step_feedback)
                if s.is_raster:
                    from_raster = True
                    if len(selections) > 1:
                        step_feedback.reportError("Group '" + grp_name + "' does not exist.")
                        utils.user_error("Several selections in group '" + grp_name +"'")
            out_path = self.bdModel.groupsModel.getRasterPath(grp_name)
            if not from_raster:
                crs, extent, resolution = self.bdModel.getRasterParams()
                if os.path.isfile(out_path):
                    qgsUtils.removeRaster(out_path)
                BioDispersal_algs.applyRasterizationFixAllTouch(grp_vector_path,out_path,extent,resolution,
                                                 field="Code",out_type=1,all_touch=True,
                                                 context=context,feedback=step_feedback)
            qgsUtils.loadRasterLayer(out_path,loadProject=True)
            curr_step += 1
            step_feedback.setCurrentStep(curr_step)
            
        
class SelectionConnector(abstract_model.AbstractConnector):

    def __init__(self,dlg,selectionModel):
        self.dlg = dlg
        self.onlySelection = False
        super().__init__(selectionModel,self.dlg.selectionView,
                        self.dlg.selectionAdd,self.dlg.selectionRemove)
                        
    def initGui(self):
        self.activateGroupDisplay()
        self.dlg.selectionInLayerCombo.setFilters(QgsMapLayerProxyModel.All)
        
    def connectComponents(self):
        super().connectComponents()
        # In layer
        self.dlg.selectionLayerFormatVector.stateChanged.connect(self.switchVectorMode)
        self.dlg.selectionLayerFormatRaster.stateChanged.connect(self.switchRasterMode)
        self.dlg.selectionInLayerCombo.layerChanged.connect(self.setInLayerFromCombo)
        self.dlg.selectionInLayer.fileChanged.connect(self.setInLayer)
        # Selection mode
        self.dlg.fieldSelectionMode.stateChanged.connect(self.switchFieldMode)
        self.dlg.exprSelectionMode.stateChanged.connect(self.switchExprMode)
        self.dlg.selectionCreateClasses.stateChanged.connect(self.switchRClassMode)
        # Class
        self.dlg.classDisplay.stateChanged.connect(self.switchClassDisplay)
        # Group
        self.dlg.selectionGroupCombo.setModel(self.model.bdModel.groupsModel)
        self.dlg.groupDisplay.stateChanged.connect(self.switchGroupDisplay)
        # Selections
        self.dlg.selectionUp.clicked.connect(self.upgradeItem)
        self.dlg.selectionDown.clicked.connect(self.downgradeItem)
        self.dlg.selectionRunSelectionMode.stateChanged.connect(self.switchOnlySelection)
        self.dlg.selectionRun.clicked.connect(self.applyItems)
        #
        header = self.dlg.selectionView.horizontalHeader()     
        self.activateVectorMode()
        self.activateFieldMode()
        #header.setSectionResizeMode(1, QHeaderView.Stretch)
        
    def applyItems(self):
        if self.onlySelection:
            indexes = list(set([i.row() for i in self.view.selectedIndexes()]))
        else:
            indexes = range(0,len(self.model.items))
        utils.debug(str(indexes))
        feedbacks.beginSection("Selection")
        self.model.applyItemsWithContext(indexes,self.dlg.context,self.dlg.feedback)
        feedbacks.endSection()
                        
    # Fetches or create
    def getOrCreateGroup(self):
        utils.debug("getOrCreateGroup")
        group = self.dlg.selectionGroupCombo.currentText()
        utils.debug("group = " + str(group))
        if not group:
            utils.user_error("No group selected")
        group_item = self.model.bdModel.groupsModel.getGroupByName(group)
        return group_item
        
    # def groupOfItem(self,item):
        # grp_name = item.dict["group"]
        # grp_item = self.model.bdModel.groupsModel.getGroupByName(grp_name)
        # return grp_item
        
    # def getClassesOfItem(self,item):
        # grp_name = item.dict["group"]
        # class_items = self.model.bdModel.classModel.getClassesOfGroup(grp_name)
        # return class_items
        
    # Instatiates classes from raw values
    def getClassesFromVals(self,group,vals):
        res = []
        for v in vals:
            class_name = group + "_" + str(v)
            class_descr = "Class " + str(v) + " of group " + group
            res.append((class_name,class_descr))
        return res
        
    # Instantiates SelectionItem from GUI state
    def mkItem(self):
        in_layer = self.dlg.selectionInLayerCombo.currentLayer()
        if not in_layer:
            utils.user_error("No layer selected")
        in_layer_path = self.model.bdModel.normalizePath(qgsUtils.pathOfLayer(in_layer))
        expr = self.dlg.selectionExpr.expression()
        grp_item = self.getOrCreateGroup()
        grp_name = grp_item.dict["name"]
        grp_descr = grp_item.dict["descr"]
        if self.dlg.selectionLayerFormatVector.isChecked():
            in_geom = qgsUtils.getLayerSimpleGeomStr(in_layer)
            grp_item.checkGeom(in_geom)
            if self.dlg.fieldSelectionMode.isChecked():
                self.model.checkGroupNotUsed(grp_name)
                mode = vfield
                mode_val = self.dlg.selectionField.currentField()
                utils.debug("mode_val = " + str(mode_val))
                if not mode_val:
                    utils.user_error("No field selected")
                vals = qgsUtils.getVectorVals(in_layer,mode_val)
                utils.debug("vals = " + str(vals))
                class_names = self.getClassesFromVals(grp_name,vals)
            elif self.dlg.exprSelectionMode.isChecked():
                mode = vexpr
                mode_val = self.dlg.selectionExpr.expression()
                class_names = [(grp_name, grp_descr)]
            else:
                assert False
        elif self.dlg.selectionLayerFormatRaster.isChecked():
            self.model.checkGroupNotUsed(grp_name)
            in_geom = "Raster"
            if self.dlg.selectionCreateClasses.isChecked():
                mode = rclasses
                feedbacks.beginSection("Fetching unique values")
                vals = qgsTreatments.getRasterUniqueVals(in_layer,feedback=self.dlg.feedback)
                # hist = qgsUtils.getHistogram(in_layer)
                # utils.debug("hist = " + str(hist))
                # hist_vect = hist.histogramVector
                # utils.debug("hist_vect = " + str(hist_vect))
                # hist_vect_list = list(hist.histogramVector)
                # utils.debug("hist_vect_list = " + str(hist_vect_list))
                # vals = hist_vect_list
                feedbacks.endSection()
                class_names = self.getClassesFromVals(grp_name,vals)
            else:
                mode = rresample
                class_names = [(grp_name, grp_descr)]
            resample_idx = self.dlg.selectionResampleCombo.currentIndex()
            mode_val = resampling_modes[resample_idx]
        else:
            assert False
        utils.debug("class_names = " + str(class_names))
        for (class_name, class_descr) in class_names:
            class_code = self.model.bdModel.classModel.getFreeCode()
            class_item = classes.ClassItem(class_name,class_descr,class_code,grp_name)
            self.model.bdModel.classModel.addItem(class_item)
            self.model.bdModel.classModel.layoutChanged.emit()
        item = SelectionItem(in_layer_path,mode,mode_val,grp_name)
        return item
        
    def setClass(self,text):
        cls_item = self.model.classModel.getClassByName(text)
        self.dlg.selectionClassName.setText(cls_item.dict["name"])
        self.dlg.selectionClassDescr.setText(cls_item.dict["descr"])
        
    def setGroup(self,text):
        grp_item = self.model.bdModel.groupsModel.getGroupByName(text)
        self.dlg.selectionGroupName.setText(grp_item.dict["name"])
        self.dlg.selectionGroupDescr.setText(grp_item.dict["descr"])
                        
    def setInLayerFromCombo(self,layer):
        utils.debug("setInLayerFromCombo")
        utils.debug(str(layer.__class__.__name__))
        if layer:
            path = qgsUtils.pathOfLayer(layer)
            self.dlg.selectionExpr.setLayer(layer)
            self.dlg.selectionField.setLayer(layer)
        else:
            utils.warn("Could not load selection in layer")
        
    def setInLayer(self,path):
        utils.debug("setInLayer " + path)
        if path:
            try:
                if self.dlg.selectionLayerFormatVector.isChecked():
                    loaded_layer = qgsUtils.loadVectorLayer(path,loadProject=True)
                    self.dlg.selectionExpr.setLayer(loaded_layer)
                    self.dlg.selectionField.setLayer(loaded_layer)
                    utils.debug("selectionField layer : " + str(self.dlg.selectionField.layer().name()))
                    utils.debug(str(self.dlg.selectionField.layer().fields().names()))
                else:
                    loaded_layer = qgsUtils.loadRasterLayer(path,loadProject=True)
                self.dlg.selectionInLayerCombo.setLayer(loaded_layer)
            except utils.CustomException as e:
                self.dlg.selectionInLayer.setFilePath("")
                raise e
                    
    # Vector / raster modes
    
    def switchVectorMode(self,checked):
        if checked:
            self.activateVectorMode()
        else:
            self.activateRasterMode()
            
    def switchRasterMode(self,checked):
        if checked:
            self.activateRasterMode()
        else:
            self.activateVectorMode()
        
    def activateVectorMode(self):
        utils.debug("activateVectorMode")
        self.dlg.selectionLayerFormatRaster.setCheckState(0)
        self.dlg.selectionLayerFormatVector.setCheckState(2)
        self.dlg.selectionInLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.selectionInLayer.setFilter(qgsUtils.getVectorFilters())
        self.dlg.stackSelectionMode.setCurrentWidget(self.dlg.stackSelectionModeVect)
        self.activateExprMode()
            
    def activateRasterMode(self):
        utils.debug("activateRasterMode")
        self.dlg.selectionLayerFormatVector.setCheckState(0)
        self.dlg.selectionLayerFormatRaster.setCheckState(2)
        self.dlg.selectionInLayerCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.selectionInLayer.setFilter(qgsUtils.getRasterFilters())
        self.dlg.stackSelectionMode.setCurrentWidget(self.dlg.stackSelectionModeRaster)
        self.dlg.stackSelectionExprField.setCurrentWidget(self.dlg.stackSelectionResampling)
        
            
    # Field / expression modes
            
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
        utils.debug("activateExprMode")
        self.dlg.fieldSelectionMode.setCheckState(0)
        self.dlg.exprSelectionMode.setCheckState(2)
        self.dlg.stackSelectionExprField.setCurrentWidget(self.dlg.stackSelectionExpr)
        
    def activateFieldMode(self):
        utils.debug("activateFieldMode")
        self.dlg.exprSelectionMode.setCheckState(0)
        self.dlg.fieldSelectionMode.setCheckState(2)
        self.dlg.stackSelectionExprField.setCurrentWidget(self.dlg.stackSelectionField)
        
    # Class / Resample modes
    
    def switchRClassMode(self,checked):
        if checked:
            self.activateRClassMode()
        else:
            self.activateRResampleMode()
        
    def activateRClassMode(self):
        utils.debug("activateRClassMode")
        self.dlg.selectionResampleCombo.setCurrentIndex(0)
        self.dlg.selectionResampleCombo.setDisabled(True)
        
    def activateRResampleMode(self):
        utils.debug("activateRResampleMode")
        self.dlg.selectionResampleCombo.setEnabled(True)
        
        
    # Groups / class display
        
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
        self.dlg.stackGroupClass.setCurrentWidget(self.dlg.stackGroup)
        
    def activateClassDisplay(self):
        self.dlg.groupDisplay.setCheckState(0)
        self.dlg.classDisplay.setCheckState(2)
        self.dlg.stackGroupClass.setCurrentWidget(self.dlg.stackClass)
    
