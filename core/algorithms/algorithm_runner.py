# -*- coding: utf-8 -*-

"""
/***************************************************************************
 AlosContourExtractor
                                 A QGIS plugin
 Creates contour and elevation points from Alos Palsar DEM
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-20
        copyright            : (C) 2021 by CamellOnCase
        email                : camelloncase@gmail.com
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

__author__ = 'Francisco Alves Camello Neto'
__date__ = '2021-07-20'
__copyright__ = '(C) 2021 by CamellOnCase'

import uuid
import processing
from qgis.analysis import QgsGeometrySnapper, QgsInternalGeometrySnapper
from qgis.core import (edit, Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsExpression, QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry, QgsMessageLog,
                       QgsProcessingContext, QgsProcessingMultiStepFeedback, QgsProcessingUtils, QgsProject,
                       QgsSpatialIndex, QgsVectorDataProvider, QgsVectorLayer, QgsVectorLayerUtils, QgsWkbTypes,
                       QgsProcessingFeatureSourceDefinition, QgsFeatureSink)
from qgis.PyQt.Qt import QObject, QVariant


class AlgorithmRunner():
    """
    Docstring
    """

    def __init__(self, iface=None, parent=None):
        super(AlgorithmRunner, self).__init__()
        self.parent = parent
        self.iface = iface
        if iface:
            self.canvas = iface.mapCanvas()

    def generate_gdal_output(self):
        uuid_value = str(uuid.uuid4()).replace('-','')
        output = QgsProcessingUtils.generateTempFilename('output_{uuid}.shp'.format(uuid=uuid_value))
        error = QgsProcessingUtils.generateTempFilename('error_{uuid}.shp'.format(uuid=uuid_value))
        return output, error
    
    def get_gdal_return(self, outputDict, context, returnError = False):
        lyr = QgsProcessingUtils.mapLayerFromString(outputDict['OUTPUT'], context)
        if returnError:
            errorLyr = QgsProcessingUtils.mapLayerFromString(outputDict['error'], context)
            return lyr, errorLyr
        else:
            return lyr

    def run_buffer(self, inputLayer, distance, context, dissolve=False, endCapStyle=None, joinStyle=None,
                   segments=None, mitterLimit=None, feedback=None, output_layer=None):
        endCapStyle = 0 if endCapStyle is None else endCapStyle
        joinStyle = 0 if joinStyle is None else joinStyle
        segments = 5 if segments is None else segments
        mitterLimit = 2 if mitterLimit is None else mitterLimit
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inputLayer,
            'DISTANCE': distance,
            'DISSOLVE': dissolve,
            'END_CAP_STYLE': endCapStyle,
            'JOIN_STYLE': endCapStyle,
            'SEGMENTS': segments,
            'MITER_LIMIT': mitterLimit,
            'OUTPUT': output_layer
        }
        output = processing.run("native:buffer",
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_polygons_to_lines(self, inpuy_layer, context, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inpuy_layer,
            'OUTPUT': output_layer
        }
        output = processing.run('native:polygonstolines',
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_bounding_box_retrieve(self, inpuy_layer, context, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inpuy_layer,
            'FIELD': '',
            'TYPE': 1,
            'OUTPUT': output_layer
        }
        output = processing.run("qgis:minimumboundinggeometry",
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_multi_to_single_part(self, inpuy_layer, context, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inpuy_layer,
            'OUTPUT': output_layer
        }
        output = processing.run('native:multiparttosingleparts',
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_polygonize(self, inpuy_layer, context, keep_fields=True, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inpuy_layer,
            'KEEP_FIELDS': keep_fields,
            'OUTPUT': output_layer
        }
        output = processing.run('native:polygonize',
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_contour(self, inputLyr, band, elevation_attribute, interval, context, feedback=None, output_layer=None):
        # output_layer = 'memory:' if output_layer is None else output_layer
        output = QgsProcessingUtils.generateTempFilename('OUTPUT.gpkg')
        parameters = {
            'BAND': band,
            'CREATE_3D': False,
            'EXTRA': '',
            'FIELD_NAME': elevation_attribute,
            'IGNORE_NODATA': False,
            'INPUT': inputLyr,
            'INTERVAL': interval,
            'NODATA': None,
            'OFFSET': 0,
            'OUTPUT': output}
        outputDict = processing.run('gdal:contour',
                                    parameters, context=context, feedback=feedback)
        return self.get_gdal_return(outputDict, context)

    def run_simplify(self, inputLyr, method, tolerance, context, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inputLyr,
            'METHOD': method,
            'TOLERANCE': tolerance,
            'OUTPUT': output_layer}
        output = processing.run('native:simplifygeometries',
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']

    def run_smooth(self, inputLyr, iterations, offset, max_angle, context, feedback=None, output_layer=None):
        output_layer = 'memory:' if output_layer is None else output_layer
        parameters = {
            'INPUT': inputLyr,
            'ITERATIONS': iterations,
            'OFFSET': offset,
            'MAX_ANGLE': max_angle,
            'OUTPUT': output_layer}
        output = processing.run('native:smoothgeometry',
                                parameters, context=context, feedback=feedback)
        return output['OUTPUT']