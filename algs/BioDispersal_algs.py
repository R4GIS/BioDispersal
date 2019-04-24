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

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (Qgis,
                       QgsProject,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessing,
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
                       QgsFeatureSink)

import processing

from ..qgis_lib_mc import qgsUtils, qgsTreatments

MEMORY_LAYER_NAME = 'TEMPORARY_OUTPUT'

class BioDispersalAlgorithmsProvider(QgsProcessingProvider):

    NAME = "BioDispersal"

    def __init__(self):
        self.alglist = [TestAlg(),
                        SelectVExprAlg(),
                        SelectVFieldAlg(),
                        WeightingBasics(),
                        WeightingByIntervals(),
                        WeightingByDistance()]
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
        
    def loadAlgorithms(self):
        for a in self.alglist:
            self.addAlgorithm(a)
            
            
class TestAlg(QgsProcessingAlgorithm):

    ALG_NAME = "testalg"

    LAYERS = "LAYERS"
    EXTENT = "EXTENT"
    NUMBER = "NUMBER"
    MATRIX = "MATRIX"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return TestAlg()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("1 - Prepare landscape")
        
    def shortHelpString(self):
        return self.tr("This algorithms prepares land cover data by applying selection (from expression) and dissolving geometries")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.LAYERS,
                self.tr("Raster layers")))
        self.addParameter(
            QgsProcessingParameterExtent (
                self.EXTENT,
                description=self.tr("Extent"),
                optional=True))
        self.addParameter(
            QgsProcessingParameterNumber (
                self.NUMBER,
                description=self.tr("Number"),
                optional=True))
        self.addParameter(
            QgsProcessingParameterMatrix (
                self.MATRIX,
                "Matrix",
                numberRows=1,
                hasFixedNumberRows=False,
                headers=['c1','c2','c3']))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        return None
        
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
        warp_params = { 'INPUT' : weighting,
                        'TARGET_CRS' : crs,
                        'RESAMPLING' : resampling,
                        'NODATA' : nodata_val,
                        'TARGET_RESOLUTION' : resolution,
                        'TARGET_EXTENT' : input.extent(),
                        'TARGET_EXTENT_CRS' : crs,
                        'OUTPUT' : MEMORY_LAYER_NAME }
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
        return self.tr('TODO')

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
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        warped_layer = self.warpWeightingLayer(parameters,context,feedback)
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        if operator == 0:
            out = qgsTreatments.applyRasterCalcMin(input,warped_layer,output,
                                                   nodata_val=nodata_val,
                                                   context=context,feedback=feedback)
        elif operator == 1:
            out = qgsTreatments.applyRasterCalcMax(input,warped_layer,output,
                                                   nodata_val=nodata_val,
                                                   context=context,feedback=feedback)
        elif operator == 1:
            out = qgsTreatments.applyRasterCalcMult(input,warped_layer,output,
                                                    nodata_val=nodata_val,
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
                                                     defaultValue=0))
                
   
