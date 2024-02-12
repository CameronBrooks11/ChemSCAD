#!/usr/bin/python
# coding: utf-8


import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets

from ccad.in_out import InputOutput
import ccad.constants as cst


class AddIODialogFR(QtWidgets.QDialog):

    """
    Dialog box opened from module_reactor when the user adds/modify a side I/O
    """

    def __init__(self, parent=None, io_dict=None):

        super(AddIODialogFR, self).__init__(parent)

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

            self.SIDE_INPUT = "Side Input"
            self.SIDE_OUTPUT = "Side Ouput"
        else:
            self.l = self.parent.l
            # self.options = self.parent.options
            self.test = False

            self.SIDE_INPUT = self.parent.SIDE_INPUT
            self.SIDE_OUTPUT = self.parent.SIDE_OUTPUT

        self.l.debug("AddIODialog opened")

        self.initUI()
        self.defineSlots()

        # Dict to store module's features
        self.params = dict()
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # Type IO changed (external/internal)
        self.combo_external.currentIndexChanged.connect(self.typeIOChanged)

        # To close the window and build the module
        self.ok_button.clicked.connect(self.buildIO)

    def typeIOChanged(self):

        """
        Type of IO changed (external/internal). Disable diameter spin box
        and set it to 5 mm if type is external
        """

        if self.combo_type_io.currentText() == "Internal":
            self.spin_diameter.setEnabled(True)
        else:
            self.spin_diameter.setValue(cst.D_EXT_INLET)
            self.spin_diameter.setEnabled(False)

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
        self.params["height_per"] = self.io_dict["height_per"]
        self.params["diameter"] = self.io_dict["diameter"]
        self.params["external"] = self.io_dict["external"]
        self.params["angle"] = self.io_dict["angle"]

        # Set values for graphical elements
        # Disable name editing
        self.line_name.setText(self.params["name"])
        self.line_name.setEnabled(False)

        # Restore type of I/O to combo box
        if self.params["type_io"] == self.SIDE_INPUT:
            self.combo_type_io.setCurrentIndex(0)
        elif self.params["type_io"] == self.SIDE_OUTPUT:
            self.combo_type_io.setCurrentIndex(1)

        # Disable combo box for type of I/O, user cant' change it
        self.combo_type_io.setEnabled(False)

        self.spin_height_per.setValue(self.params["height_per"])
        self.spin_diameter.setValue(self.params["diameter"])

        # 'external' is a bool, convert it to text for display in combo box
        if self.params["external"]:
            self.combo_external.setCurrentText("External")
        else:
            self.combo_external.setCurrentText("Internal")

        self.spin_angle.setValue(self.params["angle"])

    def readForm(self):

        """
        Read the form, and get the parameters of the input. Put them in a dict
        """

        self.params["name"] = self.line_name.text()
        self.params["type_io"] = self.combo_type_io.currentText()
        self.params["height_per"] = self.spin_height_per.value()
        self.params["diameter"] = self.spin_diameter.value()

        external = self.combo_external.currentText()
        if external == "External":
            external = True
        else:
            external = False

        self.params["external"] = external

        self.params["angle"] = self.spin_angle.value()

    def _checkIOName(self, name: str) -> bool:

        """
        Check io's name is valid (not already used by otherI/O), otherwise
        display error dialog box
        """

        if self.test:
            return True

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

            # Call different methods from parent depending of type of I/O:
            # input or output
            if self.params["type_io"] == self.SIDE_INPUT:
                self.parent.addInput(self.params)
            else:
                self.parent.addOutput(self.params)

        # Close the settings window and free the memory
        self.close()

    def initUI(self):

        """Handles the display"""

        if self.io_dict is None:
            self.setWindowTitle("Add an I/O")
        else:
            self.setWindowTitle("Modify I/O")

        # ----------------- BASIC SETTINGS ------------------------------------

        widget_form_basic = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_basic.setLayout(fbox)

        # Line edit for input's name
        self.line_name = QtWidgets.QLineEdit(self)

        # Combo box to choose input or output
        self.combo_type_io = QtWidgets.QComboBox(self)
        self.combo_type_io.addItems([self.SIDE_INPUT, self.SIDE_OUTPUT])

        # Percentage height
        self.spin_height_per = QtWidgets.QSpinBox(self)
        self.spin_height_per.setMinimum(0)
        self.spin_height_per.setMaximum(100)
        self.spin_height_per.setValue(100)

        # Diameter
        self.spin_diameter = QtWidgets.QDoubleSpinBox(self)
        self.spin_diameter.setMinimum(0)

        self.spin_diameter.setValue(cst.D_CAN)

        # Combo box to choose external or internal input
        self.combo_external = QtWidgets.QComboBox(self)
        self.combo_external.addItems(["Internal", "External"])

        # Spin box for input's angle
        self.spin_angle = QtWidgets.QSpinBox(self)
        self.spin_angle.setMinimum(-180)
        self.spin_angle.setMaximum(180)
        self.spin_angle.setValue(180)

        # Add widgets to form layout
        fbox.addRow("Name: ", self.line_name)
        fbox.addRow("Type: ", self.combo_type_io)
        fbox.addRow("Percentage height: ", self.spin_height_per)
        fbox.addRow("Diameter: ", self.spin_diameter)
        fbox.addRow("Outlet type: ", self.combo_external)
        fbox.addRow("Angle: ", self.spin_angle)

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
    obj = AddIODialogFR()
    sys.exit(app.exec_())
