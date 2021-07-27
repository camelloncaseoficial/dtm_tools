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

import processing
from qgis.PyQt.Qt import QVariant
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBand,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)


class AlosContourExtractorAlgorithm(QgsProcessingAlgorithm):
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
            QgsProcessingParameterNumber(
                self.CONTOUR_INTERVAL,
                self.tr('Interval between contour lines'),
                type=0
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.ELEVATION_ATTRIBUTE,
                self.tr('Interval between contour lines')
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.CONTOUR,
                self.tr('Contour lines')
            )
        )
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.DONUTHOLE,
        #         self.tr('Donut Hole')
        #     )
        # )
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.OUTPUT,
        #         self.tr('Output layer')
        #     )
        # )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsRasterLayer(
            parameters, self.RASTER_INPUT, context)
        band = self.parameterAsInt(
            parameters, self.BAND_NUMBER, context)
        interval = self.parameterAsDouble(
            parameters, self.CONTOUR_INTERVAL, context)
        elevation_attribute = self.parameterAsString(
            parameters, self.ELEVATION_ATTRIBUTE, context)

        contour_fields = QgsFields()
        contour_fields.append(QgsField(elevation_attribute, QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(parameters, contour_fields, QgsWkbTypes.LineGeometry, source.crs(), self.CONTOUR, context)
        # output = self.parameterAsOutputLayer(parameters, self.CONTOUR, context)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        parameters = {
            'BAND': band,
            'CREATE_3D': False,
            'EXTRA': '',
            'FIELD_NAME': elevation_attribute,
            'IGNORE_NODATA': False,
            'INPUT': source,
            'INTERVAL': interval,
            'NODATA': None,
            'OFFSET': 0,
            'OUTPUT': dest_id
        }
        outputDict = self.runClean(parameters, context, feedback)
        # total = 100.0 / outputDict.featureCount() if outputDict.featureCount() else 0
        features = outputDict.getFeatures()

        # for current, feature in enumerate(features):
        #     # Stop the algorithm if cancel button has been clicked
        #     if feedback.isCanceled():
        #         break

        #     # Add a feature in the sink
        #     sink.addFeature(feature, QgsFeatureSink.FastInsert)

        #     # Update the progress bar
        #     feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.CONTOUR: outputDict}

    def runClean(self, parameters, context, feedback=None):

        output = processing.run(
            'gdal:contour', parameters, context=context, feedback=feedback)
        return output['OUTPUT']

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
        return self.tr(self.name())

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
        return 'Contour Tools'

    def shortHelpString(self):
        """
        Retruns a short helper string for the algorithm
        """
        return self.tr('''
        extracts the contours
        ''')

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AlosContourExtractorAlgorithm()
