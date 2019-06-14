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
import locale

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTranslator, qVersion, QCoreApplication
from qgis.gui import QgsFileWidget
from qgis.core import QgsApplication, QgsProcessingContext

file_dir = os.path.dirname(__file__)
if file_dir not in sys.path:
    sys.path.append(file_dir)
    
from .BioDispersalAbout_dialog import BioDispersalAboutDialog
from .qgis_lib_mc import (utils, qgsUtils, config_parsing, log, feedbacks)
from .algs.BioDispersal_algs import BioDispersalAlgorithmsProvider
from .steps import (params, subnetworks, classes, groups, selection, fusion, friction, ponderation, cost)
from . import tabs
from .BioDispersal_model import BioDispersalModel

FORM_CLASS, _ = uic.loadUiType(os.path.join(
 os.path.dirname(__file__), 'BioDispersal_dialog_base.ui'))

#FORM_CLASS_TEST, _ = uic.loadUiType(os.path.join(
#    os.path.dirname(__file__), 'test_dialog.ui'))
    
from BioDispersal_dialog_base import Ui_BioDispersalDialogBase
    
# class BioDispersalDialog(QtWidgets.QDialog,Ui_BioDispersalDialogBase):
class BioDispersalDialog(QtWidgets.QDialog,FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(BioDispersalDialog, self).__init__(parent)
        #super().__init__()
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.provider = BioDispersalAlgorithmsProvider()
        self.setupUi(self)
        
    # Initialize plugin tabs and connectors.
    def initTabs(self):
        global progressFeedback, paramsModel
        logConnector = log.LogConnector(self)
        logConnector.initGui()
        self.feedback =  feedbacks.ProgressFeedback(self)
        feedbacks.progressFeedback = self.feedback
        self.context = QgsProcessingContext()
        self.context.setFeedback(self.feedback)
        self.bdModel = BioDispersalModel(self.context,self.feedback)
        #################
        self.paramsConnector = params.ParamsConnector(self,self.bdModel.paramsModel)
        self.stConnector = subnetworks.STConnector(self,self.bdModel.stModel)
        self.groupsConnector = groups.GroupConnector(self,self.bdModel.groupsModel)
        self.classConnector = classes.ClassConnector(self,self.bdModel.classModel)
        self.selectionConnector = selection.SelectionConnector(self,self.bdModel.selectionModel)
        self.fusionConnector = fusion.FusionConnector(self,self.bdModel.fusionModel)
        self.frictionConnector = friction.FrictionConnector(self,self.bdModel.frictionModel)
        self.ponderationConnector = ponderation.PonderationConnector(self,self.bdModel.ponderationModel)
        self.costConnector = cost.CostConnector(self,self.bdModel.costModel)
        tabConnector = tabs.TabConnector(self)
        self.connectors = {"Params" : self.paramsConnector,
                           "ST" : self.stConnector,
                           "Group" : self.groupsConnector,
                           "Class" : self.classConnector,
                           "Selection" : self.selectionConnector,
                           "Fusion" : self.fusionConnector,
                           "Friction" : self.frictionConnector,
                           "Ponderation" : self.ponderationConnector,
                           "Cost" : self.costConnector,
                           "Log" : logConnector,
                           "Progress" : feedbacks.progressFeedback,
                           "Tabs" : tabConnector}
        self.recomputeParsers()
        
    # Initialize Graphic elements for each tab
    def initGui(self):
        utils.debug("initGuiDlg")
        QgsApplication.processingRegistry().addProvider(self.provider)
        self.geometry = self.geometry()
        self.x = self.x()
        self.y = self.y()
        self.width = self.width()
        self.height = self.height()
        for k, tab in self.connectors.items():
            utils.debug("initGuiDlgItem " + str(k))
            tab.initGui()
        
    # Exception hook, i.e. function called when exception raised.
    # Displays traceback and error message in log tab.
    # Ignores CustomException : exception raised from BioDispersal and already displayed.
    def bioDispHook(self,excType, excValue, tracebackobj):
        utils.debug("bioDispHook")
        if excType == utils.CustomException:
            utils.debug("Ignoring custom exception : " + str(excValue))
        else:
            tbinfofile = StringIO()
            traceback.print_tb(tracebackobj, None, tbinfofile)
            tbinfofile.seek(0)
            tbinfo = tbinfofile.read()
            errmsg = str(excType) + " : " + str(excValue)
            separator = '-' * 80
            sections = [separator, errmsg, separator]
            utils.debug(str(sections))
            msg = '\n'.join(sections)
            utils.debug(str(msg))
            final_msg = tbinfo + "\n" + msg
            utils.debug("traceback : " + str(tbinfo))
            utils.error_msg(errmsg,prefix="Unexpected error")
        self.mTabWidget.setCurrentWidget(self.logTab)
        feedbacks.progressFeedback.clear()
        
    # Connects view and model components for each tab.
    # Connects global elements such as project file and language management.
    def connectComponents(self):
        for k, tab in self.connectors.items():
            tab.connectComponents()
        # Main tab connectors
        self.saveProjectAs.clicked.connect(self.saveModelAsAction)
        self.saveProject.clicked.connect(self.saveModel)
        self.openProject.clicked.connect(self.loadModelAction)
        self.langEn.clicked.connect(self.switchLangEn)
        self.langFr.clicked.connect(self.switchLangFr)
        self.aboutButton.clicked.connect(self.openHelpDialog)
        sys.excepthook = self.bioDispHook
                
    def initLog(self):
        utils.print_func = self.txtLog.append
        
    def tr(self, message):
        return QCoreApplication.translate('BioDispersal', message)
   
    def switchLang(self,lang):
        utils.debug("switchLang " + str(lang))
        #loc_lang = locale.getdefaultlocale()
        #utils.info("locale = " + str(loc_lang))
        plugin_dir = os.path.dirname(__file__)
        lang_path = os.path.join(plugin_dir,'i18n','BioDispersal_' + lang + '.qm')
        if os.path.exists(lang_path):
            self.translator = QTranslator()
            self.translator.load(lang_path)
            if qVersion() > '4.3.3':
                utils.debug("Installing translator " + str(lang_path))
                QCoreApplication.installTranslator(self.translator)
            else:
                utils.internal_error("Unexpected qVersion : " + str(qVersion()))
        else:
            utils.warn("No translation file : " + str(lang_path))
        self.retranslateUi(self)
        self.paramsConnector.refreshProjectName()
        utils.curr_language = lang
        self.connectors["Tabs"].loadHelpFile()
        
    def switchLangEn(self):
        self.switchLang("en")
        self.langEn.setChecked(True)
        self.langFr.setChecked(False)
        
    def switchLangFr(self):
        self.switchLang("fr")
        self.langEn.setChecked(False)
        self.langFr.setChecked(True)
        
    def openHelpDialog(self):
        utils.debug("openHelpDialog")
        about_dlg = BioDispersalAboutDialog(self)
        about_dlg.show()
        
    # Recompute self.parsers in case they have been reloaded
    # TODO
    def recomputeParsers(self):
        self.parsers = [ self.bdModel.paramsModel,
                         self.bdModel.stModel,
                         self.bdModel.classModel,
                         self.bdModel.groupsModel,
                         self.bdModel.selectionModel,
                         self.bdModel.fusionModel,
                         self.bdModel.frictionModel,
                         self.bdModel.ponderationModel,
                         self.bdModel.costModel ]
        
    # Return XML string describing project
    def toXML(self):
        return self.bdModel.toXML()

    # Save project to 'fname'
    def saveModelAs(self,fname):
        self.recomputeParsers()
        xmlStr = self.toXML()
        #self.bdModel.paramsModel.projectFile = fname
        self.paramsConnector.setProjectFile(fname)
        utils.writeFile(fname,xmlStr)
        utils.info("BioDispersal model saved into file '" + fname + "'")
        
    def saveModelAsAction(self):
        fname = qgsUtils.saveFileDialog(parent=self,
                                        msg=self.tr("Save BioDispersal project as"),
                                        filter="*.xml")
        if fname:
            self.saveModelAs(fname)
        
    # Save project to projectFile if existing
    def saveModel(self):
        fname = self.bdModel.paramsModel.projectFile
        utils.checkFileExists(fname,"Project ")
        self.saveModelAs(fname)
   
    # Load project from 'fname' if existing
    def loadModel(self,fname):
        utils.debug("loadModel " + str(fname))
        utils.checkFileExists(fname)
        config_parsing.setConfigParsers(self.parsers)
        #self.bdModel.paramsModel.projectFile = fname
        self.paramsConnector.setProjectFile(fname)
        config_parsing.parseConfig(fname)
        utils.info("BioDispersal model loaded from file '" + fname + "'")
        
    def loadModelAction(self):
        fname = qgsUtils.openFileDialog(parent=self,
                                        msg=self.tr("Open BioDispersal project"),
                                        filter="*.xml")
        if fname:
            self.loadModel(fname)
