#!/usr/bin/python
# coding: utf-8

import os
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Union, List, Dict, Optional

from chemscad.log import MyLog

from ccad.object import ObjectCAD


class AlignFilters(QtWidgets.QDialog):

    """
    Create a modal window to select couples of modules with filters to
    align. The user will choose through a combo box. Will send the couples
    to the parent's assembly
    """

    def __init__(self, parent=None) -> None:

        super(AlignFilters, self).__init__(parent)

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

        # List of tuples of combo boxes
        self.list_boxes_align: List[QtWidgets.QComboBox] = list()

        self.initUI()
        self.defineSlots()

        self.loadValues()
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # Button to add line
        self.button_add_line.clicked.connect(self.addLine)

        # User finished selecting filters to align
        self.ok_button.clicked.connect(self.readForm)

    def loadValues(self):

        """
        Load the values/name that will be used in combo boxes
        """

        if self.test:
            return

        # Use a dict comprehension to only get objects with filter
        self.dict_objects: Dict[str, ObjectCAD] = {
            name: obj
            for name, obj in self.parent.ass.reactors_names.items()
            if hasattr(obj, "z_top_filter")
        }

    def restoreParams(self):

        """
        Will restore the filters that need to be aligned, from Assembly.
        Will create a ligne of combo boxes for each couple
        """

        if self.test:
            return

        # For all the couples of filters in the assembly
        for couple in self.parent.ass.list_align_filters:
            mod_mov, mod_target = couple

            # Find the name of the objects
            for name, obj in self.dict_objects.items():
                if mod_mov is obj:
                    name_mod_move = name
                elif mod_target is obj:
                    name_mod_target = name

            # Add a line of combo boxes with the names
            self.addLine(name_mod_move, name_mod_target)

    def readForm(self):

        """
        Slot called when OK button is pressed. Will read the lines of
        the form, and send the filters to align to the Assembly of the
        parent object
        """

        # Clean the list of filters to align in assembly, we'll rebuild
        # it below
        self.parent.ass.cleanAlignFilters()

        # For all the combo boxes in every line
        for i, couple in enumerate(self.list_boxes_align):
            combo_mov, combo_target = couple

            # Get the object from their name
            mod_mov = self.dict_objects[combo_mov.currentText()]
            mod_target = self.dict_objects[combo_target.currentText()]

            if mod_mov is mod_target:
                mes = f"Module selected twice on line {i + 1}. Line ignored"
                QtWidgets.QMessageBox.critical(
                    self, "Selection error", mes, QtWidgets.QMessageBox.Ok
                )

                continue

            # Try to align by by-passing assembly. If it doesn't fail,
            # tell the assembly to align
            try:
                mod_mov.alignFilterToHeight(mod_target.z_top_filter)
            except Exception as e:
                self.l.error("Problem with align_filters: {e}", exc_info=True)

                name_mod_mov = combo_mov.currentText()
                name_mod_target = combo_target.currentText()

                mes = "Impossible to align filters from {} and {}: {}"
                mes = mes.format(name_mod_mov, name_mod_target, e)
                QtWidgets.QMessageBox.critical(
                    self, "Refresh error", mes, QtWidgets.QMessageBox.Ok
                )
                continue

            # Add the couple to the list of filters to align in assembly
            self.parent.ass.addAlignFilters(mod_mov, mod_target)

        self.parent.refresh()
        self.close()

    def addLine(
        self, name_mod_move: Optional[str] = None, name_mod_target: Optional[str] = None
    ):

        """
        Slot called when the user presses the addLine button. Add a line
        for a new couple of filters to align
        """

        # Create 2 new combo boxes
        combo_mod_mov = QtWidgets.QComboBox()
        combo_mod_target = QtWidgets.QComboBox()

        if not self.test:
            combo_mod_mov.addItems(self.dict_objects.keys())
            combo_mod_target.addItems(self.dict_objects.keys())

        # If addLine is called overloaded, it's called from restoreParams,
        # restore the filters to be aligned
        if name_mod_move is not None:
            combo_mod_mov.setCurrentText(name_mod_move)
        if name_mod_target is not None:
            combo_mod_target.setCurrentText(name_mod_target)

        # Append the 2 new boxes to the list of combo boxes
        self.list_boxes_align.append((combo_mod_mov, combo_mod_target))

        # Create 2 labels to identify the combo boxes
        label_mov = QtWidgets.QLabel("Align filter of ")
        label_target = QtWidgets.QLabel("On filter of ")

        button_delete = QtWidgets.QPushButton("Delete", self)

        hbox_line = QtWidgets.QHBoxLayout()
        hbox_line.addWidget(label_mov)
        hbox_line.addWidget(combo_mod_mov)
        hbox_line.addWidget(label_target)
        hbox_line.addWidget(combo_mod_target)
        hbox_line.addWidget(button_delete)

        button_delete.clicked.connect(
            lambda: self.deleteLine(hbox_line, combo_mod_mov, combo_mod_target)
        )

        self.vbox_lines_couples.addLayout(hbox_line)

    def deleteLine(
        self,
        hbox: QtWidgets.QHBoxLayout,
        combo_mod_mov: QtWidgets.QComboBox,
        combo_mod_target: QtWidgets.QComboBox,
    ):

        """
        Delete a line of combo boxes when user presses delete button
        of the line
        """

        # Switch boolean for moving module
        mod_mov = self.dict_objects[combo_mod_mov.currentText()]
        mod_target = self.dict_objects[combo_mod_target.currentText()]

        # Remove couple from assembly. Let assembly do other operations
        self.parent.ass.removeCoupleAlignFilters((mod_mov, mod_target))

        self.list_boxes_align.remove((combo_mod_mov, combo_mod_target))
        self.clearLayout(hbox)

    def clearLayout(self, layout):

        """Method to erase the widgets from a layout"""

        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

                    QtWidgets.qApp.processEvents()
                else:
                    self.clearLayout(item.layout())

    def initUI(self):

        """Handles the display"""

        self.setWindowTitle("Filters to align")
        # self.setMinimumSize(200, 50)

        self.vbox_lines_couples = QtWidgets.QVBoxLayout()

        self.button_add_line = QtWidgets.QPushButton("Add line", self)
        self.ok_button = QtWidgets.QPushButton("OK", self)

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)
        self.vbox_global.addLayout(self.vbox_lines_couples)
        self.vbox_global.addWidget(self.button_add_line)
        self.vbox_global.addWidget(self.ok_button)

        self.setLayout(self.vbox_global)
        self.show()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    obj = AlignFilters()
    sys.exit(app.exec_())
