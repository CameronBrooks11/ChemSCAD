#!/usr/bin/python
# coding: utf-8

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Union, List, Dict, Optional
from ccad import ReactorCAD
from ccad.object import ObjectCAD

from chemscad.log import MyLog


class Settings(QtWidgets.QDialog):

    """
    Display a dialog box. The user can enter his settings here.
    """

    def __init__(self, parent=None):

        super(Settings, self).__init__(parent)

        self.setModal(True)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent

        if parent is None:
            self.l = MyLog("activity.log")
            self.test = True
        else:
            self.l = self.parent.l
            self.options = self.parent.options
            self.test = False

        self.initUI()
        self.defineSlots()
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # User finished selecting tops to align
        self.ok_button.clicked.connect(self.readForm)

    def restoreParams(self):

        """
        Restore the user's preferences
        """

        if self.test:
            return

        # Restore turn_x and turn_y from Assembly
        self.spin_x.setValue(self.parent.ass.turn_x)
        self.spin_y.setValue(self.parent.ass.turn_y)

    def readForm(self):

        """
        Read the preferences
        """

        if self.test:
            return

        # Read turn_x and turn_y for assembly
        self.parent.ass.turn_x = self.spin_x.value()
        self.parent.ass.turn_y = self.spin_y.value()

        # General refresh from main window
        self.parent.refresh()

        self.close()

    def initUI(self):

        """Handles the display"""

        self.setWindowTitle("Assembly angle settings")
        self.setMinimumSize(400, 100)

        fbox = QtWidgets.QFormLayout()

        self.spin_x = QtWidgets.QSpinBox(self)
        self.spin_x.setMinimum(0)
        self.spin_x.setValue(2)

        self.spin_y = QtWidgets.QSpinBox(self)
        self.spin_y.setMinimum(0)
        self.spin_y.setValue(2)

        fbox.addRow("X turn:", self.spin_x)
        fbox.addRow("Y turn:", self.spin_y)

        self.ok_button = QtWidgets.QPushButton("OK", self)

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)
        self.vbox_global.addLayout(fbox)
        self.vbox_global.addWidget(self.ok_button)

        self.setLayout(self.vbox_global)
        self.show()
    


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    obj = Settings()
    sys.exit(app.exec_())
