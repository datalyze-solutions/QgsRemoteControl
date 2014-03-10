# -*- coding: utf-8 -*-
## @package config
#       The configuration
#  @file
#       The configuration

import os
from PyQt4.QtCore import QObject, QSettings, pyqtSignal, pyqtProperty
    
class ConfigurationSettings(QObject):

    # signal changed value
    serverAddressChanged = pyqtSignal(object)
    serverPortChanged = pyqtSignal(object)
    clientAddressChanged = pyqtSignal(object)
    clientPortChanged = pyqtSignal(object)    

    def __init__(self, iniPath="config.ini"):
        super(ConfigurationSettings, self).__init__()

        self.pluginDir = os.path.dirname(__file__)
        self.iniPath = os.path.join(self.pluginDir, iniPath)
        self.pluginName = "QgsRemoteControl"

        # init defaults
        self.__serverAddress = "127.0.0.1"
        #self.serverAddress = "0.0.0.0"
        self.__serverPort = 9615
        self.__clientAddress = "127.0.0.1"
        self.__clientPort = self.serverPort
        self.__taskbarHeight = 79
        self.__windowbarHeight = 26

        # read settings from file
        try:
            self.readSettings()
        except Exception as e:
            raise e

    def getSettings(self):
        return QSettings(self.iniPath, QSettings.IniFormat)

    def restoreDefaults(self):
        settings = self.getSettings()
        settings.setValue("serverAddress", "0.0.0.0")
        settings.setValue("serverPort", 9615)
        settings.setValue("clientAddress", "127.0.0.1")
        settings.setValue("clientPort", 9615)
        settings.setValue("taskbarHeight", 79)
        settings.setValue("windowbarHeight", 26)

    def readSettings(self):
        settings = self.getSettings()
        self.serverAddress = settings.value("serverAddress", type=str)
        self.serverPort = settings.value("serverPort", type=int)
        self.clientAddress = settings.value("clientAddress", type=str)
        self.clientPort = settings.value("clientPort", type=int)
        self.taskbarHeight = settings.value("taskbarHeight", type=int)
        self.windowbarHeight = settings.value("windowbarHeight", type=int)

    def writeSettings(self):
        settings = self.getSettings()
        settings.setValue("serverAddress", self.serverAddress)
        settings.setValue("serverPort", self.serverPort)
        settings.setValue("clientAddress", self.clientAddress)
        settings.setValue("clientPort", self.clientPort)
        settings.setValue("taskbarHeight", self.taskbarHeight)
        settings.setValue("windowbarHeight", self.windowbarHeight)

    @property
    def serverAddress(self):
        return self.__serverAddress
    @serverAddress.setter
    def serverAddress(self, IPv4AddressString):
        self.__serverAddress = IPv4AddressString
        self.serverAddressChanged.emit(self.__serverAddress)
    def setServerAddress(self, IPv4AddressString):
        self.serverAddress = IPv4AddressString

    @property
    def serverPort(self):
        return self.__serverPort
    @serverPort.setter
    def serverPort(self, port):
        print port
        self.__serverPort = port
    def setServerPort(self, port):
        self.serverPort = port

    @property
    def clientAddress(self):
        return self.__clientAddress
    @clientAddress.setter
    def clientAddress(self, IPv4AddressString):
        self.__clientAddress = IPv4AddressString
        self.clientAddressChanged.emit(self.__clientAddress)
    def setClientAddress(self, IPv4AddressString):
        self.clientAddress = IPv4AddressString

    @property
    def clientPort(self):
        return self.__clientPort
    @clientPort.setter
    def clientPort(self, port):
        self.__clientPort = port
    def setClientPort(self, port):
        self.clientPort = port

    def setServerAddressToLocalhost(self):
        self.serverAddress = "127.0.0.1"

    def setServerAddressToAll(self):
        self.serverAddress = "0.0.0.0"

    def setClientAddressToLocalhost(self):
        self.clientAddress = "127.0.0.1"

    def setClientPortDefault(self):
        self.clientPort = 9615

    def setServerPortDefault(self):
        self.serverPort = 9615

    @property
    def taskbarHeight(self):
        return self.__taskbarHeight
    @taskbarHeight.setter
    def taskbarHeight(self, height):
        self.__taskbarHeight = height
    def setTaskbarHeight(self, height):
        self.taskbarHeight = height

    @property
    def windowbarHeight(self):
        return self.__windowbarHeight
    @windowbarHeight.setter
    def windowbarHeight(self, height):
        self.__windowbarHeight = height
    def setWindowbarHeight(self, height):
        self.windowbarHeight = height