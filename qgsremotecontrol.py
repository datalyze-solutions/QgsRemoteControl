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
 *   (at your option) any later version.                                   *
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
        self.server = None
        self.client = None
        self.config = ConfigurationSettings()

    def initGui(self):
        # setup toolbar actions
        self.actionServerStart = QAction(QIcon(":/icons/call-start.png"), u"start server", self.iface.mainWindow())
        self.actionServerStop = QAction(QIcon(":/icons/call-stop.png"), u"stop server", self.iface.mainWindow())
        self.actionServerStart.triggered.connect(self.startServer)

        self.actionClientConnect = QAction(QIcon(":/icons/network-connect.png"), u"connect client", self.iface.mainWindow())
        self.actionClientDisconnect = QAction(QIcon(":/icons/network-disconnect.png"), u"disconnect client", self.iface.mainWindow())

        self.actionClientSync = QAction(QIcon(":/icons/system-switch-user.png"), u"sync windows", self.iface.mainWindow())
        self.actionClientSync.setChecked(False)
        self.actionClientSync.setCheckable(True)            


        self.remoteControlDockWidget = RemoteControlDockWidget()
        self.mainWindow.addDockWidget(Qt.RightDockWidgetArea, self.remoteControlDockWidget)
        self.remoteControlDockWidget.startServerToolButton.clicked.connect(self.startServer)

        self.remoteControlToolbar = QToolBar('QgsRemoteControlServer')
        self.remoteControlToolbar.setObjectName("QgsRemoteControlServer")
        self.remoteControlToolbar.addAction(self.actionServerStart)
        self.remoteControlToolbar.addAction(self.actionServerStop)
        self.remoteControlToolbar.addAction(self.actionClientConnect)
        self.remoteControlToolbar.addAction(self.actionClientDisconnect)
        self.remoteControlToolbar.addAction(self.actionClientSync)
        self.iface.mainWindow().addToolBar(Qt.TopToolBarArea, self.remoteControlToolbar)

        if self.config.serverAutostart:
            self.startServer()

    def startServer(self):
        try:
            if not self.server == None:
                self.actionServerStop.triggered.disconnect(self.server.shutdownServer)
                self.remoteControlDockWidget.stopServerToolButton.clicked.disconnect(self.server.shutdownServer)
                self.server.shutdownServer()
            
            self.server = QgsRemoteCommandServer(host=self.config.serverAddress, port=self.config.port)
            self.actionServerStop.triggered.connect(self.server.shutdownServer)
            self.remoteControlDockWidget.stopServerToolButton.clicked.connect(self.server.shutdownServer)

            self.client = QgsRemoteCommandClient(self.iface, host=self.config.serverAddress, port=self.config.port)
            self.actionClientConnect.triggered.connect(self.client.connectToServer)
            self.actionClientDisconnect.triggered.connect(self.client.disconnectFromServer)
            self.actionClientSync.toggled.connect(self.client.setSynced)

            self.client.disconnected.connect(self.clientDisconnected)
            
        except Exception as e:
            raise e                   
        
    def unload(self):
        # Remove the plugin menu item and icon
        self.mainWindow.removeToolBar(self.remoteControlToolbar)
        self.mainWindow.removeDockWidget(self.remoteControlDockWidget)
        
        try:
            self.client.close()
            self.server.shutdownServer()
        except:
            raise

    def clientDisconnected(self):
        self.iface.messageBar().pushMessage("Warning", "Remote Client disconnected or Remote Server is shutdown", level=QgsMessageBar.WARNING, duration=3)