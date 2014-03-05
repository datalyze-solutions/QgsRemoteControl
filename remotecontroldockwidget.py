# -*- coding: utf-8 -*-
## @package remoteControlDockWidget
#       This widget sets all information
#  @file
#       This widget sets all information

from PyQt4 import QtCore, QtGui
from ui_remotecontroldockwidget import Ui_RemoteControlDockWidget

class RemoteControlDockWidget(QtGui.QDockWidget, Ui_RemoteControlDockWidget):

    def __init__(self):
        super(RemoteControlDockWidget, self).__init__()
        self.setupUi(self)