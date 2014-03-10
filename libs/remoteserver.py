# -*- coding: utf-8 -*-
## @package remoteServer
#       The tcp/ip based server
#  @file
#       The tcp/ip based server

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from copy import copy
from remotecommands import *

SIZEOF_UINT32 = 4

class QgsRemoteCommandServer(QTcpServer):

    # first: isListening
    # second: called in which function, e.x. startListening or shutdown
    signalServerStatus = pyqtSignal(object, object)

    def __init__(self, host="127.0.0.1", port=9615):
        super(QgsRemoteCommandServer, self).__init__()

        # connection related
        self.host = host
        self.port = port

        self.sendMessageBackToSender = False

        # save incomming client sockets
        self.newConnection.connect(self.addConnection)
        self.connections = []        

    def startListening(self):
        self.listen(QHostAddress(self.host), self.port)
        self.signalServerStatus.emit(self.isListening(), "startListening")

    def shutdown(self):
        for connection in self.connections:
            connection.disconnectFromHost()
        self.close()        
        self.signalServerStatus.emit(self.isListening(), "shutdown")

    def startStop(self, starting):
        if starting:
            self.startListening()
        else:
            self.shutdown()

    def addConnection(self):
        clientConnection = self.nextPendingConnection()
        clientConnection.nextBlockSize = 0
        self.connections.append(clientConnection)
        print "newly connected:", self.connections

        clientConnection.readyRead.connect(self.receiveMessage)
        clientConnection.disconnected.connect(self.removeConnection)
        clientConnection.error.connect(self.socketError)

        self.returnClientList(self.connections)

    def receiveMessage(self):
        sender = self.sender()

        if sender.bytesAvailable() > 0:
            stream = QDataStream(sender)
            stream.setVersion(QDataStream.Qt_4_2)
            if sender.nextBlockSize == 0:
                if sender.bytesAvailable() < SIZEOF_UINT32:
                    return
                sender.nextBlockSize = stream.readUInt32()
            if sender.bytesAvailable() < sender.nextBlockSize:
                return
            command = stream.readQVariant()
            sender.nextBlockSize = 0
            if isinstance(command, CommandGetConnectedClients):
                self.returnClientList([sender])
            elif isinstance(command, CommandArrangeWindows):
                self.arrangeWindows()
            else:
                # only if piping the stream
                #commandByteStream = sender.readAll()
                commandByteStream = self.__getReply(command)
                if self.sendMessageBackToSender:
                    self.broadcast(self.connections, commandByteStream)
                else:
                    sockets = copy(self.connections)
                    sockets.remove(sender)
                    self.broadcast(sockets, commandByteStream)
            sender.nextBlockSize = 0

    def __getReply(self, payload):
        reply = QByteArray()
        stream = QDataStream(reply, QIODevice.WriteOnly)
        stream.setVersion(QDataStream.Qt_4_2)
        stream.writeUInt32(0)
        stream.writeQVariant(payload)
        stream.device().seek(0)
        stream.writeUInt32(reply.size() - SIZEOF_UINT32)
        return reply

    def returnClientList(self, sockets):
        clients = []
        for connection in self.connections:
            clients.append({
                "descriptor": connection.socketDescriptor(),
                "address": connection.peerAddress().toString(),
                "port": connection.peerPort()
            })
        reply = self.__getReply(CommandConnectedClients(clients))
        for socket in sockets:
            socket.write(reply)
        
    def broadcast(self, sockets, commandByteStream):
        for socket in sockets:
            socket.write(commandByteStream)

    def arrangeWindows(self):
        # - group connections by peerAddress
        # - find best arrangement
        connectionsGroupedPerAddress = {}
        for connection in self.connections:
            if connection.peerAddress().toString() in connectionsGroupedPerAddress:
                connectionsGroupedPerAddress[connection.peerAddress().toString()].append(connection)
            else:
                connectionsGroupedPerAddress[connection.peerAddress().toString()] = [connection]                
                
        print connectionsGroupedPerAddress
        for key in connectionsGroupedPerAddress:            
            windowCount = len(connectionsGroupedPerAddress[key])
            if windowCount == 1:
                for connection in connectionsGroupedPerAddress[key]:
                    connection.write( self.__getReply(CommandSetWindowPosition(positionFullscreen)) )
            elif windowCount == 2:                
                connectionsGroupedPerAddress[key][0].write( self.__getReply(CommandSetWindowPosition(positionLeft)) )
                connectionsGroupedPerAddress[key][1].write( self.__getReply(CommandSetWindowPosition(positionRight)) )
            elif windowCount == 3:
                connectionsGroupedPerAddress[key][0].write( self.__getReply(CommandSetWindowPosition(positionLeft)) )
                connectionsGroupedPerAddress[key][1].write( self.__getReply(CommandSetWindowPosition(positionUpperRight)) )
                connectionsGroupedPerAddress[key][2].write( self.__getReply(CommandSetWindowPosition(positionLowerRight)) )
            elif windowCount >= 4:
                connectionsGroupedPerAddress[key][0].write( self.__getReply(CommandSetWindowPosition(positionUpperLeft)) )
                connectionsGroupedPerAddress[key][1].write( self.__getReply(CommandSetWindowPosition(positionUpperRight)) )
                connectionsGroupedPerAddress[key][2].write( self.__getReply(CommandSetWindowPosition(positionLowerRight)) )
                connectionsGroupedPerAddress[key][3].write( self.__getReply(CommandSetWindowPosition(positionLowerLeft)) )

    def removeConnection(self):
        self.connections.remove(self.sender())
        self.returnClientList(self.connections)

    def socketError(self):
        self.sender().disconnectFromHost()
        self.returnClientList(self.connections)