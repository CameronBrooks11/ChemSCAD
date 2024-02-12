#!/usr/bin/python
# coding: utf-8

import os, math, sys
from typing import Union
from PyQt5 import QtGui, QtCore, QtWidgets
from time import sleep
import time as time

from ccad import FlowReactorCAD as rea
from add_io import AddIODialog
from add_top_io import AddTopIODialog
from ccad.exceptions import *
import ccad.constants as cst


class ChemModule(QtWidgets.QDialog):

    """Flow Reactor module. """

    def __init__(self, parent=None, cad_obj: Union[None, rea] = None):

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

        self.volume = self.calculateVolume()

    def defineSlots(self):

        """Establish the slots"""

        # To close the window and build the module
        #self.ok_button.clicked.connect(self.buildModule)

        # To close the window and delete the module
        self.del_button.clicked.connect(self.deleteModule)
        self.del_button.setShortcut("Del")

        # Update volume when spinboxes change
        self.spin_npipes.valueChanged.connect(self.calculateVolume)
        self.spin_width.valueChanged.connect(self.calculateVolume)
        self.spin_radius.valueChanged.connect(self.calculateVolume)
        self.spin_spacing.valueChanged.connect(self.calculateVolume)
        self.spin_ninputs.valueChanged.connect(self.calculateVolume)


    def calculateVolume(self):

        """ Calculates the volume of the internal channels """

        npipes = self.spin_npipes.value()
        width = self.spin_width.value()
        radius = self.spin_radius.value()
        spacing = self.spin_spacing.value()
        inputs = self.spin_ninputs.value()
        
        total_volume, flowpath = self.getVolume(npipes, width, radius, spacing, inputs)

        text = "{:.{}f}".format( total_volume/1000, 2 )
        self.vol_label.setText(text +" ml")

        text = "{:.{}f}".format( flowpath/1000, 2 )
        self.flowpath_label.setText(text +" ml")


    def getVolume(self, npipes, width, radius, spacing, inputs):

        # First calculate the volume of the horizontal pipes
        vhpipe = math.pi * width * radius**2 # volume of 1 horizontal pipe
        vhpipes = vhpipe * npipes # multiply by npies

        # now volume of curved connecting pipes
        # volume of curved pipe is volume of half torus
        torus1 = math.pi*radius**2
        torus2 = 2*math.pi*spacing/2
        torus = (torus1*torus2) / 2 # we only have half torus
        ncurved = npipes + 1
        volcurved = torus*ncurved

        # each in/out has a quarter of a torus, remember torus is /2
        toio = torus
        # last 2 horizontal (half sized) pipes connecting to input output
        last_horizontal = math.pi*(radius**2)*(width/2-spacing/2)
        toio += last_horizontal * 2
        # we add the last horizontal pipe bit connecting to outlet
        toio += math.pi*(radius**2)*spacing

        # now the volume of the inlets
        invol = math.pi*(radius**2)*(spacing/2)
        if inputs in [1,3]: # add volume of central outlet
            invol += math.pi*(radius**2)*spacing
        if inputs in [2,3]: # add volume of 2 extra outlets
            invol += math.pi*(radius**2)*20 # horizontal pipe - HPD - 13/02/20 - changed 10 to 18 to reflect change in distpipes value
            invol += torus # 2 last 1/4 torus
            invol += (math.pi*(radius**2)*spacing)*2#last piping

        total_volume = vhpipes + volcurved + toio + invol
        flowpath = vhpipes + volcurved + toio

        return total_volume, flowpath

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
        self.params["npipes"] = self.cad_obj.npipes
        self.params["ninputs"] = self.cad_obj.ninputs
        self.params["width"] = self.cad_obj.width
        self.params["radius"] = self.cad_obj.radius
        self.params["spacing"] = self.cad_obj.spacing

        # Set values for graphical elements
        self.spin_npipes.setValue(self.params["npipes"])
        self.spin_ninputs.setValue(self.params["ninputs"])
        self.spin_width.setValue(self.params["width"])
        self.spin_radius.setValue(self.params["radius"])
        self.spin_spacing.setValue(self.params["spacing"])
        self.spin_volume.setValue(self.params["volume"])

        self.restoreIO()

        self.l.debug(f"Flow Reactor, restored flow reactor: {self.params}")

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

            self.l.debug(f"Flow Reactor, restoring I/O {params}")

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

            self.l.debug(f"Flow Reactor, restoring I/O {params}")

            self.dict_outputs[name] = params

            # Add I/O to the table
            if name == "default":
                # Different type of output if default
                self._addNewRow(name, self.DEF_OUTPUT, connected)
            else:
                self._addNewRow(name, self.SIDE_OUTPUT, connected)

        self.l.debug("Flow Reactor, restored I/O")

    def readForm_Basic(self):

        """
        Read the form, and get the parameters of the module. Put them in a dict 
        """
        self.params["npipes"] = self.spin_npipes.value()
        self.params["ninputs"] = self.spin_ninputs.value()
        self.params["width"] = self.spin_width.value()
        self.params["radius"] = self.spin_radius.value()
        self.params["spacing"] = self.spin_spacing.value()
        self.params["volume"] = self.spin_volume.value()
        self.l.debug(f"Flow reactor, read form {self.params}")

    def readForm_Advanced(self):

        """
        Read the form, and get the parameters of the module. Put them in a dict 
        """
        self.params["npipes"] = self.spin_npipes.value()
        self.params["ninputs"] = self.spin_ninputs.value()
        self.params["width"] = self.spin_width.value()
        self.params["radius"] = self.spin_radius.value()
        self.params["spacing"] = self.spin_spacing.value()
        self.params["volume"] = self.spin_volume.value()
        self.l.debug(f"Flow reactor, read form {self.params}")

    def setTemplate(self, template=None):

        template_1 = {
            'npipes': 8,
            'ninputs': 2,
            'width': 20,
            'radius': 0.8,
            'spacing': 6,
            'volume' : 1
            }
        template_2 = {
            'npipes': 24,
            'ninputs': 2,
            'width': 20,
            'radius': 0.8,
            'spacing': 6,
            'volume' : 1
            }
        template_3 = {
            'npipes': 8,
            'ninputs': 3,
            'width': 20,
            'radius': 0.8,
            'spacing': 6,
            'volume' : 1
            }
        template_4 = {
            'npipes': 24,
            'ninputs': 3,
            'width': 20,
            'radius': 0.8,
            'spacing': 6,
            'volume' : 1
            }

        if template == 'Template 1':
            for key, value in template_1.items():
                self.params[key] = value
                self.l.debug(f"Flow reactor, read form {self.params}")
            if not self.test:
            # If no CAD object provided, we're creating a new object
                if self.cad_obj is None:
                    self._buildNewModule()
                else:
                    self._updateModule()

        if template == 'Template 2':
            for key, value in template_2.items():
                self.params[key] = value
                self.l.debug(f"Flow reactor, read form {self.params}")
            if not self.test:
            # If no CAD object provided, we're creating a new object
                if self.cad_obj is None:
                    self._buildNewModule()
                else:
                    self._updateModule()

        if template == 'Template 3':
            for key, value in template_3.items():
                self.params[key] = value
                self.l.debug(f"Flow reactor, read form {self.params}")
            if not self.test:
            # If no CAD object provided, we're creating a new object
                if self.cad_obj is None:
                    self._buildNewModule()
                else:
                    self._updateModule()


        if template == 'Template 4':
            for key, value in template_4.items():
                self.params[key] = value
                self.l.debug(f"Flow reactor, read form {self.params}")
            if not self.test:
            # If no CAD object provided, we're creating a new object
                if self.cad_obj is None:
                    self._buildNewModule()
                else:
                    self._updateModule()
            # Close the settings window and free the memory


    def addInput(self, params: dict):

        """The AddIODialog class will call this method"""

        self.l.debug(f"Flow Reactor, adding input: {params}")

        name = params["name"]
        del params["name"]

        # If input not already in dict_inputs, add it to the table
        if name not in self.dict_inputs:
            self._addNewRow(name, params["type_io"])
            self.l.debug(f"module_reactor: addInput {params}")
        else:
            self.l.debug(f"addInput, updating input {name} with {params}")

        self.dict_inputs[name] = params

    def addOutput(self, params: dict):

        """The AddIODialog class will call this method"""

        self.l.debug(f"Flow Reactor, adding output: {params}")

        name = params["name"]
        del params["name"]

        # If input not already in dict_outputs, add it to the table
        if name not in self.dict_outputs:
            self._addNewRow(name, params["type_io"])
            self.l.debug(f"module_reactor: addOutput {params}")
        else:
            self.l.debug(f"addOutput, updating output {name} with {params}")

        self.dict_outputs[name] = params

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

        self.l.debug("Reactor, building inputs")

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

        self.l.debug("Reactor, building outputs")

        for name, out_io in self.dict_outputs.items():

            # Skip default output
            if name == "default":
                continue

            cad_obj.addOutputPercentage(
                name,
                out_io["height_per"],
                out_io["angle"],
                out_io["diameter"],
                out_io["external"],
            )

    def buildModule_Advanced(self):

        """
        Called when user clicks the OK button. Will read the form, build the 3D
        model of the module, and tell the parent to display the module
        """

        # TODO: generate an image of the module, and build the CAD object

        self.readForm_Advanced()

        if not self.test:
            # If no CAD object provided, we're creating a new object
            if self.cad_obj is None:
                self._buildNewModule()
            else:
                self._updateModule()

        # Close the settings window and free the memory
        self.close()

    def buildModule_Basic(self):

        """
        Called when user clicks the OK button. Will read the form, build the 3D
        model of the module, and tell the parent to display the module
        """

        # TODO: generate an image of the module, and build the CAD object

        self.readForm_Basic()

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

        self.l.debug("Flow Reactor, deleteModule")
        self.parent.deleteModule(self.cad_obj)

        # Close the settings window and free the memory
        self.close()

    def _buildNewModule(self) -> bool:

        """
        Internal method called when building the object for the first time
        """

        self.l.debug("Flow Reactor, _buildNewModule")

        try:
            reactor = self._buildCADObject()
        except Exception as e:
            mes = f"Impossible to create flow reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Creation error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        # Try to build I/Os
        try:
            self.buildInputs(reactor)
            self.buildOutputs(reactor)
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

        self.l.debug("Flow Reactor, _updateModule")

        # Try to build a temporary reactor with the new parameters
        # If it fails, exit immediately
        try:
            _ = self._buildCADObject()
        except Exception as e:
            mes = f"Impossible to update flow reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Update error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        # If temporary reactor was built, update cad_object
        self.l.debug("Flow Reactor, buildModule w cad_obj")

        self.cad_obj.npipes = self.params["npipes"]
        self.cad_obj.ninputs = self.params["ninputs"]
        self.cad_obj.width = self.params["width"]
        self.cad_obj.radius = self.params["radius"]
        self.cad_obj.spacing = self.params["spacing"]
        self.cad_obj.volume = self.params["volume"]

        # Try to build I/Os
        try:
            self.buildInputs(self.cad_obj)
            self.buildOutputs(self.cad_obj)
        except Exception as e:
            mes = f"Impossible to create I/Os: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "I/Os error", mes, QtWidgets.QMessageBox.Ok
            )
            return False

        # Try to refresh assembly
        try:
            self.parent.refresh()
        except Exception as e:
            mes = f"Impossible to refresh flow reactor: {e}"
            self.l.error(mes, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Refresh error", mes, QtWidgets.QMessageBox.Ok
            )

        return True

    def _buildCADObject(self) -> rea:

        """
        Use the parameters read from the form to build the CAD object. Does
        nothing else, no GUI task here
        """

        npipes = self.params["npipes"]
        ninputs = self.params["ninputs"]
        width = self.params["width"]
        radius = self.params["radius"]
        spacing = self.params["spacing"]
        volume = self.params["volume"]

        reactor = rea(
            npipes,
            ninputs,
            width,
            radius,
            spacing,
            volume,
        )

        return reactor

    def changeTemplate(self, event):
        changeTemplate = QtWidgets.QMessageBox.question(self,
                                         "Change Template",
                                         "Would you like to change the selected flow reactor parameters? Go to ADVANCED",
                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if changeTemplate == QtWidgets.QMessageBox.Yes:
            pass
        else:
            self.close()


    def buttonClicked(self):
        sender = self.sender()
        if sender == self.template1_button:
            self.setTemplate(template='Template 1')
            #self.changeTemplate(event)
        elif sender == self.template2_button:
            self.setTemplate(template='Template 2')
            #self.changeTemplate(event)
        elif sender == self.template3_button:
            self.setTemplate(template='Template 3')
            #self.changeTemplate(event)
        elif sender == self.template4_button:
            self.setTemplate(template='Template 4')
            #self.changeTemplate(event)
        self.close()

    def basicUpdated(self):

        """ Update basic tab values """

        npipes = 10
        width = 10
        spacing = 6
        inputs = 3
        radius = self.spin_radius.value() # spin_radius_basic
        volume = self.spin_volume.value() # if volume = 10, width = some value

        
        total_volume, flowpath = self.getVolume(npipes, width, radius, spacing, inputs)

        text = "{:.{}f}".format( total_volume/1000, 2 )
        self.vol_label.setText(text +" ml")

        text = "{:.{}f}".format( flowpath/1000, 2 )
        self.flowpath_label.setText(text +" ml")
        print("Radius was updated...")

    def initUI(self):

        """Handles the display"""

        if self.cad_obj is None:
            self.setWindowTitle("Add a flow reactor module")
        else:
            self.setWindowTitle("Modify flow reactor module")

        # Build the basic settings tab
        widget_form_basic = self._buildBasicSettings()

        # Build the advanced settings tab
        widget_form_advanced = self._buildAdvancedSettings()

        # Build the templates tab
        widget_form_template = self._buildTemplateSettings()

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)

        self.tabs = QtWidgets.QTabWidget(self)

        self.tabs.addTab(widget_form_basic, "Basic")
        self.tabs.addTab(widget_form_template, "Templates")
        self.tabs.addTab(widget_form_advanced, "Advanced")


        
        self.del_button = QtWidgets.QPushButton("Delete", self)
        split_butttons = QtWidgets.QHBoxLayout()
        #split_butttons.addWidget(self.ok_button)
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

        """Build the widget for the basic settings"""

        widget_form_basic = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_basic.setLayout(fbox)

        # Spin box to specify radius pipes
        self.spin_radius = QtWidgets.QDoubleSpinBox(self)
        # Set default and bound values
        self.spin_radius.setValue(1)
        self.spin_radius.setMinimum(0.1)
        self.spin_radius.setMaximum(200)
        self.spin_radius.valueChanged.connect(self.basicUpdated)

        # Spin box to specify volume of flow path
        self.spin_volume = QtWidgets.QDoubleSpinBox(self)
        # Set default and bound values
        self.spin_volume.setValue(1)
        self.spin_volume.setMinimum(0.1)
        self.spin_volume.setMaximum(100)
        self.spin_volume.valueChanged.connect(self.basicUpdated)


        # text label for total volume
        self.vol_label = QtWidgets.QLabel("0", self)

        # text label for flowpath volume
        self.flowpath_label = QtWidgets.QLabel("0", self)

        # Add widgets to form layout
        fbox.addRow("Volume (mL) of flow path: ", self.spin_volume)
        fbox.addRow("Radius (mm) of all the pipes: ", self.spin_radius)
        fbox.addRow("Total volume of reactor: ", self.vol_label)
        fbox.addRow("Volume of flow path: ", self.flowpath_label)

        self.ok_button_basic = QtWidgets.QPushButton("OK", self)
        self.ok_button_basic.clicked.connect(self.buildModule_Basic)
        fbox.addRow("", self.ok_button_basic)

        return widget_form_basic

    def _buildAdvancedSettings(self) -> QtWidgets.QWidget:

        """Build the widget for the template settings"""

        widget_form_advanced = QtWidgets.QWidget(self)
        fbox = QtWidgets.QFormLayout()
        widget_form_advanced.setLayout(fbox)

        # Spin box to specify number of horizontal pipes
        self.spin_npipes = QtWidgets.QSpinBox(self)
        # Set default and bound values
        self.spin_npipes.setValue(4)
        self.spin_npipes.setMinimum(1)
        self.spin_npipes.setMaximum(200)

        # Spin box to specify number of inlets
        self.spin_ninputs = QtWidgets.QSpinBox(self)
        # Set default and bound values
        self.spin_ninputs.setValue(2)
        self.spin_ninputs.setMinimum(1)
        self.spin_ninputs.setMaximum(3)

        # Spin box to specify width of horizontal pipes
        self.spin_width = QtWidgets.QDoubleSpinBox(self)
        # Set default and bound values
        self.spin_width.setValue(10)
        self.spin_width.setMinimum(1)
        self.spin_width.setMaximum(200)

        # Spin box to specify radius pipes
        self.spin_radius = QtWidgets.QDoubleSpinBox(self)
        # Set default and bound values
        self.spin_radius.setValue(1)
        self.spin_radius.setMinimum(0.1)
        self.spin_radius.setMaximum(200)

        # Spin box to specify spacing between pipes
        self.spin_spacing = QtWidgets.QDoubleSpinBox(self)
        # Set default and bound values
        self.spin_spacing.setValue(6)
        self.spin_spacing.setMinimum(1)
        self.spin_spacing.setMaximum(200)

        # text label for total volume
        self.vol_label = QtWidgets.QLabel("0", self)

        # text label for flowpath volume
        self.flowpath_label = QtWidgets.QLabel("0", self)

        # Add widgets to form layout
        fbox.addRow("Number horizontal pipes: ", self.spin_npipes)
        fbox.addRow("Number inputs: ", self.spin_ninputs)
        fbox.addRow("Width (mm) h-tal pipes: ", self.spin_width)
        fbox.addRow("Radius (mm) of all the pipes: ", self.spin_radius)
        fbox.addRow("Spacing (mm) between h-tal pipes: ", self.spin_spacing)
        fbox.addRow("Total volume of reactor: ", self.vol_label)
        fbox.addRow("Volume of flow path: ", self.flowpath_label)
        self.ok_button_advanced = QtWidgets.QPushButton("OK", self)
        fbox.addRow("", self.ok_button_advanced)
        self.ok_button_advanced.clicked.connect(self.buildModule_Advanced)

        return widget_form_advanced

    def _buildTemplateSettings(self) -> QtWidgets.QWidget:

        """Build the widget for the template settings"""
        widget_form_template = QtWidgets.QWidget(self)
        fbox = QtWidgets.QVBoxLayout(self)
        widget_form_template.setLayout(fbox)

        self.template1_button = QtWidgets.QPushButton("Inputs: 2, Volume of Flow Path: 0.55 mL", self)
        self.template2_button = QtWidgets.QPushButton("Inputs: 2, Volume of Flow Path: 1.50 mL", self)
        self.template3_button = QtWidgets.QPushButton("Inputs: 3, Volume of Flow Path: 0.55 mL", self)
        self.template4_button = QtWidgets.QPushButton("Inputs: 3, Volume of Flow Path: 1.50 mL", self)

        fbox.addWidget(self.template1_button)
        fbox.addWidget(self.template2_button)
        fbox.addWidget(self.template3_button)
        fbox.addWidget(self.template4_button)
        self.template1_button.clicked.connect(self.buttonClicked)
        self.template2_button.clicked.connect(self.buttonClicked)
        self.template3_button.clicked.connect(self.buttonClicked)
        self.template4_button.clicked.connect(self.buttonClicked)

        #self.show()

        # # Spin box to specify number of horizontal pipes
        # self.spin_npipes = QtWidgets.QSpinBox(self)
        # # Set default and bound values
        # self.spin_npipes.setValue(4)
        # self.spin_npipes.setMinimum(1)
        # self.spin_npipes.setMaximum(200)

        # # Spin box to specify number of inlets
        # self.spin_ninputs = QtWidgets.QSpinBox(self)
        # # Set default and bound values
        # self.spin_ninputs.setValue(2)
        # self.spin_ninputs.setMinimum(1)
        # self.spin_ninputs.setMaximum(3)

        # # Spin box to specify width of horizontal pipes
        # self.spin_width = QtWidgets.QDoubleSpinBox(self)
        # # Set default and bound values
        # self.spin_width.setValue(10)
        # self.spin_width.setMinimum(1)
        # self.spin_width.setMaximum(200)

        # # Spin box to specify radius pipes
        # self.spin_radius = QtWidgets.QDoubleSpinBox(self)
        # # Set default and bound values
        # self.spin_radius.setValue(1)
        # self.spin_radius.setMinimum(0.1)
        # self.spin_radius.setMaximum(200)

        # # Spin box to specify spacing between pipes
        # self.spin_spacing = QtWidgets.QDoubleSpinBox(self)
        # # Set default and bound values
        # self.spin_spacing.setValue(6)
        # self.spin_spacing.setMinimum(1)
        # self.spin_spacing.setMaximum(200)

        # # text label for total volume
        # self.vol_label = QtWidgets.QLabel("0", self)

        # # text label for flowpath volume
        # self.flowpath_label = QtWidgets.QLabel("0", self)

        # # Add widgets to form layout
        # fbox.addRow("Number horizontal pipes: ", self.spin_npipes)
        # fbox.addRow("Number inputs: ", self.spin_ninputs)
        # fbox.addRow("Width (mm) h-tal pipes: ", self.spin_width)
        # fbox.addRow("Radius (mm) of all the pipes: ", self.spin_radius)
        # fbox.addRow("Spacing (mm) between h-tal pipes: ", self.spin_spacing)
        # fbox.addRow("Total volume of reactor: ", self.vol_label)
        # fbox.addRow("Volume of flow path: ", self.flowpath_label)

        return widget_form_template




if __name__ == "__main__":
    print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    app = QtWidgets.QApplication(sys.argv)
    obj = ChemModule()
    sys.exit(app.exec_())
