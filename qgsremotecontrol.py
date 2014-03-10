# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgsRemoteControl
                                 A QGIS plugin
 QgsRemoteControl
                              -------------------
        begin                : 2014-02-28
        copyright            : (C) 2014 by Matthias Ludwig - Datalyze Solutions
        email                : m.ludwig@datalyze-solutions.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                           shutdown        *
 *                                                                         *
 ***************************************************************************/
"""

## server code adapted from: http://stackoverflow.com/questions/9355511/pyqt-qtcpserver-how-to-return-data-to-multiple-clients

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qgis.core import *
from qgis.gui import *
import os.path

import resources_rc
from config import ConfigurationSettings
from libs.remoteclient import QgsRemoteCommandClient
from libs.remoteserver import QgsRemoteCommandServer
from remotecontroldockwidget import RemoteControlDockWidget

class QgsRemoteControl(object): 

    #   - bind config to dockwidget
    #   - rewrite config as QSettings INI
    
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.mainWindow = self.iface.mainWindow()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'qgsremotecontrol_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # init variables
        self.config = ConfigurationSettings()
        self.server = QgsRemoteCommandServer(host=self.config.serverAddress, port=self.config.serverPort)
        self.client = QgsRemoteCommandClient(self.iface, host=self.config.clientAddress, port=self.config.clientPort)

    def initGui(self):
        # client actions
        self.actionClientConnectDisconnect = QAction(QIcon(":/icons/client-toggle.png"), u"connect/disconnect client", self.iface.mainWindow())
        self.actionClientConnectDisconnect.setChecked(False)
        self.actionClientConnectDisconnect.setCheckable(True)
        
        self.actionClientSync = QAction(QIcon(":/icons/system-switch-user.png"), u"sync windows", self.iface.mainWindow())
        self.actionClientSync.setChecked(False)
        self.actionClientSync.setCheckable(True)

        self.actionClientArrangeWindows = QAction(QIcon(":/icons/arrange-windows.png"), u"arrange windows", self.iface.mainWindow())

        # server actions
        self.actionServerStartStop = QAction(QIcon(":/icons/server-toggle.png"), u"start/stop server", self.iface.mainWindow())
        self.actionServerStartStop.setChecked(False)
        self.actionServerStartStop.setCheckable(True)

        # gui actions
        self.actionShowHideDockWidget = QAction(QIcon(":/icons/configure.png"), u"show/hide Remote Control Widget", self.iface.mainWindow())
        self.actionShowHideDockWidget.setChecked(False)
        self.actionShowHideDockWidget.setCheckable(True)

        # toolbar
        self.remoteControlToolbar = QToolBar('QgsRemoteControl')
        self.remoteControlToolbar.setObjectName("QgsRemoteControl")
        self.remoteControlToolbar.addAction(self.actionShowHideDockWidget)
        self.remoteControlToolbar.addAction(self.actionServerStartStop)
        self.remoteControlToolbar.addAction(self.actionClientConnectDisconnect)
        self.remoteControlToolbar.addAction(self.actionClientSync)
        self.remoteControlToolbar.addAction(self.actionClientArrangeWindows)        
        self.iface.mainWindow().addToolBar(Qt.TopToolBarArea, self.remoteControlToolbar)

        # dock widget
        self.remoteControlDockWidget = RemoteControlDockWidget()
        self.mainWindow.addDockWidget(Qt.RightDockWidgetArea, self.remoteControlDockWidget)
        self.remoteControlDockWidget.hide()        
        self.actionShowHideDockWidget.toggled.connect(self.remoteControlDockWidget.setVisible)

        # dock widget buttons --> config
        self.remoteControlDockWidget.serverAddressLineEdit.setText(self.config.serverAddress)
        self.remoteControlDockWidget.serverPortSpinBox.setValue(self.config.serverPort)
        self.remoteControlDockWidget.clientAddressLineEdit.setText(self.config.clientAddress)
        self.remoteControlDockWidget.clientPortSpinBox.setValue(self.config.clientPort)
        
        self.remoteControlDockWidget.serverAddressLineEdit.textChanged.connect(self.config.setServerAddress)
        self.remoteControlDockWidget.serverPortSpinBox.valueChanged.connect(self.config.setServerPort)
        self.remoteControlDockWidget.clientAddressLineEdit.textChanged.connect(self.config.setClientAddress)
        self.remoteControlDockWidget.clientPortSpinBox.valueChanged.connect(self.config.setClientPort)

        self.remoteControlDockWidget.serverAddressListenLocalhostToolButton.clicked.connect(self.config.setServerAddressToLocalhost)
        self.remoteControlDockWidget.serverAddressListenAllToolButton.clicked.connect(self.config.setServerAddressToAll)
        self.config.serverAddressChanged.connect(self.remoteControlDockWidget.serverAddressLineEdit.setText)

        self.remoteControlDockWidget.clientAddressListenLocalhostToolButton.clicked.connect(self.config.setClientAddressToLocalhost)
        self.config.clientAddressChanged.connect(self.remoteControlDockWidget.clientAddressLineEdit.setText)

        self.remoteControlDockWidget.serverPortDefaultToolButton.clicked.connect(self.config.setServerPortDefault)
        self.config.serverPortChanged.connect(self.remoteControlDockWidget.serverPortSpinBox.setValue)

        self.remoteControlDockWidget.clientPortDefaultToolButton.clicked.connect(self.config.setClientPortDefault)
        self.config.clientPortChanged.connect(self.remoteControlDockWidget.clientPortSpinBox.setValue)

        # Server
        self.actionServerStartStop.toggled.connect(self.startStopServer)
        self.remoteControlDockWidget.startStopServerToolButton.clicked.connect(self.startStopServer)
        
        ## Client
        self.actionClientConnectDisconnect.toggled.connect(self.connectDisconnectClient)
        self.remoteControlDockWidget.connectDisconnectClientToolButton.toggled.connect(self.connectDisconnectClient)
       
    def startStopServer(self, checked):
        if checked:
            self.server = QgsRemoteCommandServer(host=self.config.serverAddress, port=self.config.serverPort)
            self.connectServerControls()
            print "new server init"
        self.server.startStop(checked)
        
    def connectServerControls(self):
        # connect server actions and buttons
        self.server.signalServerStatus.connect(self.listenServerStatus)
        #self.actionServerStartStop.toggled.connect(self.startStopServer)
        #self.remoteControlDockWidget.startStopServerToolButton.clicked.connect(self.startStopServer)

    def disconnectServerControls(self):
        # connect server actions and buttons
        self.server.signalServerStatus.disconnect(self.listenServerStatus)
        #self.actionServerStartStop.toggled.disconnect(self.server.startStop)
        #self.remoteControlDockWidget.startStopServerToolButton.clicked.disconnect(self.server.startStop)

    def connectDisconnectClient(self, checked):        
        if checked:
            self.client = QgsRemoteCommandClient(self.iface, host=self.config.clientAddress, port=self.config.clientPort)
            self.actionClientArrangeWindows.triggered.connect(self.client.arrangeWindows)

            # client status
            self.actionClientSync.toggled.connect(self.client.setSynced)
            self.client.clientListUpdated.connect(self.clientListUpdated)
            self.client.stateChanged.connect(self.listenClientStatus)
            self.client.error.connect(self.clientError)
            
        self.client.connectDisconnect(checked)

    def setClientConnectDisconnectChecked(self, checked):
        self.actionClientConnectDisconnect.toggled.disconnect(self.connectDisconnectClient)
        self.remoteControlDockWidget.connectDisconnectClientToolButton.toggled.disconnect(self.connectDisconnectClient)

        self.actionClientConnectDisconnect.setChecked(checked)
        self.remoteControlDockWidget.connectDisconnectClientToolButton.setChecked(checked)

        self.actionClientConnectDisconnect.toggled.connect(self.connectDisconnectClient)
        self.remoteControlDockWidget.connectDisconnectClientToolButton.toggled.connect(self.connectDisconnectClient)                
        
    def listenServerStatus(self, isListening, modus):
        self.disconnectServerControls()
        
        if (not isListening) & (modus == "startListening"):
            self.iface.messageBar().pushMessage(self.config.pluginName, "Can't start server. Another server is still running or port used by something else.", level=QgsMessageBar.CRITICAL, duration=6)
        elif (not isListening) & (modus == "shutdown"):
            self.iface.messageBar().pushMessage(self.config.pluginName, "Server shutdown.", level=QgsMessageBar.INFO, duration=2)
        elif isListening & (modus == "startListening"):
            self.iface.messageBar().pushMessage(self.config.pluginName, "Server started.", level=QgsMessageBar.INFO, duration=2)

        self.actionServerStartStop.setChecked(isListening)
        self.remoteControlDockWidget.startStopServerToolButton.setChecked(isListening)
        self.connectServerControls()

    def listenClientStatus(self, state):
        if state == QAbstractSocket.UnconnectedState:
            print "UnconnectedState"           
            self.setClientConnectDisconnectChecked(False)
            self.actionClientSync.toggled.disconnect(self.client.setSynced)
            self.actionClientSync.setChecked(False)
            
            self.iface.messageBar().pushMessage(self.config.pluginName, "Client disconnected.", level=QgsMessageBar.INFO, duration=3)
        elif state == QAbstractSocket.HostLookupState:
            print "HostLookupState"
        elif state == QAbstractSocket.ConnectingState:
            print "ConnectingState"
        elif state == QAbstractSocket.ConnectedState:
            print "ConnectedState"
            self.setClientConnectDisconnectChecked(True)
            self.iface.messageBar().pushMessage(self.config.pluginName, "Client connected.", level=QgsMessageBar.INFO, duration=2)
        elif state == QAbstractSocket.BoundState:
            print "BoundState"
        elif state == QAbstractSocket.ClosingState:
            print "ClosingState"
        elif state == QAbstractSocket.ListeningState:
            print "ListeningState"
        else:
            print "unknown state...", state

    def clientError(self, error):
        self.iface.messageBar().pushMessage(self.config.pluginName, self.client.errorString(), level=QgsMessageBar.CRITICAL, duration=3)
    
    def clientListUpdated(self, clientListModel):
        self.remoteControlDockWidget.clientListView.setModel(clientListModel)
        
    def unload(self):
        try:
            self.config.writeSettings()
        except Exception as e:
            raise e
        
        # Remove the plugin menu item and icon
        self.mainWindow.removeToolBar(self.remoteControlToolbar)
        self.mainWindow.removeDockWidget(self.remoteControlDockWidget)
        
        try:
            self.server.close()
        except:
            pass

        try:
            self.client.close()
        except:
            pass        