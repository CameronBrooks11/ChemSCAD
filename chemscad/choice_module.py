#!/usr/bin/python
# coding: utf-8

import os
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from typing import Dict

from chemscad.log import MyLog


class ChoiceModule(QtWidgets.QDialog):

    """
    Create a modal window to display the available modules. The user will
    choose through a combo box. Will open a window for the chosen module
    """

    def __init__(self, parent=None):

        super(ChoiceModule, self).__init__(parent)

        # modal doesnt let the user to interact with main window while this shows
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

        self.dic_modules = self.listModules()
        self.l.info(f"MODS: {self.dic_modules}")

        self.initUI()
        self.defineSlots()

    def defineSlots(self):

        """Establish the slots"""

        # Choice made, display window module
        self.ok_button.clicked.connect(self.openForm)

    def openForm(self):

        """Import the available modules"""

        # Get module's name from combo box
        module_name = self.combo_choice.currentText()
        self.l.debug(f"Module {module_name} chosen")

        module_dir = os.path.join("gui_modules", self.dic_modules[module_name])

        # Add module's directory to the import path
        sys.path.insert(0, module_dir)

        # Import module
        module = __import__(self.dic_modules[module_name])

        # Build the ChemModule class contained in the module
        # Display the module's window
        if self.test:
            chem_module = module.ChemModule(self)
        else:
            chem_module = module.ChemModule(self.parent)

        self.close()

    def listModules(self) -> Dict[str, str]:

        """
        Build the list of modules by getting names from all name.txt files
        in module_* folders
        """

        if not self.test:
            return self.parent.listModules()
        else:
            return dict()

    def initUI(self):

        """Handles the display"""

        self.setWindowTitle("Add a new module")
        #self.setMinimumSize(200, 50)

        self.combo_choice = QtWidgets.QComboBox(self)

        # Add module name to list in combo box
        self.combo_choice.addItems(self.dic_modules)
        # I hardcode it to display the reactor by default, because it is the most used
        self.combo_choice.setCurrentIndex(list(self.dic_modules).index('Reactor'))

        self.ok_button = QtWidgets.QPushButton("OK", self)

        # ----------------- ASSEMBLING ----------------------------------------

        self.vbox_global = QtWidgets.QVBoxLayout(self)
        self.vbox_global.addWidget(self.combo_choice)
        self.vbox_global.addWidget(self.ok_button)

        self.setLayout(self.vbox_global)
        self.setMinimumSize(self.sizeHint())
        self.show()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    obj = ChoiceModule()
    sys.exit(app.exec_())
