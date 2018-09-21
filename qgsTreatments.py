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
from qgis.core import QgsProcessingFeedback, QgsProject
import gdal

import os.path
import sys
import subprocess
import processing

import utils
import qgsUtils

nodata_val = '-9999'

def applyProcessingAlg(parameters,alg_name):
    feedback = QgsProcessingFeedback()
    if 'GRASS_REGION_CELLSIZE_PARAMETER' not in parameters:
        parameters['GRASS_REGION_CELLSIZE_PARAMETER'] = 25
    utils.debug("parameters : " + str(parameters))
    try:
        res = processing.run("grass7:" + alg_name,parameters,feedback=feedback)
        utils.debug(str(feedback))
        utils.debug(str(res["output"]))
        utils.debug ("call to " + alg_name + " successful")
        #res_layer = qgsUtils.loadRasterLayer(out_path)
        #QgsProject.instance().addMapLayer(res_layer)
    except Exception as e:
        utils.warn ("Failed to call " + alg_name + " : " + str(e))
        raise e
    finally:  
        utils.debug("End run " + alg_name)
        

def applySelection(in_layer,expr,out_layer):
    pass
    
# Apply rasterization on field 'field' of vector layer 'in_path'.
# Output raster layer in 'out_path'.
# Resolution set to 25 if not given.
# Extent can be given through 'extent_path'. If not, it is extracted from input layer.
# Output raster layer is loaded in QGIS if 'load_flag' is True.
def applyRasterization(in_path,field,out_path,resolution=None,extent_path=None,load_flag=False):
    utils.debug("applyRasterization")
    in_layer = qgsUtils.loadVectorLayer(in_path)
    if extent_path:
        extent_layer = qgsUtils.loadLayer(extent_path)
        extent = extent_layer.extent()
    else:
        in_layer = qgsUtils.loadVectorLayer(in_path)
        extent = in_layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()
    if not resolution:
        utils.warn("Setting rasterization resolution to 25")
        resolution = 25
    width = int((x_max - x_min) / float(resolution))
    height = int((y_max - y_min) / float(resolution))
    parameters = ['gdal_rasterize',
                  '-at',
                  '-te',str(x_min),str(y_min),str(x_max),str(y_max),
                  '-ts', str(width), str(height),
                  '-ot','Int32',
                  '-of','GTiff',
                  '-a_nodata',nodata_val]
    if field == "geom":
        parameters += ['-burn', '1']
    else:
        parameters += ['-a',field]
    parameters += [in_path,out_path]
    p = subprocess.Popen(parameters,stderr=subprocess.PIPE)
    out,err = p.communicate()
    utils.debug(str(p.args))
    if out:
        utils.info(str(out))
    if err:
        utils.user_error(str(err))
    elif load_flag:
        res_layer = qgsUtils.loadRasterLayer(out_path)
        QgsProject.instance().addMapLayer(res_layer)
        

# Apply raster calculator from expression 'expr'.
# Calculation is made on a single file and a signled band renamed 'A'.
# Output format is Integer32.
def applyResampleProcessing(in_path,out_path):
    utils.debug("qgsTreatments.applyResampleProcessing")
    parameters = {'input' : in_path,
                   'output' : out_path,
                   '--overwrite' : True,
                   'GRASS_REGION_CELLSIZE_PARAMETER' : 50,
                   'GRASS_SNAP_TOLERANCE_PARAMETER' : -1,
                   'GRASS_MIN_AREA_PARAMETER' : 0}
    feedback = QgsProcessingFeedback()
    try:
        processing.run("grass7:r.resample",parameters,feedback=feedback)
        utils.debug ("call to r.cost successful")
    except Exception as e:
        utils.warn ("Failed to call r.reclass : " + str(e))
        raise e
    finally:
        utils.debug("End resample")
        
