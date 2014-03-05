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

        # without loop
        #if sender.bytesAvailable() > 0:
            #stream = QDataStream(sender)
            #stream.setVersion(QDataStream.Qt_4_2)
            #if sender.nextBlockSize == 0:
                #if sender.bytesAvailable() < SIZEOF_UINT32:
                    #return
                #sender.nextBlockSize = stream.readUInt32()
            #if sender.bytesAvailable() < sender.nextBlockSize:
                #return
            #command = stream.readQVariant()
            #sender.nextBlockSize = 0
            #if self.sendMessageBackToSender:                
                #self.broadcastCommands(self.connections, command)
            #else:
                #sockets = copy(self.connections)
                #sockets.remove(sender)
                #self.broadcastCommands(sockets, command)
            #sender.nextBlockSize = 0

        # original
        #for s in self.connections:
            #if s.bytesAvailable() > 0:
                #stream = QDataStream(s)
                #stream.setVersion(QDataStream.Qt_4_2)

                #if s.nextBlockSize == 0:
                    #if s.bytesAvailable() < SIZEOF_UINT32:
                        #return
                    #s.nextBlockSize = stream.readUInt32()
                #if s.bytesAvailable() < s.nextBlockSize:
                    #return

                #command = stream.readQVariant()
                #s.nextBlockSize = 0
                #self.sendMessage(command, s.socketDescriptor())
                #s.nextBlockSize = 0

    #def sendMessage(self, command, socketId):        
        #for s in self.connections:
            #if s.socketDescriptor() == socketId:
                #if self.sendMessageBackToSender:
                    #self.sendAnswer(s, command)
            #else:
                #self.sendAnswer(s, command)

    def broadcast(self, sockets, commandByteStream):
        for socket in sockets:
            socket.write(commandByteStream)
            #self.sendAnswer(socket, commandByteStream)

    # old version
    #def sendAnswer(self, socket, command):
        #reply = QByteArray()
        #stream = QDataStream(reply, QIODevice.WriteOnly)
        #stream.setVersion(QDataStream.Qt_4_2)
        #stream.writeUInt32(0)
        #stream.writeQVariant(command)
        #stream.device().seek(0)
        #stream.writeUInt32(reply.size() - SIZEOF_UINT32)        
        #socket.write(reply)

    def removeConnection(self):
        self.connections.remove(self.sender())

    def socketError(self):
        self.sender().disconnectFromHost()
        #self.connections.remove(self.sender())