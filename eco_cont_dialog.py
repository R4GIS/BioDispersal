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
import sys
import traceback
from io import StringIO

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import processing
from processing.gui import AlgorithmDialog
from qgis.core import *
from qgis.gui import *
from qgis.gui import QgsFileWidget

file_dir = os.path.dirname(__file__)
if file_dir not in sys.path:
    sys.path.append(file_dir)

import utils
from .qgsUtils import *
import params
import sous_trames
import classes
import groups
from .selection import SelectionConnector
import fusion
import friction
from .ponderation import PonderationConnector
from .cost import CostConnector
from .config_parsing import *
from .log import LogConnector
import progress
import tabs

#FORM_CLASS, _ = uic.loadUiType(os.path.join(
#    os.path.dirname(__file__), 'eco_cont_dialog_base.ui'))

FORM_CLASS_TEST, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'test_dialog.ui'))
    
#from test_dialog import Ui_TestDialog
    
class EcologicalContinuityDialog(QtWidgets.QDialog,FORM_CLASS_TEST):
    def __init__(self, parent=None):
        """Constructor."""
        super(EcologicalContinuityDialog, self).__init__(parent)
        #super().__init__()
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #metagroupConnector = Metagroups(self)
        #self.groupConnector = Groups(self,metagroupConnector.metaclassModel)
        #rasterizationConnector = Rasterization(self)
        #self.tabs=[Groups(self),
        #            Metagroups(self),
        #            VectorSelections(self),
        #            Rasterization(self)]
        #self.tabs = [self.groupConnector,metagroupConnector,rasterizationConnector]
        self.setupUi(self)
        #self.connectComponents()
        
    # Initialize plugin tabs.
    # One tab <=> one connector.
    def initTabs(self):
        paramsConnector = params.ParamsConnector(self)
        params.params = paramsConnector.model
        stConnector = sous_trames.STConnector(self)
        sous_trames.stModel = stConnector.model
        groupsConnector = groups.GroupConnector(self)
        groups.groupsModel = groupsConnector.model
        classConnector = classes.ClassConnector(self)
        classes.classModel = classConnector.model
        selectionConnector = SelectionConnector(self)
        fusionConnector = fusion.FusionConnector(self)
        fusion.fusionModel = fusionConnector.model
        frictionConnector = friction.FrictionConnector(self)
        friction.frictionModel = frictionConnector.model
        ponderationConnector = PonderationConnector(self)
        costConnector = CostConnector(self)
        logConnector = LogConnector(self)
        progressConnector = progress.ProgressConnector(self)
        progress.progressConnector = progressConnector
        tabConnector = tabs.TabConnector(self)
        self.connectors = {"Params" : paramsConnector,
                           "ST" : stConnector,
                           "Group" : groupsConnector,
                           "Class" : classConnector,
                           "Selection" : selectionConnector,
                           "Fusion" : fusionConnector,
                           "Friction" : frictionConnector,
                           "Ponderation" : ponderationConnector,
                           "Cost" : costConnector,
                           "Log" : logConnector,
                           "Progress" : progressConnector,
                           "Tabs" : tabConnector}
        self.recomputeModels()
        
    # Initialize Graphic elements for each tab
    # TODO : resize
    def initGui(self):
        utils.debug("initGuiDlg")
        self.geometry = self.geometry()
        self.x = self.x()
        self.y = self.y()
        self.width = self.width()
        self.height = self.height()
        for k, tab in self.connectors.items():
            utils.debug("initGuiDlgItem " + str(k))
            tab.initGui()
        self.openProject.setToolTip("Ouvrir un projet BioDispersal")
        self.saveProject.setToolTip("Enregistrer le projet")
        self.saveProjectAs.setToolTip("Enregistrer le projet sous")
        #self.pluginTabs.removeTab(5)
        
    def bioDispHook(self,excType, excValue, tracebackobj):
        if excType == utils.CustomException:
            pass
        else:
            tbinfofile = StringIO()
            traceback.print_tb(tracebackobj, None, tbinfofile)
            tbinfofile.seek(0)
            tbinfo = tbinfofile.read()
            errmsg = str(excType) + "," + str(excValue)
            separator = '-' * 80
            sections = [separator, errmsg, separator]
            msg = '\n'.join(sections)
            final_msg = tbinfo + msg
            utils.print_func(final_msg)
        self.mTabWidget.setCurrentWidget(self.logTab)
        progress.progressConnector.clear()
        
    # Connect view and model components for each tab
    def connectComponents(self):
        for k, tab in self.connectors.items():
            tab.connectComponents()
        # Main tab connectors
        self.saveProjectAs.clicked.connect(self.saveModelAsAction)
        self.saveProject.clicked.connect(self.saveModel)
        self.openProject.clicked.connect(self.loadModelAction)
        sys.excepthook = self.bioDispHook
        
    def initializeGlobals(self):
        groups.groupsModel = None
        classes.classModel = None
        classes.class_fields = ["name","code","descr"]
        sous_trames.stModel = None
        fusion.fusionModel = None
        friction.frictionModel = None
        friction.frictionFields = ["class_descr","class","code"]
        
    def initLog(self):
        utils.print_func = self.txtLog.append
        
    def onResize(self,event):
        new_size = event.size()
        
    # Recompute self.models in case they have been reloaded
    def recomputeModels(self):
        self.models = {"ParamsModel" : params.params,
                        "STModel" : sous_trames.stModel,
                        "GroupModel" : groups.groupsModel,
                        "ClassModel" : classes.classModel,
                        "SelectionModel" : self.connectors["Selection"].model,
                        "FusionModel" : fusion.fusionModel,
                        "FrictionModel" : friction.frictionModel,
                        "PonderationModel" : self.connectors["Ponderation"].model,
                        "CostModel" : self.connectors["Cost"].model}
        
    # Return XML string describing project
    def toXML(self):
        xmlStr = "<ModelConfig>\n"
        for k, m in self.models.items():
            xmlStr += m.toXML() + "\n"
        xmlStr += "</ModelConfig>\n"
        utils.debug("Final xml : \n" + xmlStr)
        return xmlStr

    # Save project to 'fname'
    def saveModelAs(self,fname):
        self.recomputeModels()
        xmlStr = self.toXML()
        params.params.projectFile = fname
        utils.writeFile(fname,xmlStr)
        utils.info("BioDispersal model saved into file '" + fname + "'")
        
    def saveModelAsAction(self):
        fname = params.saveFileDialog(parent=self,msg="Sauvegarder le projet sous",filter="*.xml")
        if fname:
            self.saveModelAs(fname)
        
    # Save project to projectFile if existing
    def saveModel(self):
        fname = params.params.projectFile
        utils.checkFileExists(fname,"Project ")
        self.saveModelAs(fname)
   
    # Load project from 'fname' if existing
    def loadModel(self,fname):
        utils.debug("loadModel " + str(fname))
        utils.checkFileExists(fname)
        setConfigModels(self.models)
        params.params.projectFile = fname
        parseConfig(fname)
        utils.info("BioDispersal model loaded from file '" + fname + "'")
        
    def loadModelAction(self):
        fname = params.openFileDialog(parent=self,msg="Ouvrir le projet",filter="*.xml")
        if fname:
            self.loadModel(fname)
            
            
