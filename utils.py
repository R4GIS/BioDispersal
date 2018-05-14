# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Utils
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

import datetime
import os.path

debug_flag=True

def printDate(msg):
    print ("[" + str(datetime.datetime.now()) + "] " + msg)
    
def debug(msg):
    if debug_flag:
        printDate("[debug] " + msg)
    
def info(msg):
    printDate("[info] " + msg)
    
def warn(msg):
    printDate("[warn] " + msg)
    
def user_error(msg):
    printDate("[user error] " + msg)
    raise Exception(msg)
    
def internal_error(msg):
    printDate("[internal error] " + msg)
    raise Exception(msg)

def checkFileExists(fname):
    if not (os.path.isfile(fname)):
        user_error("File '" + fname + "' does not exist")
        
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
#def writeShapefile(layer,outfname):
#    error = QgsVectorFileWriter.writeAsVectorFormat(layer,outfname)
#    if error == QgsVectorFileWriter.NoError:
#        info("Shapefile '" + outfname + "' succesfully created")
#    else:
#        user_error("Unable to create shapefile '" + outfname + "' : " + str(error))
