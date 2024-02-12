#!/usr/bin/python
# coding: utf-8

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Union, List, Dict, Optional
from ccad import ReactorCAD
from ccad.object import ObjectCAD

from chemscad.log import MyLog

class help_info(QtWidgets.QDialog):

    """
    Display an 'About ChemSCAD' window. The user can view info about the software including contributers, repository, current version, pip package info etc.
    """

    def __init__(self, parent=None):

        super(help_info, self).__init__(parent)

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

    def defineSlots(self):

        """Establish the slots"""

        # User finished selecting tops to align
        self.ok_button.clicked.connect(self.closeSettings)

    def closeSettings(self):

        """
        Close the settings window
        """

        if self.test:
            return

        # General refresh from main window
        self.parent.refresh()

        self.close()


    def initUI(self):
        self.title="About ChemSCAD"
        self.ok_button = QtWidgets.QPushButton("OK", self)
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("Name: ChemSCAD\nVersion: 2.0\nDescription: software for generating reactionware objects")
        msgBox.setWindowTitle(self.title)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msgBox.exec()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    obj = help_info()
    sys.exit(app.exec_())

