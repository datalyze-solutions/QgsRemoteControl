# -*- coding: utf-8 -*-
## @package remoteClient
#       The client for interaction with other clients over the tcp server connection
#  @file
#       The client for interaction with other clients over the tcp server connection

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from remotecommands import *

SIZEOF_UINT32 = 4

class QgsRemoteCommandClient(QTcpSocket):

    ## ToDo:
    #   - sync map tools
    #   - sync srs
    #   - set window placement
    #   - autostart new server if server stops unexpectedly

    def __init__(self, iface, host='localhost', port=9615, synced=False):
        super(QgsRemoteCommandClient, self).__init__()

        # QGIS related
        self.iface = iface
        self.mainWindow = self.iface.mainWindow()
        self.canvas = self.iface.mapCanvas()
        self.__synced = synced

        # connection related
        self.host = host
        self.port = port

        # Socket related
        self.__nextBlockSize = 0
        self.__request = None

        self.readyRead.connect(self.readFromServer)
        self.disconnected.connect(self.serverHasStopped)

    def setSynced(self, isChecked):
        self.__synced = isChecked
        if isChecked:
            self.canvas.extentsChanged.connect(self.canvasExtentsChanged)
        else:
            self.canvas.extentsChanged.disconnect(self.canvasExtentsChanged)

    def isSynced(self):
        return self.__synced

    def canvasExtentsChanged(self):
        self.sendCommand( CommandSetViewPort(self.canvas.extent(), self.canvas.scale()) )

    def connectToServer(self):
        self.connectToHost(self.host, self.port)

    def disconnectFromServer(self):
        self.disconnectFromHost()
        self.close()

    def serverHasStopped(self):
        self.close()
        print "Server has stopped"

    def serverHasError(self):
        print "Error: {}".format(self.errorString())
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

            if self.isSynced():
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