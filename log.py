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

from . import utils
from . import params

class LogConnector:
    
    def __init__(self,dlg):
        self.dlg = dlg
    
    def initGui(self):
        self.dlg.debugButton.setChecked(utils.debug_flag)
    
    def connectComponents(self):
        self.dlg.debugButton.clicked.connect(self.switchDebugMode)
        self.dlg.logSaveAs.clicked.connect(self.saveLogAs)
        self.dlg.logClear.clicked.connect(self.myClearLog)
        
    def switchDebugMode(self):
        if self.dlg.debugButton.isChecked():
            utils.debug_flag = True
            utils.info("Debug mode activated")
        else:
            utils.debug_flag = False
            utils.info("Debug mode deactivated")
            
    def saveLogAs(self):
        txt = self.dlg.txtLog.toPlainText()
        fname = params.saveFileDialog(self,msg="Enregistrer le journal sous",filter="*.txt")
        utils.writeFile(fname,txt)
        utils.info("Log saved to file '" + fname + "'")
        
    def myClearLog(self):
        self.dlg.txtLog.clear()