# TODO
def applyWarpGdal(in_path,out_path,resampling_mode,
                  crs=None,resolution=None,extent_path=None,
                  load_flag=False,more_args=[]):
    utils.debug("qgsTreatments.applyWarpGdal")
    in_layer = qgsUtils.loadRasterLayer(in_path)
    if extent_path:
        extent_layer = qgsUtils.loadLayer(extent_path)
        extent = extent_layer.extent()
    else:
        in_layer = qgsUtils.loadLayer(in_path)
        extent = in_layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()
    if not resolution:
        utils.warn("Setting rasterization resolution to 25")
        resolution = 25
    width = int((x_max - x_min) / float(resolution))
    height = int((y_max - y_min) / float(resolution))
    in_crs = qgsUtils.getLayerCrsStr(in_layer)
    cmd_args = ['gdalwarp',
                '-s_srs',in_crs,
                '-t_srs',crs.authid(),
                '-te',str(x_min),str(y_min),str(x_max),str(y_max),
                '-ts', str(width), str(height),
                '-dstnodata',nodata_val,
                '-overwrite']
    if resampling_mode:
        cmd_args += ['-r',resampling_mode]
    cmd_args += more_args
    cmd_args += [in_path, out_path]
    utils.executeCmd(cmd_args)
    if load_flag:
        res_layer = qgsUtils.loadRasterLayer(out_path)
        QgsProject.instance().addMapLayer(res_layer)
        
# TO TEST
def applyReclassProcessing(in_path,out_path,rules_file,title):
    parameters = {'input' : in_path,
                  'output' : out_path,
                  'rules' : rules_file,
                  'title' : title,
                   'GRASS_REGION_CELLSIZE_PARAMETER' : 50,
                   'GRASS_SNAP_TOLERANCE_PARAMETER' : -1,
                   'GRASS_MIN_AREA_PARAMETER' : 0}
    feedback = QgsProcessingFeedback()
    try:
        processing.run("grass7:r.reclass",parameters,feedback=feedback)
        utils.debug ("call to r.cost successful")
    except Exception as e:
        utils.warn ("Failed to call r.reclass : " + str(e))
        raise e
    finally:
        utils.debug("End reclass")
        
# Apply raster calculator from expression 'expr'.
# Calculation is made on a single file and a signled band renamed 'A'.
# Output format is Integer32.
def applyGdalCalc(in_path,out_path,expr,load_flag=False,more_args=[]):
    utils.debug("qgsTreatments.applyGdalCalc(" + str(expr) + ")")
    if os.path.isfile(out_path):
        qgsUtils.removeRaster(out_path)
    cmd_args = ['gdal_calc.bat',
                '-A', in_path,
                '--type=Int32',
                '--outfile='+out_path,
                '--NoDataValue='+nodata_val,
                '--overwrite']
    cmd_args += more_args
    expr_opt = '--calc=' + expr
    cmd_args.append(expr_opt)
    utils.executeCmd(cmd_args)
    if load_flag:
        res_layer = qgsUtils.loadRasterLayer(out_path)
        QgsProject.instance().addMapLayer(res_layer)
        
# Filters input raster 'in_path' to keep values inferior to 'max_val' 
# in output raster 'out_path'.
def applyFilterGdalFromMaxVal(in_path,out_path,max_val,load_flag=False):
    utils.debug("qgsTreatments.applyReclassGdalFromMaxVal(" + str(max_val) + ")")
    expr = ('(A*less_equal(A,' + str(max_val) + ')*less_equal(0,A))'
        + '+(' + str(nodata_val) + '*less(' + str(max_val) + ',A))'
        + '+(' + str(nodata_val) + '*less(A,0))')
    applyGdalCalc(in_path,out_path,expr,load_flag,more_args=['--type=Float32'])
    # utils.executeCmdAsScript(cmd_args)
    # res_layer = qgsUtils.loadRasterLayer(out_path)
    # QgsProject.instance().addMapLayer(res_layer)
    
# Applies reclassification from 'in_path' to 'out_path' according to 'reclass_dict'.
# Dictionary contains associations of type {old_val -> new_val}.
# Pixels of value 'old_val' are set to 'new_val' value.
def applyReclassGdalFromDict(in_path,out_path,reclass_dict,load_flag=False):
    utils.debug("qgsTreatments.applyReclassGdalFromDict(" + str(reclass_dict) + ")")
    expr = ''
    for old_cls,new_cls in reclass_dict.items():
        if expr != '':
            expr += '+'
        expr += str(new_cls) + '*(A==' + str(old_cls)+ ')'
    applyGdalCalc(in_path,out_path,expr,load_flag)
    # cmd_args.append(expr)
    # utils.executeCmd(cmd_args)
    # res_layer = qgsUtils.loadRasterLayer(out_path)
    # QgsProject.instance().addMapLayer(res_layer)
    
