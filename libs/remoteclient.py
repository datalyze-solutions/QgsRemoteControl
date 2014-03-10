# -*- coding: utf-8 -*-
## @package remoteClient
#       The client for interaction with other clients over the tcp server connection
#  @file
#       The client for interaction with other clients over the tcp server connection

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

from remotecommands import *

SIZEOF_UINT32 = 4

class QgsRemoteCommandClient(QTcpSocket):

    # argument: clientList
    clientListUpdated = pyqtSignal(object)
    
    ## ToDo:
    #   - sync map tools
    #   - sync srs
    #   - autostart new server if server stops unexpectedly
    #   - slots or transfer objects to client?!
    #   - remove sync button and do the same with connect/disconnect
    #   - sync buttons send event
    #   - source SRS coords --> 4326 --> send --> 4326 --> goal SRS coords

    def __init__(self, iface, config, host='localhost', port=9615, synced=False):
        super(QgsRemoteCommandClient, self).__init__()

        # QGIS related
        self.iface = iface
        self.mainWindow = self.iface.mainWindow()
        self.canvas = self.iface.mapCanvas()
        self.config = config
        self.__synced = synced

        self.crsTransform = CoordinateTransformation(self.canvas.mapRenderer().destinationCrs())

        # connection related
        self.host = host
        self.port = port

        # Socket related
        self.__nextBlockSize = 0
        self.__request = None

        self.readyRead.connect(self.readFromServer)
        self.disconnected.connect(self.serverHasStopped)

    def __del__(self):
        try:
            self.canvas.extentsChanged.disconnect(self.canvasExtentsChanged)
            #self.canvas.mapToolSet.disconnect(self.syncMapTool)
        except:
            pass
        
    def __getScreenGeometry(self):
        return QApplication.instance().desktop().screenGeometry()

    def setSynced(self, isChecked):
        self.__synced = isChecked
        if isChecked:
            self.canvas.extentsChanged.connect(self.canvasExtentsChanged)
            #self.canvas.mapToolSet.connect(self.syncMapTool)
        else:
            self.canvas.extentsChanged.disconnect(self.canvasExtentsChanged)
            #self.canvas.mapToolSet.disconnect(self.syncMapTool)

    def isSynced(self):
        return self.__synced

    def canvasExtentsChanged(self):
        #print self.canvas.extent().toString()
        #extentLatLon = self.crsTransform.toLatLon.transform(self.canvas.extent())
        #print extentLatLon.toString()
        try:
            self.sendCommand( CommandSetViewPort(self.canvas.extent(), self.canvas.scale()) )
        #except NoneType:
            #pass
        except:
            raise

    #def syncMapTool(self, qgsMapTool):
        #self.sendCommand(CommandSetMapTool(qgsMapTool.__class__))
        
    def arrangeWindows(self):
        self.sendCommand(CommandArrangeWindows())
        
    def connectToServer(self):
        self.connectToHost(self.host, self.port)

    def disconnectFromServer(self):
        self.clientListUpdated.emit(ClientListModel([]))
        self.disconnectFromHost()
        self.close()

    def connectDisconnect(self, connecting):
        if connecting:
            self.connectToServer()
        else:
            self.disconnectFromServer()

    def serverHasStopped(self):
        self.clientListUpdated.emit(ClientListModel([]))    
        self.close()
        
    def sendCommand(self, command):
        self.__request = QByteArray()
        stream = QDataStream(self.__request, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_2)
        stream.writeUInt32(0)
        stream.writeQVariant(command)
        stream.device().seek(0)
        stream.writeUInt32(self.__request.size() - SIZEOF_UINT32)        
        self.write(self.__request)               
        self.__nextBlockSize = 0
        self.__request = None

    def readFromServer(self):
        stream = QDataStream(self)
        stream.setVersion(QDataStream.Qt_4_2)

        while True:
            if self.__nextBlockSize == 0:
                if self.bytesAvailable() < SIZEOF_UINT32:
                    break
                self.__nextBlockSize = stream.readUInt32()
            if self.bytesAvailable() < self.__nextBlockSize:
                break
            commandFromServer = stream.readQVariant()
            self.__nextBlockSize = 0

            if isinstance(commandFromServer, CommandConnectedClients):
               self.clientListUpdated.emit(ClientListModel(commandFromServer.clients))
            elif isinstance(commandFromServer, CommandSetWindowPosition):
                screenHeight = self.__getScreenGeometry().height()
                screenWidth = self.__getScreenGeometry().width()
                winTaskHeight = self.config.taskbarHeight + self.config.windowbarHeight
                if commandFromServer.positionCode == positionFullscreen:
                    self.mainWindow.move(0, 0)
                    self.mainWindow.resize(screenWidth, screenHeight)
                elif commandFromServer.positionCode == positionLeft:
                    self.mainWindow.move(0, 0)
                    self.mainWindow.resize(screenWidth/2, screenHeight)
                elif commandFromServer.positionCode == positionRight:
                    self.mainWindow.move(screenWidth/2, 0)
                    self.mainWindow.resize(screenWidth/2, screenHeight)
                elif commandFromServer.positionCode == positionUpperLeft:
                    self.mainWindow.move(0, 0)                    
                    self.mainWindow.resize(screenWidth/2, screenHeight/2 - winTaskHeight/2)
                elif commandFromServer.positionCode == positionUpperRight:
                    self.mainWindow.move(screenWidth/2, 0)
                    self.mainWindow.resize(screenWidth/2, screenHeight/2  - winTaskHeight/2)
                    
                elif commandFromServer.positionCode == positionLowerRight:
                    self.mainWindow.move(screenWidth/2, screenHeight/2 - self.config.windowbarHeight)
                    self.mainWindow.resize(screenWidth/2, screenHeight/2  - winTaskHeight/2)
                    
                elif commandFromServer.positionCode == positionLowerLeft:
                    self.mainWindow.move(0, screenHeight/2 - self.config.windowbarHeight)
                    self.mainWindow.resize(screenWidth/2, screenHeight/2  - winTaskHeight/2)
                        
            elif self.isSynced():
                if isinstance(commandFromServer, CommandZoomIn):
                    self.__disableCanvasActions()
                    self.canvas.zoomIn()
                    self.__enableCanvasActions()
                elif isinstance(commandFromServer, CommandZoomOut):
                    self.__disableCanvasActions()
                    self.canvas.zoomOut()
                    self.__enableCanvasActions()
                elif isinstance(commandFromServer, CommandSetViewPort):
                    self.__disableCanvasActions()
                    self.canvas.setExtent(commandFromServer.extent)
                    self.canvas.zoomScale(commandFromServer.scale)
                    self.__enableCanvasActions()
                elif isinstance(commandFromServer, CommandSetMapTool):
                    pass
                    #print commandFromServer.mapTool
                    #print commandFromServer.mapTool.__name__

                    #from qgis.gui import QgsMapToolPan
                    #self.canvas.mapToolSet.disconnect(self.syncMapTool)
                    #mapTool = QgsMapToolPan(self.canvas)
                    #self.canvas.setMapTool(mapTool)
                    #self.canvas.mapToolSet.connect(self.syncMapTool)
                    #print mapTool
                    

    def __disableCanvasActions(self):
        # deactivate rendering
        self.canvas.setRenderFlag(False)
        # disconnect signals for rerendering
        self.canvas.extentsChanged.disconnect(self.canvasExtentsChanged)

    def __enableCanvasActions(self):
        # reconnect signals
        self.canvas.extentsChanged.connect(self.canvasExtentsChanged)
        # activate rendering
        self.canvas.setRenderFlag(True)