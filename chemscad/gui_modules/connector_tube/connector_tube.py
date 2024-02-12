#!/usr/bin/python
# coding: utf-8


import sys
import os
from typing import Union
from PyQt5 import QtGui, QtCore, QtWidgets

from ccad import TubeConnectorCAD as tube
from ccad.exceptions import *


class ChemModule(QtWidgets.QDialog):

    """Tube connector module. To connect reactor-like objects"""

    def __init__(self, parent=None, cad_obj: Union[None, tube] = None):

        """Dialog box for tube"""

        super(ChemModule, self).__init__(parent)

        self.setModal(True)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent

        self.cad_obj = cad_obj

        # Dict to store module's features
        self.params = dict()

        if parent is None:
            sys.path.append(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
            from log import MyLog

            self.l = MyLog("activity.log")

            # # Dummy file for saving if testing
            # self.options = QtCore.QSettings("debug/options.ini",
            # QtCore.QSettings.IniFormat)

            self.test = True
        else:
            self.l = self.parent.l
            # self.options = self.parent.options
            self.test = False

        self.path = os.path.dirname(os.path.abspath(__file__))
        self.l.debug(f"Module path: {self.path}")

        self.initUI()
        self.defineSlots()

        # Dicts to store I/O and objects by name
        self.dict_inputs = dict()
        self.dict_outputs = dict()
        self.dict_objects = dict()

        # Load the values in combo boxes and fill dicts above
        self.loadValues()
        self.adjustSize()  # Adjust size of dialog to fit contents of combo boxes.
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # To close the window and build the module
        self.ok_button.clicked.connect(self.buildModule)

        # To close the window and delete the module
        self.del_button.clicked.connect(self.deleteModule)
        self.del_button.setShortcut("Del")

    def readForm(self):

        """
        Read the form, and get the parameters of the module. Put them in a dict
        """

        # Get the name of the input I/O
        in_io_name = self.combo_in_io.currentText()
        out_io_name = self.combo_out_io.currentText()

        # If one I/O has no name, it was empty. Display error message and exit
        if not in_io_name or not out_io_name:
            self.l.debug("Missing I/O for tube")

            mes = "At least one I/O is missing"
            QtWidgets.QMessageBox.critical(
                self, "Missing IO", mes, QtWidgets.QMessageBox.Ok
            )

            raise MissingConnector("Missing I/O")

        self.params["in_io"] = self.dict_outputs[in_io_name]
        self.params["out_io"] = self.dict_inputs[out_io_name]

        # Get the input object from the name of input I/O.
        # Avoids using another combo box for input object
        obj_in_nbr = in_io_name[-1]
        for name in self.dict_objects:
            if str(obj_in_nbr) in name:
                obj_in = self.dict_objects[name]
                break

        # Get the output object from the name of output I/O.
        # Avoids using another combo box for output object
        obj_out_nbr = out_io_name[-1]
        for name in self.dict_objects:
            if obj_out_nbr in name:
                obj_out = self.dict_objects[name]
                break

        self.params["obj_in"] = obj_in
        self.params["obj_out"] = obj_out

        # Get the text for the conflicts strategy
        conflicts = self.combo_conflicts.currentText()

        # Transform the text to an API str parameter
        if conflicts == "Lift input object":
            self.params["conflicts"] = "lift_in_obj"
        elif conflicts == "Lift output object":
            self.params["conflicts"] = "lift_out_obj"
        elif conflicts == "Move output":
            self.params["conflicts"] = "move_out_io"

        length = self.spin_length.value()
        self.params["length"] = length

        self.l.debug(f"tube, form read: {self.params}")

    def restoreParams(self):

        """
        If a CAD object is provided, we are updating the object.
        Restore the parameters previously entered to the display
        """

        # If no cad_obj, we're creating a module, nothing to restore
        if self.cad_obj is None:
            return

        # Restore input and output objects to parameters
        for name, obj in self.dict_objects.items():
            if obj is self.cad_obj.obj_in:
                self.params["obj_in"] = obj
                continue
            elif obj is self.cad_obj.obj_out:
                self.params["obj_out"] = obj
                continue

        # Restore input to parameters
        for name, io in self.dict_outputs.items():
            if io is self.cad_obj.in_io:
                self.params["in_io"] = io
                self.combo_in_io.setCurrentIndex(self.combo_in_io.findText(name))
                break

        # Restore output to parameters
        for name, io in self.dict_inputs.items():
            if io is self.cad_obj.out_io:
                self.params["out_io"] = io
                self.combo_out_io.setCurrentIndex(self.combo_out_io.findText(name))
                break

        # Restore the conflict strategy in the combo box
        if self.cad_obj.conflicts == "lift_in_obj":
            self.combo_conflicts.setCurrentText("Lift input object")
        elif self.cad_obj.conflicts == "lift_out_obj":
            self.combo_conflicts.setCurrentText("Lift output object")
        elif self.cad_obj.conflicts == "move_out_io":
            self.combo_conflicts.setCurrentText("Move output")

        # Restore length of connector
        self.params["length"] = self.cad_obj.length
        self.spin_length.setValue(self.params["length"])
        self.spin_length.setEnabled(True)

        self.l.debug(f"TubeConnector, parameters restored: {self.params}")

    def buildModule(self):

        """
        Called when user clicks the OK button. Will read the form, build the 3D
        model of the module, and tell the parent to display the module
        """

        # TODO: generate an image of the module, and build the CAD object

        # Don't do anything if missing I/O
        try:
            self.readForm()
        except MissingConnector:
            self.l.error("Siphon called w missing connector. Exit")
            return

        if not self.test:
            if self.cad_obj is None:
                self._buildNewModule()
            else:
                self._updateModule()

        # Close the settings window and free the memory
        self.close()

    def deleteModule(self):

        """
        Called when user clicks the delete button. 
        It will delete the selected module
        """

        self.l.debug("Tube, deleteModule")
        self.parent.deleteModule(self.cad_obj)

        # Close the settings window and free the memory
        self.close()

    def _buildNewModule(self) -> bool:

        """
        Internal method called when building the object for the first time
        """

        self.l.debug("TubeConnector, _buildNewModule")

        obj_in = self.params["obj_in"]
        in_io = self.params["in_io"]
        obj_out = self.params["obj_out"]
        out_io = self.params["out_io"]
        conflicts = self.params["conflicts"]

        try:
            con = tube(obj_in, in_io, obj_out, out_io, conflicts)
        except Exception as e:
            mes = f"Impossible to create tube connector: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Creation error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        self.parent.buildModule(con)

        return True

    def _updateModule(self) -> bool:

        self.l.debug("TubeConnector, _updateModule")

        obj_in = self.params["obj_in"]
        in_io = self.params["in_io"]
        obj_out = self.params["obj_out"]
        out_io = self.params["out_io"]
        conflicts = self.params["conflicts"]
        length = self.params["length"]

        self.cad_obj.obj_in = obj_in
        self.cad_obj.in_io = in_io
        self.cad_obj.obj_out = obj_out
        self.cad_obj.out_io = out_io
        self.cad_obj.conflicts = conflicts
        self.cad_obj.length = length

        # TODO: check if object changed before calling refresh
        self.parent.refresh()

        return True

    def loadValues(self):

        """
        Load the values/name for combo boxes (choices for I/O and objects)
        Only consider unconnected I/O, disable others
        https://stackoverflow.com/questions/29971030/pyqt-enable-disable-elements-in-a-qcombobox
        """

        self.l.debug("Siphon, loading values")

        if self.test:
            return

        # List of objects
        self.dict_objects = self.parent.ass.reactors_names

        self.dict_outputs = self.parent.ass.outputs
        for name, io in self.dict_outputs.items():
            self.combo_in_io.addItem(name)

            # Disable I/O in choices if connected
            if io.connected:
                index = self.combo_in_io.count() - 1
                self.combo_in_io.model().item(index).setEnabled(False)

        self.dict_inputs = self.parent.ass.inputs
        for name, io in self.dict_inputs.items():
            self.combo_out_io.addItem(name)

            # Disable I/O in choices if connected
            if io.connected:
                index = self.combo_out_io.count() - 1
                self.combo_out_io.model().item(index).setEnabled(False)

    def initUI(self):

        """Handles the display"""

        self.setWindowTitle("Add a tube connector")

        # self.tabs = QtWidgets.QTabWidget(self)

        # ----------------- BASIC SETTINGS ------------------------------------

        fbox = QtWidgets.QFormLayout()
        # Combo box to choose input I/O
        self.combo_in_io = QtWidgets.QComboBox(self)
        self.combo_in_io.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        # Combo box to choose output I/O
        self.combo_out_io = QtWidgets.QComboBox(self)
        self.combo_out_io.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

        self.combo_conflicts = QtWidgets.QComboBox(self)
        self.combo_conflicts.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        list_conflicts = ["Lift input object", "Lift output object", "Move output"]
        self.combo_conflicts.addItems(list_conflicts)

        # Combo box to set length of connector
        self.spin_length = QtWidgets.QDoubleSpinBox(self)
        self.spin_length.setMinimum(0)
        self.spin_length.setEnabled(False)

        # Add widgets to form layout
        fbox.addRow("Input I/O: ", self.combo_in_io)
        fbox.addRow("Output I/O: ", self.combo_out_io)
        fbox.addRow("Conflicts: ", self.combo_conflicts)
        fbox.addRow("Length: ", self.spin_length)

        # ----------------- ASSEMBLING ----------------------------------------

        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.del_button = QtWidgets.QPushButton("Delete", self)
        split_butttons = QtWidgets.QHBoxLayout()
        split_butttons.addWidget(self.ok_button)
        split_butttons.addWidget(self.del_button)

        # if new object only display ok button
        if self.cad_obj is None:
            self.del_button.setVisible(False)

        fbox.addRow(split_butttons)

        self.setLayout(fbox)
        self.show()


if __name__ == "__main__":
    print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    app = QtWidgets.QApplication(sys.argv)
    obj = ChemModule()
    sys.exit(app.exec_())