def applyGdalCalcAB_ANull(in_path1,in_path2,out_path,expr,load_flag=False):
    utils.debug("qgsTreatments.applyGdalCalcAB")
    if os.path.isfile(out_path):
        qgsUtils.removeRaster(out_path)
    cmd_args = ['gdal_calc.bat',
                '-A', in_path1,
                '-B', in_path2,
                #'--type=Int32',
                '--NoDataValue='+nodata_val,
                '--overwrite',
                '--outfile='+out_path]
    expr_opt = '--calc=' + str(expr)
    cmd_args.append(expr_opt)
    utils.executeCmd(cmd_args)
    if load_flag:
        res_layer = qgsUtils.loadRasterLayer(out_path)
        QgsProject.instance().addMapLayer(res_layer)
    
# Creates raster 'out_path' from 'in_path1', 'in_path2' and 'expr'.
def applyGdalCalcAB(in_path1,in_path2,out_path,expr,load_flag=False):
    utils.debug("qgsTreatments.applyGdalCalcAB")
    if os.path.isfile(out_path):
        qgsUtils.removeRaster(out_path)
    tmp_no_data_val = -1
    nonull_p1 = utils.mkTmpPath(in_path1,suffix="_nonull")
    nonull_p2 = utils.mkTmpPath(in_path2,suffix="_nonull")
    nonull_out = utils.mkTmpPath(out_path,suffix="_nonull")
    nonull_out_tmp = utils.mkTmpPath(nonull_out,suffix="_tmp")
    applyRNull(in_path1,tmp_no_data_val,nonull_p1)
    applyRNull(in_path2,tmp_no_data_val,nonull_p2)
    cmd_args = ['gdal_calc.bat',
                '-A', nonull_p1,
                '-B', nonull_p2,
                #'--type=Int32',
                '--NoDataValue='+nodata_val,
                '--overwrite',
                '--outfile='+nonull_out]
    expr_opt = '--calc=' + str(expr)
    cmd_args.append(expr_opt)
    utils.executeCmd(cmd_args)
    reset_nodata_expr = '(A==' + str(tmp_no_data_val) + ')*' + str(nodata_val)
    reset_nodata_expr += '+(A!=' + str(tmp_no_data_val) + ')*A'
    applyGdalCalc(nonull_out,nonull_out_tmp,reset_nodata_expr)
    applyRSetNull(nonull_out_tmp,nodata_val,out_path)
    remove_tmp_flag = not utils.debug_flag
    if remove_tmp_flag:
        qgsUtils.removeRaster(nonull_p1)
        qgsUtils.removeRaster(nonull_p2)
        qgsUtils.removeRaster(nonull_out)
        qgsUtils.removeRaster(nonull_out_tmp)
    if load_flag:
        res_layer = qgsUtils.loadRasterLayer(out_path)
        QgsProject.instance().addMapLayer(res_layer)
    
# Applies ponderation on 'in_path1' according to 'in_path2' values.
# Result stored in 'out_path'.
def applyPonderationGdal(a_path,b_path,out_path,pos_values=False):
    utils.debug("qgsTreatments.applyPonderationGdal")
    if os.path.isfile(out_path):
        qgsUtils.removeRaster(out_path)
    cmd_args = ['gdal_calc.bat',
                '-A', a_path,
                '-B', b_path,
                #'--type=Int32',
                '--NoDataValue='+nodata_val,
                '--overwrite',
                '--outfile='+out_path]
    if pos_values:
        expr_opt = '--calc=A*B*less_equal(0,A)*less_equal(0,B)'
    else:
        expr_opt = '--calc=A*B'
    cmd_args.append(expr_opt)
    utils.executeCmd(cmd_args)
    res_layer = qgsUtils.loadRasterLayer(out_path)
    QgsProject.instance().addMapLayer(res_layer)
    