class WeightingByIntervals(WeightingIntervalsAlgorithm):

    ALG_NAME = 'weightingbyintervals'
        
    def createInstance(self):
        return WeightingByIntervals()
        
    def displayName(self):
        return self.tr('Weighting (By intervals)')
        
    def shortHelpString(self):
        return self.tr('TODO')

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
                
    def processAlgorithm(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        range_boundaries = self.parameterAsEnum(parameters,self.RANGE_BOUNDARIES,context)
        # WARP
        warped_layer = self.warpWeightingLayer(parameters,context,feedback)
        # RECLASSIFY
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        reclass_params = { 'DATA_TYPE' : 5,
                           'INPUT_RASTER' : warped_layer,
                           'NODATA_FOR_MISSING' : True,
                           'NO_DATA' : nodata_val,
                           'OUTPUT' : 'TEMPORARY_OUTPUT',
                           'RANGE_BOUNDARIES' : range_boundaries,
                           'RASTER_BAND' : 1,
                           'TABLE' : parameters[self.INTERVALS] }
        reclassed = processing.run('native:reclassifybytable',reclass_params,context=context,feedback=feedback)
        reclassed_layer = reclassed['OUTPUT']
        # WEIGHTING
        expr = "A*B"
        rastercalc_params = { 'BAND_A' : 1,
                              'BAND_B' : 1,
                              'FORMULA' : expr,
                              'INPUT_A' : input,
                              'INPUT_B' : reclassed_layer,
                              'NO_DATA' : nodata_val,
                              'OUTPUT' : output,
                              'RTYPE' : 5 }
        calc = processing.run('gdal:rastercalculator',rastercalc_params,context=context,feedback=feedback)
        return calc
   
class WeightingByDistance(WeightingIntervalsAlgorithm):

    ALG_NAME = 'weightingbydistance'
        
    def createInstance(self):
        return WeightingByDistance()
        
    def displayName(self):
        return self.tr('Weighting (By distance)')
        
    def shortHelpString(self):
        return self.tr('TODO')

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
                
    def processAlgorithm(self,parameters,context,feedback):
        input, weighting, resampling, output = self.prepareParameters(parameters,context,feedback)
        range_boundaries = self.parameterAsEnum(parameters,self.RANGE_BOUNDARIES,context)
        intervals = self.parameterAsMatrix(parameters,self.INTERVALS,context)
        # WARP
        #warped_layer = self.warpWeightingLayer(parameters,context,feedback)
        # BUFFER
        feedback.pushDebugInfo('intervals = ' +str(intervals))
        distances = intervals[1::3]
        feedback.pushDebugInfo('distances = ' +str(distances))
        distances_str = ",".join([str(d) for d in distances])
        feedback.pushDebugInfo('distances_str = ' +str(distances_str))
        buffer_params = { 'input' : weighting,
                          'output' : 'TEMPORARY_OUTPUT',
                          'distances' : distances_str,
                          'units' : 0, # 0 = meters ?
                          'GRASS_RASTER_FORMAT_META' : '',
                          'GRASS_RASTER_FORMAT_OPT' : '',
                          'GRASS_REGION_CELLSIZE_PARAMETER' : 0,
                          'GRASS_REGION_PARAMETER' : None,
                          '-z' : False }
                          #'--type' : 'Int32'
                          #'--overwrite' : False}
        buffered = processing.run('grass7:r.buffer',buffer_params,context=context,feedback=feedback)
        buffered_layer = buffered['output']
        # RECLASSIFY
        nodata_val = input.dataProvider().sourceNoDataValue(1)
        reclass_params = { 'DATA_TYPE' : 5,
                           'INPUT_RASTER' : buffered_layer,
                           'NODATA_FOR_MISSING' : True,
                           'NO_DATA' : nodata_val,
                           'OUTPUT' : 'TEMPORARY_OUTPUT',
                           'RANGE_BOUNDARIES' : range_boundaries,
                           'RASTER_BAND' : 1,
                           'TABLE' : parameters[self.INTERVALS] }
        reclassed = processing.run('native:reclassifybytable',reclass_params,context=context,feedback=feedback)
        reclassed_layer = reclassed['OUTPUT']
        # WEIGHTING
        expr = "A*B"
        rastercalc_params = { 'BAND_A' : 1,
                              'BAND_B' : 1,
                              'FORMULA' : expr,
                              'INPUT_A' : input,
                              'INPUT_B' : reclassed_layer,
                              'NO_DATA' : nodata_val,
                              'OUTPUT' : output,
                              'RTYPE' : 5 }
        calc = processing.run('gdal:rastercalculator',rastercalc_params,context=context,feedback=feedback)
        return calc
   
class WeightingByValueBis(QgsProcessingAlgorithm):

    ALG_NAME = 'weightingbyvaluebis'
    
    INPUT_LAYER = 'INPUT_LAYER'
    WEIGHT_LAYER = 'WEIGHT_LAYER'
    RESAMPLING = 'RESAMPLING'
    INTERVALS = 'INTERVALS'
    RANGE_BOUNDARIES = 'RANGE_BOUNDARIES'
    OUTPUT = 'OUTPUT'
    
    LOW_BOUND = 'LOW_BOUND'
    UP_BOUND = 'UP_BOUND'
    POND_VAL = 'POND_VALUE'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return WeightingByValueBis()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr('Weighting (By value bis)')
        
    def shortHelpString(self):
        return self.tr('TODO')

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
        self.range_boundaries = [self.tr('min < value <= max'),
                                 self.tr('min <= value < max'),
                                 self.tr('min <= value <= max'),
                                 self.tr('min < value < max')]
                        
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
                                                     defaultValue=0))
        self.addParameter(
            QgsProcessingParameterMatrix (
                self.INTERVALS,
                description=self.tr('Value intervals'),
                numberRows=1,
                hasFixedNumberRows=False,
                headers=[self.LOW_BOUND,self.UP_BOUND,self.POND_VAL]))
        self.addParameter(QgsProcessingParameterEnum(self.RANGE_BOUNDARIES,
                                                     self.tr('Range boundaries'),
                                                     options=self.range_boundaries,
                                                     defaultValue=0))
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        input = self.parameterAsRasterLayer(parameters,self.INPUT_LAYER,context)
        if input is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.INPUT_LAYER))
        weighting = self.parameterAsRasterLayer(parameters,self.WEIGHT_LAYER,context)
        if weighting is None:
            raise QgsProcessingException(self.invalidRasterError(parameters, self.WEIGHT_LAYER))
        #resampling = self.methods[self.parameterAsEnum(parameters, self.RESAMPLING, context)][1]
        #intervals = self.parameterAsMatrix(parameters,self.INTERVALS,context)
        range_boundaries = self.parameterAsEnum(parameters,self.RANGE_BOUNDARIES,context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        #nodata_val = -9999
        # WARP
        input_dp = input.dataProvider()
        nodata_val = input_dp.sourceNoDataValue(1)
        resolution = input.rasterUnitsPerPixelX()
        crs = input.crs()
        warp_params = { 'INPUT' : weighting,
                        'TARGET_CRS' : crs,
                        'RESAMPLING' : parameters[self.RESAMPLING],
                        'NODATA' : nodata_val,
                        'TARGET_RESOLUTION' : resolution,
                        'TARGET_EXTENT' : input.extent(),
                        'TARGET_EXTENT_CRS' : crs,
                        'OUTPUT' : 'TEMPORARY_OUTPUT' }
        warped = processing.run('gdal:warpreproject',warp_params,context=context,feedback=feedback)
        warped_layer = warped['OUTPUT']
        # RECLASSIFY
        reclass_params = { 'DATA_TYPE' : 5,
                           'INPUT_RASTER' : warped_layer,
                           'NODATA_FOR_MISSING' : True,
                           'NO_DATA' : nodata_val,
                           'OUTPUT' : 'TEMPORARY_OUTPUT',
                           'RANGE_BOUNDARIES' : range_boundaries,
                           'RASTER_BAND' : 1,
                           'TABLE' : parameters[self.INTERVALS] }
        reclassed = processing.run('native:reclassifybytable',reclass_params,context=context,feedback=feedback)
        reclassed_layer = reclassed['OUTPUT']
        # WEIGHTING
        expr = "A*B"
        rastercalc_params = { 'BAND_A' : 1,
                              'BAND_B' : 1,
                              'FORMULA' : expr,
                              'INPUT_A' : input,
                              'INPUT_B' : reclassed_layer,
                              'NO_DATA' : nodata_val,
                              'OUTPUT' : output,
                              'RTYPE' : 5 }
        calc = processing.run('gdal:rastercalculator',rastercalc_params,context=context,feedback=feedback)
        return calc
