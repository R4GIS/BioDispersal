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

from PyQt5.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from qgis.core import (Qgis,
                       QgsProject,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingProvider,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterString,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       QgsFeatureSink)

import processing
from processing.algs.gdal.rasterize import rasterize

from ..qgis_lib_mc import utils, qgsUtils, qgsTreatments, feedbacks
from ..BioDispersal_model import BioDispersalModel

MEMORY_LAYER_NAME = qgsTreatments.MEMORY_LAYER_NAME

class BioDispersalAlgorithmsProvider(QgsProcessingProvider):

    NAME = "BioDispersal"

    def __init__(self):
        self.alglist = [SelectVExprAlg(),
                        SelectVFieldAlg(),
                        WeightingBasics(),
                        WeightingByIntervals(),
                        WeightingByDistance(),
                        RasterSelectionByValue(),
                        BioDispersalAlgorithm(),
                        RasterizeFixAllTouch()]
        for a in self.alglist:
            a.initAlgorithm()
        super().__init__()
        
    def unload(self):
        pass
        
    def id(self):
        return self.NAME
        
    def name(self):
        return self.NAME
        
    def longName(self):
        return self.name()
        
    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "cerf.png")
        return QIcon(icon_path)

        
    def loadAlgorithms(self):
        for a in self.alglist:
            self.addAlgorithm(a)
            
               
class BioDispersalAlgorithm(QgsProcessingAlgorithm):

    # Algorithm parameters
    INPUT_CONFIG = "INPUT"
    LOG_FILE = "LOG"
    OUTPUT = "OUTPUT"
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return BioDispersalAlgorithm()
        
    def name(self):
        return "BioDispersalAlgorithm"
        
    def displayName(self):
        return self.tr("Run BioDispersal from configuration file")
        
    def shortHelpString(self):
        return self.tr("Executes complete process from XML configuration file")

    def initAlgorithm(self,config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_CONFIG,
                description=self.tr("Input configuration file")))
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.LOG_FILE,
                description=self.tr("Log file")))
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                description=self.tr("Output layer"),
                type=QgsProcessing.TypeVectorPolygon))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushInfo("begin")
        print("coucou")
        utils.print_func = feedback.pushInfo
        # Parameters
        log_file = self.parameterAsFile(parameters,self.LOG_FILE,context)
        print("lof_file = " + str(log_file))
        if utils.fileExists(log_file):
            os.remove(log_file)
        with open(log_file,"w+") as f:
            f.write("BioDispersal from configuration file " + str(log_file) + "\n")
            #raise QgsProcessingException("Log file " + str(log_file) + " already exists")
        print("args ok")
        log_feedback = feedbacks.FileFeedback(log_file)
        print("args ok")
        log_feedback.pushInfo("test")
        config_file = self.parameterAsFile(parameters,self.INPUT_CONFIG,context)
        print("args ok : " + str(config_file))
        config_tree = ET.parse(config_file)
        print("args ok")
        config_root = config_tree.getroot()
        print("args ok")
        bdModel = BioDispersalModel(context,log_feedback)
        print("fs ok")
        bdModel.runModel()
        outputs = [bdModel.getOrigPath(item.dict["out_layer"]) for item in bdModel.costModel.items]
        #qgsUtils.loadVectorLayer(res,loadProject=True)
        return {self.OUTPUT: outputs}
               
