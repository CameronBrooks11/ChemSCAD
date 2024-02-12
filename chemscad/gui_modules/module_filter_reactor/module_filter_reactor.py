#!/usr/bin/python
# coding: utf-8


import sys
import os
from typing import Optional
from PyQt5 import QtGui, QtCore, QtWidgets
from ccad import FilterReactorCAD as f_rea
from add_io_fr import AddIODialogFR
from add_top_io_fr import AddTopIODialogFR
from ccad.exceptions import *
import ccad.constants as cst


class ChemModule(QtWidgets.QDialog):

    """Filter reactor module. Simple cartridge where a reaction could happen"""

    # Define str for type of I/O
    SIDE_INPUT = "Side input"
    SIDE_OUTPUT = "Side output"
    DEF_OUTPUT = "Default output"
    TOP_LUER = "Luer top inlet"
    TOP_CUSTOM = "Custom top inlet"

    def __init__(self, parent=None, cad_obj: Optional[f_rea] = None) -> None:

        super(ChemModule, self).__init__(parent)

        self.setModal(True)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent

        self.cad_obj = cad_obj

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

        # Store inputs
        self.dict_inputs = dict()

        # Store outputs
        self.dict_outputs = dict()

        # Store top inlets
        self.dict_top_inlets = dict()

        # Dict to store module's features
        self.params = dict()
        self.restoreParams()

    def defineSlots(self):

        """Establish the slots"""

        # Bottom combo box changed
        self.combo_bottom.currentIndexChanged.connect(self.bottomTypeChanged)

        # Top combo box changed
        self.combo_top.currentIndexChanged.connect(self.topTypeChanged)

        # Radius constraint checkbox changed
        self.check_r_constrained.stateChanged.connect(self.rConstraintChanged)

        # To close the window and build the module
        self.ok_button.clicked.connect(self.buildModule)

        # To close the window and delete the module
        self.del_button.clicked.connect(self.deleteModule)
        self.del_button.setShortcut("Del")

        # Open dialog box to add I/O
        self.button_add_io.clicked.connect(self.openTypeIODialog)

        # Open dialog box to modify I/O from list of inputs
        self.table_io.itemDoubleClicked.connect(self.openIODialog)

        # Delete an I/O when button clicked
        self.button_delete_io.clicked.connect(self.deleteIO)

    def bottomTypeChanged(self):

        """
        Slot called when combo box for bottom changes. Will disable the
        spin box for diameter of internal pipe when bottom has no pipe
        """

        bottom_type = self.combo_bottom.currentText()

        if bottom_type in f_rea.BOTTOMS_PIPE:
            self.spin_d_can.setEnabled(True)
        else:
            self.spin_d_can.setEnabled(False)

    def topTypeChanged(self):

        """Disable the r spin box if top is threaded"""

        top_type = self.combo_top.currentText()

        if top_type in f_rea.THREADED_TOPS:
            # Threaded top:
            # - r_constrained checkbox is checked, do this first bc
            # checking it calls rConstraintChanged and enables spin radius
            # - disable setting radius
            # - disable check box for setting constraint on radius
            self.check_r_constrained.setCheckState(QtCore.Qt.Checked)
            self.spin_r.setEnabled(False)
            self.check_r_constrained.setEnabled(False)
        else:
            self.check_r_constrained.setEnabled(True)

    def rConstraintChanged(self):

        """
        Slot called when the state of the check box for the constraint of
        the radius changes. If it's not checked, radius is not constrained,
        disable spin box for radius. If it's checked, enable spin box
        for radius
        """

        if self.check_r_constrained.checkState() == QtCore.Qt.Unchecked:
            self.spin_r.setEnabled(False)
        elif self.check_r_constrained.checkState() == QtCore.Qt.Checked:
            self.spin_r.setEnabled(True)

    def deleteIO(self):

        """Slot: delete an input from the reactor"""

        # Get row for selected I/O
        try:
            row = self.table_io.selectionModel().selectedRows()[0].row()
        except IndexError:
            self.l.debug("No I/O selected, can't delete")
            return

        # Get name and type for I/O
        name = self.table_io.item(row, 0).text()
        type_io = self.table_io.item(row, 1).text()

        if type_io == self.DEF_OUTPUT:
            # We should never be here since selection is disabled for def
            # output, but just in case, return
            return

        elif type_io == self.SIDE_INPUT:
            del self.dict_inputs[name]
            # Delete I/O from CAD object
            if self.cad_obj is not None:
                del self.cad_obj.inputs[name]

        elif type_io == self.SIDE_OUTPUT:
            del self.dict_outputs[name]
            if self.cad_obj is not None:
                del self.cad_obj.outputs[name]

        else:
            del self.dict_top_inlets[name]
            if self.cad_obj is not None:
                del self.cad_obj.top_inlets[name]

        self.l.debug(f"Filter reactor, deleting I/O {name}")

        # Remove I/O line from table
        self.table_io.removeRow(row)

    def openTypeIODialog(self):

        """
        Create a small dialog box to let the user choose what type of I/O
        he wants to create: side I/O, or top I/O
        """

        dial = QtWidgets.QDialog(self)

        label_choice = QtWidgets.QLabel("What would you like to create:")

        button_side_io = QtWidgets.QPushButton("A side I/O")
        button_top_io = QtWidgets.QPushButton("A top I/O")

        button_side_io.clicked.connect(dial.accept)
        button_side_io.clicked.connect(lambda: AddIODialogFR(self))

        button_top_io.clicked.connect(dial.accept)
        button_top_io.clicked.connect(lambda: AddTopIODialogFR(self))

        hbox_dial = QtWidgets.QHBoxLayout()
        hbox_dial.addWidget(button_side_io)
        hbox_dial.addWidget(button_top_io)

        vbox_dial = QtWidgets.QVBoxLayout()
        vbox_dial.addWidget(label_choice, alignment=QtCore.Qt.AlignHCenter)
        vbox_dial.addLayout(hbox_dial)

        dial.setLayout(vbox_dial)

        dial.show()

    def openIODialog(self, item: QtWidgets.QTableWidgetItem):

        """
        Slot: open I/O dialog box when an I/O is double-clicked in the list
        of I/O
        """

        self.l.debug("Filter Reactor, opening I/O dialog box")

        # Get row for double-clicked I/O
        row = item.row()

        # Get name and type for I/O
        name = self.table_io.item(row, 0).text()
        type_io = self.table_io.item(row, 1).text()

        # Create a dict with name and type of I/O
        params = {"name": name, "type_io": type_io}

        # Get parameters for I/O from dicts
        if type_io == self.SIDE_INPUT:
            # Merge simple dict params with full dict for I/O
            params = {**params, **self.dict_inputs[name]}
            AddIODialogFR(self, params)
        elif type_io == self.SIDE_OUTPUT:
            params = {**params, **self.dict_outputs[name]}
            AddIODialogFR(self, params)
        else:
            params = {**params, **self.dict_top_inlets[name]}
            AddTopIODialogFR(self, params)

    def restoreParams(self):

        """
        If a CAD object is provided, we are updating the object.
        Restore the parameters previously entered to the display
        """

        # If no cad_obj, we're creating a module, nothing to restore
        if self.cad_obj is None:
            return

        # Get the values of the object from cad object
        self.params["volume"] = self.cad_obj.volume
        self.params["type_top"] = self.cad_obj.type_top
        self.params["type_bottom"] = self.cad_obj.type_bottom
        self.params["h_filter"] = self.cad_obj.h_filter
        self.params["d_filter"] = self.cad_obj.d_filter

        # Advanced settings
        self.params["d_can"] = self.cad_obj.d_can
        self.params["r"] = self.cad_obj.r
        self.params["r_constrained"] = self.cad_obj.r_constrained

        # Set values for graphical elements
        self.spin_vol.setValue(self.params["volume"])
        self.combo_top.setCurrentIndex(f_rea.TOPS.index(self.params["type_top"]))
        self.combo_bottom.setCurrentIndex(
            f_rea.BOTTOMS.index(self.params["type_bottom"])
        )
        self.spin_h_filter.setValue(self.params["h_filter"])
        self.spin_d_filter.setValue(self.params["d_filter"])

        # Advanced settings
        self.spin_d_can.setValue(self.params["d_can"])
        self.spin_r.setValue(self.params["r"])

        # Restore check box state for r constrained
        if self.params["r_constrained"]:

            # Check check box for constraint on radius
            self.check_r_constrained.setCheckState(QtCore.Qt.Checked)
            if self.params["type_top"] in f_rea.THREADED_TOPS:
                # Threaded top:
                # - disable spin radius
                # - disable check box for constraint
                self.spin_r.setEnabled(False)
                self.check_r_constrained.setEnabled(False)
            else:
                self.check_r_constrained.setEnabled(True)
        else:
            self.check_r_constrained.setCheckState(QtCore.Qt.Unchecked)
            self.spin_r.setEnabled(False)

        # Restore the align top strategy
        align_top_strategy = self.cad_obj.align_top_strategy
        if align_top_strategy == "expand":
            self.combo_align_top_strategy.setCurrentText("Expand body")
        elif align_top_strategy == "lift":
            self.combo_align_top_strategy.setCurrentText("Lift reactor")

        # Restore the align filter strategy
        align_filter_strategy = self.cad_obj.align_filter_strategy
        if align_filter_strategy == "adapt":
            self.combo_align_filter_strategy.setCurrentText("Adapt")
        elif align_filter_strategy == "lift":
            self.combo_align_filter_strategy.setCurrentText("Lift reactor")

        self.restoreIO()

        self.l.debug(f"Filter reactor, restored reactor: {self.params}")

    def restoreIO(self):

        """Restore the I/O of the cad object into the dialog box"""

        # Restore all inputs for object
        for name, in_io in self.cad_obj.inputs.items():
            height_per = self.cad_obj.getHeightPercentage(in_io)
            angle = in_io.angle
            diameter = in_io.diameter
            external = in_io.external
            connected = in_io.connected

            params = {
                "height_per": height_per,
                "angle": angle,
                "diameter": diameter,
                "external": external,
                "connected": connected,
            }

            self.l.debug(f"Filter reactor, restoring I/O {params}")

            self.dict_inputs[name] = params

            # Add I/O to the table
            self._addNewRow(name, self.SIDE_INPUT, connected)

        # Restore all outputs for object
        for name, out_io in self.cad_obj.outputs.items():
            height_per = self.cad_obj.getHeightPercentage(out_io)
            angle = out_io.angle
            diameter = out_io.diameter
            external = out_io.external
            connected = out_io.connected

            params = {
                "height_per": height_per,
                "angle": angle,
                "diameter": diameter,
                "external": external,
                "connected": connected,
            }

            self.l.debug(f"Filter reactor, restoring I/O {params}")

            self.dict_outputs[name] = params

            # Add I/O to the table
            if name == "default":
                # Different type of output if default
                self._addNewRow(name, self.DEF_OUTPUT, connected)
            else:
                self._addNewRow(name, self.SIDE_OUTPUT, connected)

        # Restore all top inlets for object
        for name, top_io in self.cad_obj.top_inlets.items():
            diameter = top_io.diameter
            length = top_io.length
            walls = top_io.walls
            type_io = top_io.type_io
            connected = False

            params = {
                "diameter": diameter,
                "length": length,
                "walls": walls,
                "type_io": type_io,
                "connected": connected,
            }

            self.l.debug(f"Filter reactor, restoring I/O {params}")

            self.dict_top_inlets[name] = params

            # Add I/O to the table
            self._addNewRow(name, type_io, connected)

        self.l.debug("Filter reactor, restored I/O")

    def readForm(self):

        """
        Read the form, and get the parameters of the module. Put them in a dict
        """

        self.params["volume"] = self.spin_vol.value()
        self.params["type_top"] = self.combo_top.currentText()
        self.params["type_bottom"] = self.combo_bottom.currentText()
        self.params["h_filter"] = self.spin_h_filter.value()
        self.params["d_filter"] = self.spin_d_filter.value()

        # Advanced settings
        self.params["d_can"] = self.spin_d_can.value()
        self.params["r"] = self.spin_r.value()

        # Check if r is constrained
        state = self.check_r_constrained.checkState()
        if state == QtCore.Qt.Unchecked:
            self.params["r_constrained"] = False
        elif state == QtCore.Qt.Checked:
            self.params["r_constrained"] = True

        # Get align top strategy and transform to usable string value
        align_top_strategy = self.combo_align_top_strategy.currentText()
        if align_top_strategy == "Expand body":
            align_top_strategy = "expand"
        elif align_top_strategy == "Lift reactor":
            align_top_strategy = "lift"
        self.params["align_top_strategy"] = align_top_strategy

        # Get align filter strategy and transform to usable string value
        align_filter_strategy = self.combo_align_filter_strategy.currentText()
        if align_filter_strategy == "Adapt":
            align_filter_strategy = "adapt"
        elif align_filter_strategy == "Lift reactor":
            align_filter_strategy = "lift"
        self.params["align_filter_strategy"] = align_filter_strategy

        self.l.debug(f"Filter reactor, read form {self.params}")

    def addInput(self, params: dict):

        """The AddIODialogFR class will call this method"""

        self.l.debug(f"Filter Reactor, adding input: {params}")

        name = params["name"]
        del params["name"]

        # If input not already in dict_inputs, add it to the table
        if name not in self.dict_inputs:
            self._addNewRow(name, params["type_io"])
            self.l.debug(f"module_filter_reactor: addInput {params}")
        else:
            self.l.debug(f"addInput, updating input {name} with {params}")

        self.dict_inputs[name] = params

    def addOutput(self, params: dict):

        """The AddIODialogFR class will call this method"""

        self.l.debug(f"Filter Reactor, adding output: {params}")

        name = params["name"]
        del params["name"]

        # If input not already in dict_outputs, add it to the table
        if name not in self.dict_outputs:
            self._addNewRow(name, params["type_io"])
            self.l.debug(f"module_filter_reactor: addOutput {params}")
        else:
            self.l.debug(f"addOutput, updating output {name} with {params}")

        self.dict_outputs[name] = params

    def addTopInlet(self, params: dict):

        """
        The AddTopIODialogFR class will call this method. Create a top inlet
        """

        self.l.debug(f"Filter Reactor, adding top inlet: {params}")

        name = params["name"]
        del params["name"]

        # If input not already in dict_top_inlets, add it to the table
        if name not in self.dict_top_inlets:
            self._addNewRow(name, params["type_io"])
            self.l.debug(f"module_filter_reactor: top inlet {params}")
        else:
            self.l.debug(f"addTopInlet, updating inlet {name} with {params}")

        self.dict_top_inlets[name] = params

    def _addNewRow(self, name: str, type_io: str, connected: bool = False):

        """Add a new row in the I/O table"""

        self.l.debug(f"Adding new row {name}, {type_io}")

        # Count nbr of rows
        row_count = self.table_io.rowCount()

        # Insert row at the end
        self.table_io.insertRow(row_count)

        # Create name and type of I/O items to insert in the table
        item_name = QtWidgets.QTableWidgetItem(name)

        # TopInlet objects have an attribute 'type_io'. InputOutput objects
        # don't, their type is determined based on which dict they are in
        # (inputs or outputs)
        if type_io == "custom":
            item_type_io = QtWidgets.QTableWidgetItem("Custom top inlet")
        elif type_io == "luer":
            item_type_io = QtWidgets.QTableWidgetItem("Luer top inlet")
        else:
            item_type_io = QtWidgets.QTableWidgetItem(type_io)

        # Create an item depending on the connection state of the I/O
        if connected:
            item_connected = QtWidgets.QTableWidgetItem("Connected")
        else:
            item_connected = QtWidgets.QTableWidgetItem("Not connected")

        # Disable selection for default output; can't do anything on it
        # from I/O tab
        if type_io == self.DEF_OUTPUT:
            item_name.setFlags(QtCore.Qt.NoItemFlags)
            item_type_io.setFlags(QtCore.Qt.NoItemFlags)
            item_connected.setFlags(QtCore.Qt.NoItemFlags)

        # Insert the 2 items in the table
        self.table_io.setItem(row_count, 0, item_name)
        self.table_io.setItem(row_count, 1, item_type_io)
        self.table_io.setItem(row_count, 2, item_connected)

    def buildInputs(self, cad_obj):

        """Build an input for the CAD object"""

        self.l.debug("Filter reactor, building inputs")

        for name, in_io in self.dict_inputs.items():
            cad_obj.addInputPercentage(
                name,
                in_io["height_per"],
                in_io["angle"],
                in_io["diameter"],
                in_io["external"],
            )

    def buildOutputs(self, cad_obj):

        """Build an ouput for the CAD object"""

        self.l.debug("Filter reactor, building outputs")

        for name, out_io in self.dict_outputs.items():
            if name == "default":
                continue

            cad_obj.addOutputPercentage(
                name,
                out_io["height_per"],
                out_io["angle"],
                out_io["diameter"],
                out_io["external"],
            )

    def buildTopInlets(self, cad_obj):

        """
        Build the top inlets. Also try to place them. For now, only
        auto-placement is supported
        """

        self.l.debug("Filter Reactor, building top inlets")

        for name, io in self.dict_top_inlets.items():

            try:
                cad_obj.addCustomTopInlet(
                    name, io["diameter"], io["length"], io["walls"], io["type_io"]
                )
            except IncompatibilityError:
                self.l.debug("can't build top inlet: no custom top")
                return

        # TODO: handle manual placement (later)
        try:
            cad_obj.autoPlaceTopInlets()
        except ConstraintError:
            self.l.debug("Can't auto-place top inlets, collision ?")
            mes = """
            Impossible to auto-place the top inlets. Collision ?
            """

            QtWidgets.QMessageBox.critical(
                self, "Auto-placement error", mes, QtWidgets.QMessageBox.Ok
            )

            return

    def buildModule(self):

        """
        Called when user clicks the OK button. Will read the form, build the 3D
        model of the module, and tell the parent to display the module
        """

        # TODO: generate an image of the module, and build the CAD object

        self.readForm()

        if not self.test:
            # If no CAD object provided, we're creating a new object
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

        self.l.debug("Reactor, deleteModule")
        self.parent.deleteModule(self.cad_obj)

        # Close the settings window and free the memory
        self.close()

    def _buildNewModule(self) -> bool:

        """
        Internal method called when building the object for the first time
        """

        self.l.debug("Filter reactor, _buildNewModule")

        try:
            reactor = self._buildCADObject()
        except Exception as e:
            mes = f"Impossible to create filter reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Creation error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        # Try to build I/Os
        try:
            self.buildInputs(reactor)
            self.buildOutputs(reactor)
            self.buildTopInlets(reactor)
        except Exception as e:
            mes = f"Impossible to create I/Os: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "I/Os error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        self.parent.buildModule(reactor)

        return True

    def _updateModule(self) -> bool:

        """
        Internal method called when updating the object with new form values
        """

        self.l.debug("Filter reactor, _updateModule")

        # Try to build a temporary reactor with the new parameters
        # If it fails, exit immediately
        try:
            _ = self._buildCADObject()
        except Exception as e:
            mes = f"Impossible to update reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Update error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        # Update radius and constraint on radius before updating rest
        # of the parameters, so if user uncheck the constraint check box,
        # reactor can be recalculated properly immediately
        # Try to set the radius only if top is not threaded
        if (
            self.params["r_constrained"]
            and self.params["type_top"] not in f_rea.THREADED_TOPS
        ):
            self.cad_obj.r = self.params["r"]
        else:
            self.cad_obj.r_constrained = False

        # If temporary reactor was built, update cad_object
        self.l.debug("Filter reactor, buildModule w cad_obj")

        self.cad_obj.volume = self.params["volume"]
        self.cad_obj.type_top = self.params["type_top"]
        self.cad_obj.type_bottom = self.params["type_bottom"]
        self.cad_obj.d_can = self.params["d_can"]
        self.cad_obj.h_filter = self.params["h_filter"]
        self.cad_obj.d_filter = self.params["d_filter"]
        self.cad_obj.align_top_strategy = self.params["align_top_strategy"]
        self.cad_obj.align_filter_strategy = self.params["align_filter_strategy"]

        # Try to build I/Os
        try:
            self.buildInputs(self.cad_obj)
            self.buildOutputs(self.cad_obj)
            self.buildTopInlets(self.cad_obj)
        except Exception as e:
            mes = f"Impossible to create I/Os: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "I/Os error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        try:
            self.parent.refresh()
        except Exception as e:
            mes = f"Impossible to refresh filter reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Refresh error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        return True

    def _buildCADObject(self) -> f_rea:

        """
        Use the parameters read from the form to build the CAD object. Does
        nothing else, no GUI task here
        """

        volume = self.params["volume"]
        type_top = self.params["type_top"]
        type_bottom = self.params["type_bottom"]
        d_filter = self.params["d_filter"]
        h_filter = self.params["h_filter"]

        # Advanced settings
        d_can = self.params["d_can"]
        r = self.params["r"]
        r_constrained = self.params["r_constrained"]
        align_top_strategy = self.params["align_top_strategy"]
        align_filter_strategy = self.params["align_filter_strategy"]

        # Build the CAD module
        self.l.debug("Filter reactor, buildModule wo cad_obj")

        reactor = f_rea(
            volume,
            type_top,
            type_bottom,
            d_filter,
            h_filter,
            d_can=d_can,
            align_top_strategy=align_top_strategy,
            align_filter_strategy=align_filter_strategy,
        )

        # Try to set the radius only if top is not threaded
        if r_constrained and type_top not in f_rea.THREADED_TOPS:
            reactor.r = r

        return reactor

    def initUI(self):

        """Handles the display"""

        if self.cad_obj is None:
            self.setWindowTitle("Add a filter reactor module")
        else:
            self.setWindowTitle("Modify filter reactor module")

        # Build the basic settings
        widget_form_basic = self._buildBasicSettings()

        # Build the advanced settings
        widget_form_advanced = self._buildAdvancedSettings()

        # Build the IO tab
        widget_io = self._buildIOTab()

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)

        self.tabs = QtWidgets.QTabWidget(self)

        self.tabs.addTab(widget_form_basic, "Basic")
        self.tabs.addTab(widget_form_advanced, "Advanced")
        self.tabs.addTab(widget_io, "Inputs/Outputs")

        self.ok_button = QtWidgets.QPushButton("OK", self)
        self.del_button = QtWidgets.QPushButton("Delete", self)
        split_butttons = QtWidgets.QHBoxLayout()
        split_butttons.addWidget(self.ok_button)
        split_butttons.addWidget(self.del_button)

        # if new object only display ok button
        if self.cad_obj is None:
            self.del_button.setVisible(False)

        # self.vbox_global.addLayout(fbox)
        self.vbox_global.addWidget(self.tabs)
        self.vbox_global.addLayout(split_butttons)

        self.setLayout(self.vbox_global)
        self.show()

    def _buildBasicSettings(self) -> QtWidgets.QWidget:

        """Build the basic settings tab"""

        widget_form_basic = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_basic.setLayout(fbox)

        # Spin box to specify reactor's volume
        self.spin_vol = QtWidgets.QDoubleSpinBox(self)

        # Set default and bound values
        self.spin_vol.setValue(20)
        self.spin_vol.setMaximum(200)
        self.spin_vol.setMinimum(0)

        # Combo box to choose top of reactor
        self.combo_top = QtWidgets.QComboBox(self)
        list_top = f_rea.TOPS
        self.combo_top.addItems(list_top)

        # Combo box to choose bottom of reactor
        self.combo_bottom = QtWidgets.QComboBox(self)
        list_bottoms = f_rea.BOTTOMS

        # Remove the simple round bottom of the choices, it's useless
        # If ValueError, the window was generated before and simple round
        # bottom is already removed
        try:
            list_bottoms.remove(f_rea.B_ROUND)
        except ValueError:
            self.l.debug("Round bottom already removed")

        self.combo_bottom.addItems(list_bottoms)

        # Spin box to enter the height of the filter
        # Set default and limit values
        self.spin_h_filter = QtWidgets.QDoubleSpinBox(self)
        self.spin_h_filter.setValue(3)
        self.spin_h_filter.setMinimum(0)
        self.spin_h_filter.setMaximum(1000)

        # Spin box to enter the diameter of the filter
        # Set default and limit values
        self.spin_d_filter = QtWidgets.QDoubleSpinBox(self)
        self.spin_d_filter.setValue(20)
        self.spin_d_filter.setMinimum(0)
        self.spin_d_filter.setMaximum(200)

        # Add widgets to form layout
        fbox.addRow("Reaction volume (mL): ", self.spin_vol)
        fbox.addRow("Top type: ", self.combo_top)
        fbox.addRow("Bottom type: ", self.combo_bottom)
        fbox.addRow("Filter thickness: ", self.spin_h_filter)
        fbox.addRow("Filter diameter: ", self.spin_d_filter)

        return widget_form_basic

    def _buildAdvancedSettings(self) -> QtWidgets.QWidget:

        """Build the widget for the advanced settings"""

        widget_form_advanced = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_advanced.setLayout(fbox)

        # Spin box for internal radius of reactor
        self.spin_r = QtWidgets.QDoubleSpinBox(self)
        self.spin_r.setEnabled(False)

        # Check box to change the state of radius constrained
        self.check_r_constrained = QtWidgets.QCheckBox(self)

        # Internal pipe diameter
        # Set default
        self.spin_d_can = QtWidgets.QDoubleSpinBox(self)
        self.spin_d_can.setValue(cst.D_CAN)

        # Combo box to choose how to align the top of the reactor
        self.combo_align_top_strategy = QtWidgets.QComboBox(self)
        self.combo_align_top_strategy.addItems(f_rea.ALIGN_TOP_STRATEGIES)

        # Combo box for align filter strategy
        self.combo_align_filter_strategy = QtWidgets.QComboBox(self)
        self.combo_align_filter_strategy.addItems(f_rea.ALIGN_FILTER_STRATEGIES)

        # Add widgets to form layout
        fbox.addRow("Reactor radius: ", self.spin_r)
        fbox.addRow("Radius constrained: ", self.check_r_constrained)
        fbox.addRow("Diameter internal pipe: ", self.spin_d_can)
        fbox.addRow("Align top strategy: ", self.combo_align_top_strategy)
        fbox.addRow("Align filter strategy: ", self.combo_align_filter_strategy)

        return widget_form_advanced

    def _buildIOTab(self) -> QtWidgets.QWidget:

        """Build the IO tab"""

        # I/O widget with layout
        widget_io = QtWidgets.QWidget(self)
        vbox_io = QtWidgets.QVBoxLayout()
        widget_io.setLayout(vbox_io)

        self.table_io = QtWidgets.QTableWidget(0, 3, self)
        self.table_io.setHorizontalHeaderLabels(["Name", "Type", "Connected"])
        self.table_io.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Stretch header to fill entire space
        self.table_io.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        # Disable header resizing
        self.table_io.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Selection selects entire rows
        self.table_io.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # Only select one row at a time
        self.table_io.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        # Button to add io (opens a dialog box)
        self.button_add_io = QtWidgets.QPushButton("Add I/O", self)

        # Button to remove selected io
        self.button_delete_io = QtWidgets.QPushButton("Delete I/O", self)

        # Add the widgets to the layout
        vbox_io.addWidget(self.table_io)
        vbox_io.addWidget(self.button_add_io)
        vbox_io.addWidget(self.button_delete_io)

        return widget_io


if __name__ == "__main__":
    print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    app = QtWidgets.QApplication(sys.argv)
    obj = ChemModule()
    sys.exit(app.exec_())
