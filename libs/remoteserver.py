# -*- coding: utf-8 -*-
## @package remoteServer
#       The tcp/ip based server
#  @file
#       The tcp/ip based server

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from copy import copy

SIZEOF_UINT32 = 4

class QgsRemoteCommandServer(QTcpServer):

    def __init__(self, host="127.0.0.1", port=9615):
        super(QgsRemoteCommandServer, self).__init__()

        # connection related
        self.host = host
        self.port = port
        self.__startListening()

        self.sendMessageBackToSender = False

        # save incomming client sockets
        self.newConnection.connect(self.addConnection)
        self.connections = []

    def __startListening(self):
        self.listen(QHostAddress(self.host), self.port)

    def shutdownServer(self):
        for connection in self.connections:
            connection.disconnectFromHost()
        print "listening:", self.isListening()
        self.close()
        print "listening:", self.isListening()

    def addConnection(self):
        clientConnection = self.nextPendingConnection()
        clientConnection.nextBlockSize = 0
        self.connections.append(clientConnection)
        print "newly connected:", self.connections

        clientConnection.readyRead.connect(self.receiveMessage)
        clientConnection.disconnected.connect(self.removeConnection)
        clientConnection.error.connect(self.socketError)

    def receiveMessage(self):
        sender = self.sender()
        
        commandByteStream = sender.readAll()

        if self.sendMessageBackToSender:
            self.broadcast(self.connections, commandByteStream)
        else:
            sockets = copy(self.connections)
            sockets.remove(sender)
            self.broadcast(sockets, commandByteStream)

    def broadcast(self, sockets, commandByteStream):
        for socket in sockets:
            socket.write(commandByteStream)

    def removeConnection(self):
        self.connections.remove(self.sender())

    def socketError(self):
        self.sender().disconnectFromHost()