class SelectVExprAlg(QgsProcessingAlgorithm):

    ALG_NAME = 'selectvexpr'
    
    INPUT = 'INPUT'
    EXPR = 'EXPR'
    CLASS = 'CLASS'
    CODE = 'CODE'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return SelectVExprAlg()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr('Selection (VExpr)')
        
    def shortHelpString(self):
        return self.tr('Code layer creation from input layer')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                description=self.tr('Input layer')))
        self.addParameter(
            QgsProcessingParameterExpression (
                self.EXPR,
                description=self.tr('Expression'),
                defaultValue="",
                parentLayerParameterName=self.INPUT,
                optional=True))
        self.addParameter(
            QgsProcessingParameterString (
                self.CLASS,
                description=self.tr('Class')))
        self.addParameter(
            QgsProcessingParameterNumber (
                self.CODE,
                description=self.tr('Code'),
                type=QgsProcessingParameterNumber.Integer))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("input = " + str(input))
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        qgsUtils.normalizeEncoding(input)
        expr = self.parameterAsExpression(parameters,self.EXPR,context)
        class_name = self.parameterAsString(parameters,self.CLASS,context)
        code = self.parameterAsInt(parameters,self.CODE,context)
        out_fields = QgsFields()
        orig_field = QgsField("Origin", QVariant.String)
        class_field = QgsField("Class", QVariant.String)
        code_field = QgsField("Code", QVariant.Int)
        out_fields.append(orig_field)
        out_fields.append(class_field)
        out_fields.append(code_field)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            input.wkbType(),
            input.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        if expr is None or expr == "":
            nb_feats = input.featureCount()
            feats = input.getFeatures()
        else:
            qgsTreatments.selectByExpression(input,expr)
            nb_feats = input.selectedFeatureCount()
            feats = input.getSelectedFeatures()
            
        if nb_feats == 0:
            raise QgsProcessingException("No feature selected")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        for f in feats:
            new_f = QgsFeature(out_fields)
            new_f["Origin"] = input.sourceName()
            new_f["Class"] = class_name
            new_f["Code"] = code
            new_f.setGeometry(f.geometry())
            sink.addFeature(new_f,QgsFeatureSink.FastInsert)
            curr_step += 1
            feedback.setProgress(int(curr_step * progress_step))
            
        res = { self.OUTPUT : dest_id }
        return res

        
class SelectVFieldAlg(QgsProcessingAlgorithm):

    ALG_NAME = 'selectvfield'
    
    INPUT = 'INPUT'
    FIELD = 'FIELD'
    GROUP = 'GROUP'
    ASSOC = 'ASSOC'
    OUTPUT = 'OUTPUT'
    
    HEADER_FIELD_VAL = 'Field value'
    HEADER_INT_VAL = 'New integer value'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return SelectVFieldAlg()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr('Selection (VField)')
        
    def shortHelpString(self):
        return self.tr('Code layer creation from input layer')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                description=self.tr('Input layer')))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD,
                description=self.tr('Field'),
                defaultValue=None,
                parentLayerParameterName=self.INPUT))
        self.addParameter(
            QgsProcessingParameterString (
                self.GROUP,
                description=self.tr('Group')))
        self.addParameter(
            QgsProcessingParameterMatrix (
                self.ASSOC,
                description=self.tr('Value / code association'),
                numberRows=1,
                hasFixedNumberRows=False,
                headers=[self.HEADER_FIELD_VAL,self.HEADER_INT_VAL]))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("input = " + str(input))
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        qgsUtils.normalizeEncoding(input)
        fieldname = self.parameterAsString(parameters,self.FIELD,context)
        if not fieldname:
            raise QgsProcessingException("No field given")
        grp_name = self.parameterAsString(parameters,self.GROUP,context)
        assoc = self.parameterAsMatrix(parameters,self.ASSOC,context)
        out_fields = QgsFields()
        orig_field = QgsField("Origin", QVariant.String)
        class_field = QgsField("Class", QVariant.String)
        code_field = QgsField("Code", QVariant.Int)
        out_fields.append(orig_field)
        out_fields.append(class_field)
        out_fields.append(code_field)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            input.wkbType(),
            input.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        i = iter(assoc)
        assoc_table = dict(zip(i,i))
        feedback.pushDebugInfo("assoc_table : " + str(assoc_table))
        nb_feats = input.featureCount()
        if nb_feats == 0:
            raise QgsProcessingException("No feature in input layer")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        for f in input.getFeatures():
            field_val = str(f[fieldname])
            if field_val not in assoc_table:
                raise QgsProcessingException("Value '" + str(field_val) + "' does not exist in association")
            new_f = QgsFeature(out_fields)
            new_f["Origin"] = input.sourceName()
            new_f["Class"] = grp_name + "_" + str(field_val)
            try:
                code = int(assoc_table[field_val])
            except ValueError:
                raise QgsProcessingException("Matrix contains non-integer value " + str(assoc_table[field_val]))
            new_f["Code"] = code
            new_f.setGeometry(f.geometry())
            sink.addFeature(new_f)
            curr_step += 1
            feedback.setProgress(int(curr_step * progress_step))
        res = { self.OUTPUT : dest_id }
        return res        
      