class BioDispersalDialog(QgsProcessingAlgorithmDialogBase):

    def __init__(self):
        super().__init__()
        self.eco_dlg = EcologicalContinuityDialog()
        #self.tabWidget().removeTab(0)
        nb_tabs = self.eco_dlg.pluginTabs.count()
        for n in range(0,nb_tabs):
            n_widget = self.eco_dlg.pluginTabs.widget(0)
            n_text = self.eco_dlg.pluginTabs.tabText(0)
            self.tabWidget().insertTab(n,n_widget,n_text)
        w1 = self.eco_dlg.mainTab
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWindowFlags(Qt.FramelessWindowHint)
        scroll_area.setAttribute(Qt.WA_TranslucentBackground)
        scroll_area.setWidget(w1)
        self.tabWidget().insertTab(1,scroll_area,"test_scroll")
        
        
    
#from test_dialog import Ui_TestDialog

class TestDialog(QtWidgets.QDialog,FORM_CLASS_TEST):
    def __init__(self, parent=None):
        """Constructor."""
        super(TestDialog, self).__init__(parent)
        self.setupUi(self)
        
class ProcessingDialog(QgsProcessingAlgorithmDialogBase):

    def __init__(self,parent=None):
        super(QgsProcessingAlgorithmDialogBase, self).__init__(parent)
        
        