# Creates raster 'out_path' keeping maximum value from 'in_path1' and 'in_path2'.
def applyMaxGdal(in_path1,in_path2,out_path,load_flag=False):
    utils.debug("qgsTreatments.applyMaxGdal")
    expr = 'B*less_equal(A,B) + A*less(B,A)'
    applyGdalCalcAB(in_path1,in_path2,out_path,expr,load_flag)
    
# Creates raster 'out_path' keeping maximum value from 'in_path1' and 'in_path2'.
def applyMinGdal(in_path1,in_path2,out_path,load_flag=False):
    utils.debug("qgsTreatments.applyMinGdal")
    expr = 'A*less_equal(A,B) + B*less(B,A)'
    applyGdalCalcAB(in_path1,in_path2,out_path,expr,load_flag)
    
def applyRNull(in_path,new_val,out_path):
    utils.debug("applyRNull")
    parameters = { 'map' : in_path,
                   'null' : str(new_val),
                   'output' : out_path }
    applyProcessingAlg(parameters,"r.null")
    
def applyRSetNull(in_path,new_val,out_path):
    utils.debug("applyRNull")
    parameters = { 'map' : in_path,
                   'setnull' : str(new_val),
                   'output' : out_path }
    applyProcessingAlg(parameters,"r.null")
        
def applyRBuffer(in_path,buffer_vals,out_path):
    utils.debug ("applyRBuffer")
    utils.checkFileExists(in_path,"Buffer input layer ")
    distances_str = ""
    for v in buffer_vals:
        if distances_str != "":
            distances_str += ","
        distances_str += str(v)
    parameters = { 'input' : in_path,
                    'output' : out_path,
                    'distances' : distances_str, #"0,100,200",
                    'units' : 0, # 0 = meters ?
                    #'memory' : 5000,
                    'GRASS_RASTER_FORMAT_META' : '',
                    'GRASS_RASTER_FORMAT_OPT' : '',
                    'GRASS_REGION_CELLSIZE_PARAMETER' : 25,
                    'GRASS_REGION_PARAMETER' : None,
                    '-z' : False,
                    '--type' : 'Int32',
                    '--overwrite' : False}
    applyProcessingAlg(parameters,"r.buffer.lowmem")
    # feedback = QgsProcessingFeedback()
    # utils.debug("parameters : " + str(parameters))
    # try:
        # res = processing.run("grass7:r.buffer.lowmem",parameters,feedback=feedback)
        # print(str(feedback))
        # print(str(res["output"]))
        # print ("call to r.buffer successful")
    # except Exception as e:
        # print ("Failed to call r.buffer : " + str(e))
        # raise e
    # finally:  
        # utils.debug("End runBuffer")
        
def applyRCost(start_path,cost_path,cost,out_path):
    utils.debug ("applyRCost")
    utils.checkFileExists(start_path,"Dispersion Start Layer ")
    utils.checkFileExists(cost_path,"Dispersion Permeability Raster ")
    parameters = { 'input' : cost_path,
                    'start_raster' : start_path,
                    'max_cost' : int(cost),
                    'output' : out_path,
                    'null_cost' : None,
                    'memory' : 5000,
                    'GRASS_REGION_CELLSIZE_PARAMETER' : 25,
                    'GRASS_SNAP_TOLERANCE_PARAMETER' : -1,
                    'GRASS_MIN_AREA_PARAMETER' : 0,
                    '-k' : False,
                    '-n' : True,
                    '-r' : True,
                    '-i' : False,
                    '-b' : False}
    feedback = QgsProcessingFeedback()
    utils.debug("parameters : " + str(parameters))
    try:
        processing.run("grass7:r.cost",parameters,feedback=feedback)
        print ("call to r.cost successful")
        #res_layer = qgsUtils.loadRasterLayer(out_path)
        #QgsProject.instance().addMapLayer(res_layer)
    except Exception as e:
        print ("Failed to call r.cost : " + str(e))
        raise e
    finally:  
        utils.debug("End runCost")
        
        