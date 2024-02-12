#!/usr/bin/python
# coding: utf-8

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Union, List, Dict, Optional
from ccad import ReactorCAD
from ccad.object import ObjectCAD

from chemscad.log import MyLog

class FilterSettings(QtWidgets.QDialog):
    
    """
    Display a filter settings table. The user can view settings for filter dimensions here.
    """

    def __init__(self, parent=None):

        super(FilterSettings, self).__init__(parent)

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

        self.setWindowTitle("Filter Settings Information")
        self.setMinimumSize(440, 100)

        # Create table
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setRowCount(5)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.verticalHeader().hide()
        # Set the table headers
        self.tableWidget.setHorizontalHeaderLabels(["Filter Type", "Max Pore Size (µm)", "Mean Height (mm)", "Mean Width (mm)"])
 
        # Set the alignment to the headers
        self.tableWidget.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignCenter)
        self.tableWidget.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignHCenter)
        self.tableWidget.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignCenter)
 
        # Fill the first line
        self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem("0"))
        self.tableWidget.setItem(0, 1, QtWidgets.QTableWidgetItem("160 - 250"))
        self.tableWidget.setItem(0, 2, QtWidgets.QTableWidgetItem("3.54"))
        self.tableWidget.setItem(0, 3, QtWidgets.QTableWidgetItem("20.00"))

        self.tableWidget.setItem(1, 0, QtWidgets.QTableWidgetItem("1"))
        self.tableWidget.setItem(1, 1, QtWidgets.QTableWidgetItem("100 - 160"))
        self.tableWidget.setItem(1, 2, QtWidgets.QTableWidgetItem("3.54"))
        self.tableWidget.setItem(1, 3, QtWidgets.QTableWidgetItem("19.88"))

        self.tableWidget.setItem(2, 0, QtWidgets.QTableWidgetItem("2"))
        self.tableWidget.setItem(2, 1, QtWidgets.QTableWidgetItem("40 - 100"))
        self.tableWidget.setItem(2, 2, QtWidgets.QTableWidgetItem("3.99"))
        self.tableWidget.setItem(2, 3, QtWidgets.QTableWidgetItem("19.97"))

        self.tableWidget.setItem(3, 0, QtWidgets.QTableWidgetItem("3"))
        self.tableWidget.setItem(3, 1, QtWidgets.QTableWidgetItem("16 - 40"))
        self.tableWidget.setItem(3, 2, QtWidgets.QTableWidgetItem("3.83"))
        self.tableWidget.setItem(3, 3, QtWidgets.QTableWidgetItem("19.83"))

        self.tableWidget.setItem(4, 0, QtWidgets.QTableWidgetItem("4"))
        self.tableWidget.setItem(4, 1, QtWidgets.QTableWidgetItem("10 - 16"))
        self.tableWidget.setItem(4, 2, QtWidgets.QTableWidgetItem("3.46"))
        self.tableWidget.setItem(4, 3, QtWidgets.QTableWidgetItem("19.79"))
 
        # Do the resize of the columns by content
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.ok_button = QtWidgets.QPushButton("OK", self)

        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tableWidget) 
        self.layout.addWidget(self.ok_button)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addStretch(1)

        self.setLayout(self.layout) 

        # Show widget
        self.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    obj = FilterSettings()
    sys.exit(app.exec_())  

