# -*- coding: utf-8 -*-
## @package remoteCommands
#       available commands for interaction
#  @file
#       available commands for interaction

from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt4 import QtCore
from PyQt4.QtCore import Qt


class CommandZoomIn(object):
    pass

    
class CommandZoomOut(object):
    pass

    
class CommandArrangeWindows(object):
    pass

positionFullscreen = "1"
positionLeft = "10"
positionRight = "01"
positionUpperLeft = "1000"
positionUpperRight = "0100"
positionLowerRight = "0010"
positionLowerLeft = "0001"

class CommandSetWindowPosition(object):

    def __init__(self, positionCode):     
        self.positionCode = positionCode

    def __repr__(self):
        return self.positionCode


class CommandSetMapTool(object):

    def __init__(self, qgsMapTool):
        self.mapTool = qgsMapTool

        
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


class CoordinateTransformation(object):

    def __init__(self, crsClient):
        self.crsClient = crsClient
        self.crsLatLon = QgsCoordinateReferenceSystem(3857)
        self.toLatLon = QgsCoordinateTransform(self.crsClient, self.crsLatLon)
        self.toClient = QgsCoordinateTransform(self.crsLatLon, self.crsClient)


class CommandGetConnectedClients(object):
    pass


class CommandConnectedClients(object):
    
    def __init__(self, clients):
        self.clients = clients


class ClientListModel(QtCore.QAbstractTableModel):

    def __init__(self, clients):
        super(ClientListModel, self).__init__()
        self.clients = clients

    def rowCount(self, parent=None):
        return len(self.clients)
        
    def columnCount(self, parent):
        try:
            return len(self.clients)
        except IndexError:
            return 0

    def data(self, index, role):
        if isinstance(index, QtCore.QModelIndex):
            row = index.row()

            if role == Qt.DisplayRole:
                return "%(address)s:%(port)s" % self.clients[row]