class WeightingAlgorithm(QgsProcessingAlgorithm):
    
    INPUT_LAYER = 'INPUT_LAYER'
    WEIGHT_LAYER = 'WEIGHT_LAYER'
    RESAMPLING = 'RESAMPLING'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def name(self):
        return self.ALG_NAME

    def initAlgorithm(self, config=None):
        self.methods = ((self.tr('Nearest neighbour'), 'near'),
                        (self.tr('Bilinear'), 'bilinear'),
                        (self.tr('Cubic'), 'cubic'),
                        (self.tr('Cubic spline'), 'cubicspline'),
                        (self.tr('Lanczos windowed sinc'), 'lanczos'),
                        (self.tr('Average'), 'average'),
                        (self.tr('Mode'), 'mode'),
                        (self.tr('Maximum'), 'max'),
                        (self.tr('Minimum'), 'min'),
                        (self.tr('Median'), 'med'),
                        (self.tr('First quartile'), 'q1'),
                        (self.tr('Third quartile'), 'q3'))
                        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_LAYER,
                description=self.tr('Input layer')))
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.WEIGHT_LAYER,
                description=self.tr('Weighting layer')))
        self.addParameter(QgsProcessingParameterEnum(self.RESAMPLING,
                                                     self.tr('Resampling method to use'),
                                                     options=[i[0] for i in self.methods],
                                                     optional=True,
                                                     defaultValue=0))
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def prepareParameters(self,parameters,context,feedback):
        input = self.parameterAsRasterLayer(parameters,self.INPUT_LAYER,context)
        if input is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.INPUT_LAYER))
        weighting = self.parameterAsRasterLayer(parameters,self.WEIGHT_LAYER,context)
        if weighting is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.WEIGHT_LAYER))
        resampling = parameters[self.RESAMPLING]
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        return (input, weighting, resampling, output)
        
    def warpWeightingLayer(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        input_dp = input.dataProvider()
        nodata_val = input_dp.sourceNoDataValue(1)
        resolution = input.rasterUnitsPerPixelX()
        crs = input.crs()
        out = QgsProcessingUtils.generateTempFilename('warped.tif')
        warp_params = { 'INPUT' : weighting,
                        'TARGET_CRS' : crs,
                        'RESAMPLING' : resampling,
                        'NODATA' : nodata_val,
                        'TARGET_RESOLUTION' : resolution,
                        'TARGET_EXTENT' : input.extent(),
                        'TARGET_EXTENT_CRS' : crs,
                        'OUTPUT' : out }
        warped = processing.run('gdal:warpreproject',warp_params,context=context,feedback=feedback)
        return warped['OUTPUT']
        
    def warpFromCustomLayer(self,input,resampling,output,context,feedback):
        input_dp = input.dataProvider()
        nodata_val = input_dp.sourceNoDataValue(1)
        resolution = input.rasterUnitsPerPixelX()
        crs = input.crs()
        warp_params = { 'INPUT' : input,
                        'TARGET_CRS' : crs,
                        'RESAMPLING' : resampling,
                        'NODATA' : nodata_val,
                        'TARGET_RESOLUTION' : resolution,
                        'TARGET_EXTENT' : input.extent(),
                        'TARGET_EXTENT_CRS' : crs,
                        'OUTPUT' : output }
        warped = processing.run('gdal:warpreproject',warp_params,context=context,feedback=feedback)
        return warped['OUTPUT']


class WeightingBasics(WeightingAlgorithm):

    ALG_NAME = 'weightingbasics'

    OPERATOR = 'OPERATOR'
        
    def createInstance(self):
        return WeightingBasics()
        
    def displayName(self):
        return self.tr('Weighting (Basics)')
        
    def shortHelpString(self):
        helpStr = "Weighting of friction layer A by another layer B. Layers must be aligned.\n"
        helpStr += "Available weighting operations :\n"
        helpStr += " * Minimum (pixResult = min(pixA, pixB))\n"
        helpStr += " * Maximum (pixResult = max(pixA, pixB))\n"
        helpStr += " * Multiplication (pixResult = pixA * pixB)"
        return self.tr(helpStr)

    def initAlgorithm(self, config=None):
        self.operators = [ self.tr('Minimum'),
                           self.tr('Maximum'),
                           self.tr('Multiplication') ]
        super().initAlgorithm()
        self.addParameter(QgsProcessingParameterEnum(self.OPERATOR,
                                                     self.tr('Weighting method to use'),
                                                     options=self.operators,
                                                     defaultValue=0))
                                                             
    def processAlgorithm(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        operator = self.parameterAsEnum(parameters,self.OPERATOR,context)
        #output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        warped_path = self.warpWeightingLayer(parameters,context,feedback)
        feedback.pushDebugInfo('warped_path = ' + str(warped_path))
        warped_layer = qgsUtils.loadRasterLayer(warped_path)
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        min, max = qgsUtils.getRastersMinMax([input,weighting])
        range = [min,max]
        layers = [qgsUtils.pathOfLayer(input),qgsUtils.pathOfLayer(weighting)]
        out_path = parameters['OUTPUT']
        feedback.pushDebugInfo('out_path = ' + str(out_path))
        feedback.pushDebugInfo('output = ' + str(output))
        # if os.path.isfile(out_path):
            # qgsUtils.removeRaster(out_path)
        if operator == 0:
            # out = qgsTreatments.applyRSeries(layers,4,range,output,
                                             # context=context,feedback=feedback)
            out = qgsTreatments.applyRasterCalcMin(input,warped_layer,output,
                                                   nodata_val=nodata_val,out_type=4,
                                                   context=context,feedback=feedback)
        elif operator == 1:
            # out = qgsTreatments.applyRSeries(layers,6,range,output,
                                             # context=context,feedback=feedback)
            out = qgsTreatments.applyRasterCalcMax(input,warped_layer,output,
                                                   nodata_val=nodata_val,out_type=4,
                                                   context=context,feedback=feedback)
        elif operator == 2:
            out = qgsTreatments.applyRasterCalcMult(input,warped_layer,output,
                                                    nodata_val=nodata_val,out_type=4,
                                                    context=context,feedback=feedback)
        else:
            assert(False)
        return { 'OUTPUT' : out }

            
class WeightingIntervalsAlgorithm(WeightingAlgorithm):
    
    INTERVALS = 'INTERVALS'
    RANGE_BOUNDARIES = 'RANGE_BOUNDARIES'
    
    LOW_BOUND = 'LOW_BOUND'
    UP_BOUND = 'UP_BOUND'
    POND_VAL = 'POND_VALUE'
    NODATA_POND_VAL = 'NODATA_POND_VALUE'

    def initAlgorithm(self, config=None):
        self.range_boundaries = [self.tr('min < value <= max'),
                                 self.tr('min <= value < max'),
                                 self.tr('min <= value <= max'),
                                 self.tr('min < value < max')]
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterMatrix (
                self.INTERVALS,
                description=self.tr('Intervals'),
                numberRows=1,
                hasFixedNumberRows=False,
                headers=[self.LOW_BOUND,self.UP_BOUND,self.POND_VAL]))
        self.addParameter(QgsProcessingParameterEnum(self.RANGE_BOUNDARIES,
                                                     self.tr('Range boundaries'),
                                                     options=self.range_boundaries,
                                                     optional=True,
                                                     defaultValue=2))
                
   
class WeightingByIntervals(WeightingIntervalsAlgorithm):

    ALG_NAME = 'weightingbyintervals'
        
    def createInstance(self):
        return WeightingByIntervals()
        
    def displayName(self):
        return self.tr('Weighting (By intervals)')
        
    def shortHelpString(self):
        helpStr = "Weighting of friction layer A by another layer B. Layers must be aligned.\n"
        helpStr += "Value intervals [lowBound, upBound] and weighting value 'pond_val' are defined for layer B.\n"
        helpStr += "If pixB belongs to [lowBound, upBound] then pixResult = pixA * pond_val."
        return self.tr(helpStr)

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
                
    def processAlgorithm(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        range_boundaries = self.parameterAsEnum(parameters,self.RANGE_BOUNDARIES,context)
        # WARP
        warped_layer = self.warpWeightingLayer(parameters,context,feedback)
        # RECLASSIFY
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        out_reclassed = QgsProcessingUtils.generateTempFilename('Reclassed.tif')
        reclass_params = { 'DATA_TYPE' : 5,
                           'INPUT_RASTER' : warped_layer,
                           'NODATA_FOR_MISSING' : True,
                           'NO_DATA' : nodata_val,
                           'OUTPUT' : out_reclassed,
                           'RANGE_BOUNDARIES' : range_boundaries,
                           'RASTER_BAND' : 1,
                           'TABLE' : parameters[self.INTERVALS] }
        reclassed = processing.run('native:reclassifybytable',reclass_params,context=context,feedback=feedback)
        reclassed_layer = reclassed['OUTPUT']
        # WEIGHTING
        weighted = qgsTreatments.applyRasterCalcMult(input,reclassed_layer,output,
                                                     nodata_val=nodata_val,out_type=5,
                                                     context=context,feedback=feedback)
        return { 'OUTPUT' : weighted }
   
class WeightingByDistance(WeightingIntervalsAlgorithm):

    ALG_NAME = 'weightingbydistance'
        
    def createInstance(self):
        return WeightingByDistance()
        
    def displayName(self):
        return self.tr('Weighting (By distance)')
        
    def shortHelpString(self):
        helpStr = "Weighting of friction layer A by distance to another layer B. Layers must be aligned.\n"
        helpStr += "Distance intervals [lowBound, upBound] and weighting value 'pond_val' are defined for layer B.\n"
        helpStr += "Distance of pixA to layer B is computed as the minimum distance from pixA to a pixel of B that is not NoData"
        helpStr += "If distance(pixA,B) belongs to [lowBound, upBound] then pixResult = pixA * pond_val."
        return self.tr(helpStr)

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
                
    def processAlgorithm(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        range_boundaries = self.parameterAsEnum(parameters,self.RANGE_BOUNDARIES,context)
        intervals = self.parameterAsMatrix(parameters,self.INTERVALS,context)
        # WARP
        warped_layer = self.warpWeightingLayer(parameters,context,feedback)
        # BUFFER
        feedback.pushDebugInfo('intervals = ' +str(intervals))
        distances = intervals[1::3]
        feedback.pushDebugInfo('distances = ' +str(distances))
        distances_str = ",".join([str(d) for d in distances])
        feedback.pushDebugInfo('distances_str = ' +str(distances_str))
        out_buffer = QgsProcessingUtils.generateTempFilename('out_buffer.tif')
        buffer_params = { 'input' : warped_layer,
                          'output' : out_buffer,
                          'distances' : distances_str,
                          'units' : 0, # 0 = meters ?
                          'GRASS_RASTER_FORMAT_META' : '',
                          'GRASS_RASTER_FORMAT_OPT' : '',
                          'GRASS_REGION_CELLSIZE_PARAMETER' : 0,
                          'GRASS_REGION_PARAMETER' : None,
                          '-z' : False }
                          #'--type' : 'Int32'
                          #'--overwrite' : False}
        feedback.pushDebugInfo("buffer_params = " + str(buffer_params))
        buffered = processing.run('grass7:r.buffer',buffer_params,context=context,feedback=feedback)
        feedback.pushDebugInfo("buffered = " + str(buffered))
        buffered_layer = buffered['output']
        feedback.pushDebugInfo("buffered_layer = " + str(buffered_layer))
        # RECLASSIFY
        pond_vals = intervals[2::3]
        feedback.pushDebugInfo('pond_vals = ' + str(pond_vals))
        pv1 = pond_vals[0]
        pond_table = [1,1,pv1]
        for idx, pv in enumerate(pond_vals,2):
            pond_table.append(idx)
            pond_table.append(idx)
            pond_table.append(pv)
        feedback.pushDebugInfo('pond_table = ' + str(pond_table))
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        out_reclassed = QgsProcessingUtils.generateTempFilename('Reclassed.tif')
        reclass_params = { 'DATA_TYPE' : 5,
                           'INPUT_RASTER' : buffered_layer,
                           'NODATA_FOR_MISSING' : True,
                           'NO_DATA' : nodata_val,
                           'OUTPUT' : out_reclassed,
                           'RANGE_BOUNDARIES' : range_boundaries,
                           'RASTER_BAND' : 1,
                           'TABLE' : pond_table }
        feedback.pushDebugInfo("reclass_params = " + str(reclass_params))
        reclassed = processing.run('native:reclassifybytable',reclass_params,context=context,feedback=feedback)
        reclassed_layer = reclassed['OUTPUT']
        # NODATA
        reclassed_nonull = QgsProcessingUtils.generateTempFilename('reclassed_nonull.tif')
        nonull = qgsTreatments.applyRNull(reclassed_layer,1,reclassed_nonull,context=context,feedback=feedback)
        # WEIGHTING
        weighted = qgsTreatments.applyRasterCalcMult(input,nonull,output,
                                                     nodata_val=nodata_val,out_type=5,
                                                     context=context,feedback=feedback)
        return { 'OUTPUT' : weighted }
   
class RasterSelectionByValue(QgsProcessingAlgorithm):

    ALG_NAME = 'rasterselectionbyvalue'

    INPUT = 'INPUT'
    OPERATOR = 'OPERATOR'
    VALUE = 'VALUE'
    OUTPUT = 'OUTPUT'
    
    OPERATORS = ['<','<=','>','>=','==']
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return RasterSelectionByValue()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr('Raster selection by value')
        
    def shortHelpString(self):
        return self.tr('Creates new raster with input raster values veryfing specified operation.')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                description=self.tr('Input layer')))
        self.addParameter(
            QgsProcessingParameterEnum(self.OPERATOR,
                                       self.tr('Operator'),
                                       options=self.OPERATORS,
                                       defaultValue=4))
        self.addParameter(
            QgsProcessingParameterNumber (
                self.VALUE,
                description=self.tr('Value'),
                defaultValue=0.0,
                type=QgsProcessingParameterNumber.Double))
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def getDataType(self,in_type):
        typeAssoc = { Qgis.Byte : 0,
                      Qgis.Int16 : 1,
                      Qgis.UInt16 : 2,
                      Qgis.UInt32 : 3,
                      Qgis.Int32 : 4,
                      Qgis.Float32 : 5,
                      Qgis.Float64 : 6 }
        if in_type in typeAssoc:
            #return typeAssoc[in_type]
            return 5
        else:
            return 5
                
    def processAlgorithm(self,parameters,context,feedback):
        input = self.parameterAsRasterLayer(parameters,self.INPUT,context)
        if input is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.INPUT))
        operator = self.parameterAsEnum(parameters,self.OPERATOR,context)
        value = self.parameterAsDouble(parameters,self.VALUE,context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        # Type
        input_type = input.dataProvider().sourceDataType(1)
        out_type = self.getDataType(input_type)
        # Expression
        input_nodata_val = input.dataProvider().sourceNoDataValue(1)
        #input_name = input.name()
        #band1_str = input_name + "@1"
        #input_str = 'A'
        operator_str = self.OPERATORS[operator]
        value_str = str(value)
        nodata_str = str(input_nodata_val)
        cmp_expr = '(A {} {})'.format(operator_str,value_str)
        expr = 'A * {} + {} * (1 - {})'.format(cmp_expr,nodata_str,cmp_expr)
        #expr = 'A == 2'
        feedback.pushDebugInfo("gdalcalc expr = " + str(expr))
        # Call
        out = qgsTreatments.applyRasterCalc(input,output,expr,
                                            nodata_val=input_nodata_val,out_type=out_type,
                                            context=context,feedback=feedback)
        return { 'OUTPUT' : out }
        
    
    
class RasterizeFixAllTouch(rasterize):

    ALG_NAME = 'rasterizefixalltouch'

    def createInstance(self):
        return RasterizeFixAllTouch()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr('Rasterize (with ALL_TOUCH fix)')
        
    def shortHelpString(self):
        return self.tr('Wrapper for gdal:rasterize algorithm allowing to use ALL_TOUCH option (every pixel touching input geometry are rasterized).')

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ALL_TOUCH,
                description = 'ALL_TOUCH option',
                defaultValue=False,
                optional=True))
    
