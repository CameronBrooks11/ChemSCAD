#!/usr/bin/python
# coding: utf-8


import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets

from ccad.in_out import InputOutput
import ccad.constants as cst


class AddTopIODialog(QtWidgets.QDialog):

    """
    Dialog box opened from module_reactor when the user adds/modify a top inlet
    """

    def __init__(self, parent=None, io_dict=None):

        super(AddTopIODialog, self).__init__(parent)

        self.setModal(True)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent

        self.io_dict = io_dict

        if parent is None:
            sys.path.append(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
            from log import MyLog

            self.l = MyLog("activity.log")

            # Dummy file for saving if testing
            # self.options = QtCore.QSettings("debug/options.ini",
            # QtCore.QSettings.IniFormat)

            self.test = True

            self.TOP_LUER = "Luer top inlet"
            self.TOP_CUSTOM = "Custom top inlet"
        else:
            self.l = self.parent.l
            # self.options = self.parent.options
            self.test = False

            self.TOP_LUER = self.parent.TOP_LUER
            self.TOP_CUSTOM = self.parent.TOP_CUSTOM

        self.l.debug("AddTopIODialog opened")

        self.initUI()
        self.defineSlots()

        # Dict to store module's features
        self.params = dict()
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # To close the window and build the module
        self.ok_button.clicked.connect(self.buildIO)

        # I/O type changed
        self.combo_type_io.currentIndexChanged.connect(self.typeIOChanged)

    def typeIOChanged(self):

        """Slot called when type of top I/O (Luer, custom, etc) is changed"""

        # Disable diameter field if top I/O is Luer
        if self.combo_type_io.currentText() == self.TOP_LUER:
            self.spin_diameter.setEnabled(False)
            self.spin_length.setEnabled(False)
            self.spin_diameter.setValue(cst.D_EXT_INLET)
            self.spin_length.setValue(cst.L_EXT_INLET)
        elif self.combo_type_io.currentText() == self.TOP_CUSTOM:
            self.spin_diameter.setEnabled(True)
            self.spin_length.setEnabled(True)

    def restoreParams(self):

        """
        If a dict is provided to the class, we are updating the object.
        Restore the parameters previously entered to the display
        """

        # If no io_dict, we're creating an input, nothing to restore
        if self.io_dict is None:
            return

        # Get the values of the object from self.io_dict
        # These 2 parameters are injected by the parent in the io_dict
        self.params["name"] = self.io_dict["name"]
        self.params["type_io"] = self.io_dict["type_io"]

        # Get the values of the object from self.io_dict
        self.params["diameter"] = self.io_dict["diameter"]
        self.params["walls"] = self.io_dict["walls"]
        self.params["length"] = self.io_dict["length"]

        # Set values for graphical elements
        # Disable name editing
        self.line_name.setText(self.params["name"])
        self.line_name.setEnabled(False)

        # Restore type of I/O to combo box
        if self.params["type_io"] == "luer":
            self.combo_type_io.setCurrentIndex(0)
            self.spin_diameter.setEnabled(False)
        else:
            self.combo_type_io.setCurrentIndex(1)

        # Disable combo box for type of I/O, user cant' change it
        self.combo_type_io.setEnabled(False)

        self.spin_diameter.setValue(self.params["diameter"])
        self.spin_walls.setValue(self.params["walls"])
        self.spin_length.setValue(self.params["length"])

        # TODO: handle check box for auto-placement

        # 'external' is a bool, convert it to text for display in combo box
        # if self.params['external']:
        # self.combo_external.setCurrentText('External')
        # else:
        # self.combo_external.setCurrentText('Internal')

        # self.spin_angle.setValue(self.params['angle'])

    def readForm(self):

        """
        Read the form, and get the parameters of the I/O. Put them in a dict
        """

        self.params["name"] = self.line_name.text()
        self.params["type_io"] = self.combo_type_io.currentText()
        self.params["diameter"] = self.spin_diameter.value()
        self.params["walls"] = self.spin_walls.value()
        self.params["length"] = self.spin_length.value()

        # Transform combo box text to valid value for TopInlet object
        if self.params["type_io"] == self.TOP_LUER:
            self.params["type_io"] = "luer"
        else:
            self.params["type_io"] = "custom"

        # Get the state of the auto_placement check box
        auto_placement = self.check_placement.checkState()
        if auto_placement == 2:
            auto_placement = True
        else:
            auto_placement = False

        self.params["auto_placement"] = auto_placement

    def _checkIOName(self, name: str) -> bool:

        """
        Check io's name is valid (not already used by otherI/O), otherwise
        display error dialog box
        """

        # If updating I/O, name is valid
        if self.io_dict is not None:
            return True

        mes = """
        An I/O with this name already exists for this reactor.\n
         Please use another name
        """

        mes2 = """
        You can't use an empty name for an I/O.\n
         Please give a name to this I/O
        """

        mes = mes.replace("    ", "")

        # Build a list of all I/O names
        names = (
            list(self.parent.dict_inputs)
            + list(self.parent.dict_outputs)
            + list(self.parent.dict_top_inlets)
        )

        if name in names:

            self.l.debug("Invalid name for I/O, display error dialog")
            QtWidgets.QMessageBox.critical(
                self, "Naming error", mes, QtWidgets.QMessageBox.Ok
            )

            return False

        if not name:

            self.l.debug("Invalid (empty) name for I/O, display error dialog")
            QtWidgets.QMessageBox.critical(
                self, "Naming error", mes2, QtWidgets.QMessageBox.Ok
            )

            return False

        return True

    def buildIO(self):

        """
        Called when user clicks the OK button. Will read the form  and call the
        parent to add the I/O
        """

        self.readForm()

        # If name is not valid, don't create I/O
        if not self._checkIOName(self.params["name"]):
            return

        if not self.test:
            self.parent.addTopInlet(self.params)

        # Close the settings window and free the memory
        self.close()

    def initUI(self):

        """Handles the display"""

        if self.io_dict is None:
            self.setWindowTitle("Add a top I/O")
        else:
            self.setWindowTitle("Modify a top I/O")

        # ----------------- BASIC SETTINGS ------------------------------------

        widget_form_basic = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_basic.setLayout(fbox)

        # Line edit for input's name
        self.line_name = QtWidgets.QLineEdit(self)

        # Combo box to choose input or output
        self.combo_type_io = QtWidgets.QComboBox(self)
        self.combo_type_io.addItems([self.TOP_LUER, self.TOP_CUSTOM])

        # Diameter
        self.spin_diameter = QtWidgets.QDoubleSpinBox(self)
        self.spin_diameter.setMinimum(0)

        # Disable diameter spin box cause combo_type_io is Luer when
        # creating window. Set diameter value for Luer inlet
        self.spin_diameter.setValue(cst.D_EXT_INLET)
        self.spin_diameter.setEnabled(False)

        # Length of inlet
        self.spin_length = QtWidgets.QDoubleSpinBox(self)
        self.spin_length.setMinimum(0)

        # Freeze length field if I/O is Luer
        self.spin_length.setValue(cst.L_EXT_INLET)
        self.spin_length.setEnabled(False)

        # Walls
        self.spin_walls = QtWidgets.QDoubleSpinBox(self)
        self.spin_walls.setMinimum(0)

        # Set walls to default value since Luer inlet is selected when
        # creating window, but don't disable field so user can adapt value
        # easily
        self.spin_walls.setValue(cst.WALLS)

        self.check_placement = QtWidgets.QCheckBox(self)
        self.check_placement.setCheckState(2)

        # # TODO: TEMPORARY value
        # self.spin_diameter.setValue(3)

        # Add widgets to form layout
        fbox.addRow("Name: ", self.line_name)
        fbox.addRow("Type: ", self.combo_type_io)
        fbox.addRow("Diameter: ", self.spin_diameter)
        fbox.addRow("Length: ", self.spin_length)
        fbox.addRow("Walls: ", self.spin_walls)
        fbox.addRow("Auto placement: ", self.check_placement)

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)

        self.ok_button = QtWidgets.QPushButton("OK", self)

        self.vbox_global.addWidget(widget_form_basic)
        self.vbox_global.addWidget(self.ok_button)

        self.setLayout(self.vbox_global)
        self.show()


if __name__ == "__main__":
    print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    app = QtWidgets.QApplication(sys.argv)
    obj = AddTopIODialog()
    sys.exit(app.exec_())
