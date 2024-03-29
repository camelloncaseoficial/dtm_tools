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

__author__ = 'CamellOnCase'
__date__ = '2021-07-20'
__copyright__ = '(C) 2021 by CamellOnCase'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import time

import processing
from qgis.PyQt.Qt import QVariant
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsVectorLayer,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingMultiStepFeedback)
from .core.handlers.raster_handler import RasterHandler
from .core.handlers.vector_handler import VectorHandler
from .core.handlers.attribute_handler import AttributeHandler
from .core.algorithms.algorithm_runner import AlgorithmRunner


class DtmContourExtractorAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    RASTER_INPUT = 'RASTER_INPUT'
    BAND_NUMBER = 'BAND_NUMBER'
    CONTOUR_INTERVAL = 'CONTOUR_INTERVAL'
    ELEVATION_ATTRIBUTE = 'ELEVATION_ATTRIBUTE'
    CONTOUR = 'CONTOUR'
    ERRORS = 'ERRORS'
    KEEP_ORIGINAL = 'KEEP_ORIGINAL'
    TOPOLOGY_CHECK = 'TOPOLOGY_CHECK'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER_INPUT,
                self.tr('Input DEM raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterBand(
                self.BAND_NUMBER,
                self.tr('Band number'),
                parentLayerParameterName=self.RASTER_INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.KEEP_ORIGINAL,
                self.tr('Keep original'),
                defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.TOPOLOGY_CHECK,
                self.tr('Topology check'),
                defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CONTOUR_INTERVAL,
                self.tr('Interval between contour lines'),
                type=0,
                defaultValue=10
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.ELEVATION_ATTRIBUTE,
                self.tr('Elevation attribute name'),
                defaultValue='ELEV'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.CONTOUR,
                self.tr('Contour lines')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ERRORS,
                self.tr('Contour lines errors')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        algo_runner = AlgorithmRunner()
        vector_handler = VectorHandler()
        attribute_handler = AttributeHandler()
        multi_step_feedback = QgsProcessingMultiStepFeedback(5, feedback)
        contour_lines = QgsVectorLayer()

        input_raster_layer = self.parameterAsRasterLayer(parameters, self.RASTER_INPUT, context)
        input_crs = input_raster_layer.crs()
        band = self.parameterAsInt(parameters, self.BAND_NUMBER, context)
        keep_original = self.parameterAsBool(parameters, self.KEEP_ORIGINAL, context)
        topology_check = self.parameterAsBool(parameters, self.TOPOLOGY_CHECK, context)
        interval = self.parameterAsDouble(parameters, self.CONTOUR_INTERVAL, context)
        elevation_attribute = self.parameterAsString(parameters, self.ELEVATION_ATTRIBUTE, context)

        contour_fields = attribute_handler.create_fields(elevation_attribute=elevation_attribute)
        errors_fields = attribute_handler.create_fields(error=True)

        (sink, destination_id) = self.parameterAsSink(parameters,
                                                      self.CONTOUR,
                                                      context,
                                                      contour_fields,
                                                      2,
                                                      input_crs)

        (line_errors_sink, line_errors_sink_id) = self.parameterAsSink(parameters,
                                                                       self.ERRORS,
                                                                       context,
                                                                       errors_fields,
                                                                       2,
                                                                       input_crs)

        (point_errors_sink, point_errors_sink_id) = self.parameterAsSink(parameters,
                                                                         self.ERRORS,
                                                                         context,
                                                                         errors_fields,
                                                                         1,
                                                                         input_crs)

        multi_step_feedback.setCurrentStep(0)
        multi_step_feedback.pushInfo(self.tr('Extracting contour lines...'))

        contour_lines = algo_runner.run_contour(input_raster_layer,
                                                band,
                                                elevation_attribute,
                                                interval,
                                                context, feedback)

        if keep_original:
            features = contour_lines.getFeatures()
            sink.addFeatures(features, QgsFeatureSink.FastInsert)

            return {self.CONTOUR: destination_id}

        multi_step_feedback.setCurrentStep(1)
        simplified_contour = vector_handler.retrieve_simplified_smoothed_contour(
            contour_lines, input_crs, feedback=multi_step_feedback)
        print("Simplified contours:", time.strftime("%H:%M:%S", time.localtime()))

        if topology_check:
            errors = list()
            multi_step_feedback.setCurrentStep(2)
            multi_step_feedback.pushInfo(self.tr('\n Retrieving intersected contour lines...'))

            #intersection_points = algo_runner.run_line_intersections(simplified_contour)
            intersection_points = vector_handler.filter_self_intersecting_lines(simplified_contour)[0]
            #for feature in intersection_points.getFeatures():
            for feature in intersection_points:
                feature.setFields(attribute_handler.create_fields(None, True))
                feature[0] = f'intersected contour line'
                errors.append(feature)

            print("Intersected contours:", time.strftime("%H:%M:%S", time.localtime()))

            multi_step_feedback.setCurrentStep(3)
            multi_step_feedback.pushInfo(self.tr('\n Retrieving collapsed contour lines...'))
            print(time.strftime("%H:%M:%S", time.localtime()))

            # verificar acho que tá rodando o processo toda vez para cada feição
            for feature in simplified_contour.getFeatures():
                collapsed_points = vector_handler.get_out_of_bounds_angle(feature.geometry(), 10)
                errors.extend(collapsed_points)
            print("Collapsed contours:", time.strftime("%H:%M:%S", time.localtime()))

            multi_step_feedback.setCurrentStep(2)
            multi_step_feedback.pushInfo(self.tr('\nFiltering contour lines...\n'))

            filtered_features = vector_handler.filter_geometry_by_length(interval, simplified_contour, input_crs)
            print("Filtered contours:", time.strftime("%H:%M:%S", time.localtime()))

            sink.addFeatures(filtered_features[0].getFeatures(), QgsFeatureSink.FastInsert)
            line_errors_sink.addFeatures(filtered_features[1], QgsFeatureSink.FastInsert)
            point_errors_sink.addFeatures(errors, QgsFeatureSink.FastInsert)

            return {self.CONTOUR: destination_id, self.ERRORS: line_errors_sink_id}

        else:
            multi_step_feedback.setCurrentStep(2)
            multi_step_feedback.pushInfo(self.tr('\nFiltering contour lines...\n'))

            filtered_features = vector_handler.filter_geometry_by_length(interval, simplified_contour, input_crs)
            print("Filtered contours:", time.strftime("%H:%M:%S", time.localtime()))
            sink.addFeatures(filtered_features.getFeatures(), QgsFeatureSink.FastInsert)

            return {self.CONTOUR: destination_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'contourextractor'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Contour Extractor')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Extractor Tools'

    def shortHelpString(self):
        """
        Retruns a short helper string for the algorithm
        """
        return self.tr("""extracts the contours""")

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DtmContourExtractorAlgorithm()