# Apply rasterization on field 'field' of vector layer 'in_path'.
# Output raster layer in 'out_path'.
# Resolution set to 25 if not given.
# Extent can be given through 'extent_path'. If not, it is extracted from input layer.
# Output raster layer is loaded in QGIS if 'load_flag' is True.
def applyRasterizationFixAllTouch(in_path,out_path,extent,resolution,
                       field=None,burn_val=None,out_type=Qgis.Float32,
                       nodata_val=qgsTreatments.nodata_val,all_touch=False,overwrite=False,
                       context=None,feedback=None):
    TYPES = ['Byte', 'Int16', 'UInt16', 'UInt32', 'Int32', 'Float32',
             'Float64', 'CInt16', 'CInt32', 'CFloat32', 'CFloat64']
    if overwrite:
        qgsUtils.removeRaster(out_path)
    parameters = { 'ALL_TOUCH' : True,
                   'BURN' : burn_val,
                   'DATA_TYPE' : out_type,
                   'EXTENT' : extent,
                   'FIELD' : field,
                   'HEIGHT' : resolution,
                   'INPUT' : in_path,
                   'NODATA' : nodata_val,
                   'OUTPUT' : out_path,
                   'UNITS' : 1, 
                   'WIDTH' : resolution }
    res = qgsTreatments.applyProcessingAlg("BioDispersal","rasterizefixalltouch",parameters,context,feedback)
    return res