# -*- coding: utf-8 -*-
## @package remoteCommands
#       available commands for interaction
#  @file
#       available commands for interaction

from qgis.core import QgsRectangle

class CommandZoomIn(object):
    pass

class CommandZoomOut(object):
    pass

class CommandSetViewPort(object):
    def __init__(self, extent, scale):
        if isinstance(extent, QgsRectangle):
            self.scale = scale
            self.__xMinimum = extent.xMinimum()
            self.__yMinimum = extent.yMinimum()
            self.__xMaximum = extent.xMaximum()
            self.__yMaximum = extent.yMaximum()
        else:
            raise AttributeError, "extent %s not of type QgsRectangle" % extent

    @property
    def extent(self):
        return QgsRectangle(self.__xMinimum, self.__yMinimum, self.__xMaximum, self.__yMaximum)