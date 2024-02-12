#!/usr/bin/python
# coding: utf-8

###############################################################################
#
# This code was originally written by JP Francoia for the Cronin Group.
# I (JMP) have been given the task of continuing it.
# I plan to make minimal changes, but I have added a lot of comments to help me
# Contact me at juanma@chem.gla.ac.uk
#
###############################################################################

import sys
from PyQt5 import QtGui, QtSql, QtCore, QtWidgets
import logging
import datetime
import os
import time
import shutil
import webbrowser
from typing import Dict, List

# Personal modules
from chemscad.log import MyLog
import chemscad.functions as functions
import chemscad.app_constants as app_constants
from chemscad.stl_viewer import STLViewer
from chemscad.little_thread import LittleThread

# Dialog boxes
from chemscad.choice_module import ChoiceModule
from chemscad.align_tops import AlignTops
from chemscad.align_filters import AlignFilters
from chemscad.settings import Settings
from chemscad.filtersettings import FilterSettings
from chemscad.help_info import help_info

# from composite import Composite
from chemscad.dashboard import Dashboard

# CAD modules
from ccad.object import ObjectCAD
from ccad.connector import ConnectorCAD
from ccad import Assembly
from ccad import ReactorCAD


# # DEBUG: do not show deprecation warningmport warningss
# import warnings
# warnings.filterwarnings("ignore", category=DeprecationWarning)

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):

        super(MyWindow, self).__init__()

        # Get the DATA_PATH and the resource_dir pathes
        self.resource_dir, self.DATA_PATH = functions.getRightDirs()

        # create a render dir for the user
        self.createUserDirs()

        # Create the logger w/ the appropriate size
        self.l = MyLog("activity.log")

        # Set the logging level
        self.l.setLevel(logging.DEBUG)

        # Log the resource and data directories and the library path
        # fn and fs are chemcad parameters related to the quality of the render
        self.l.info(f"resource_dir: {self.resource_dir}")
        self.l.info(f"DATA_PATH: {self.DATA_PATH}")
        self.l.info(f"fn: {app_constants.fn}")
        self.l.info(f"fs: {app_constants.fs}")
        self.l.info(QtWidgets.QApplication.libraryPaths())
        self.l.info("Starting the program")

        # Clean the renders dir from any file
        # He does this again 10 lines ahead. I dont see why it needs to be repeated twice. Commenting for now
        # functions.cleanRendersDir(self.l)

        # Start a timer
        start_time = datetime.datetime.now()
        diff_time = start_time

        # Clean the renders dir, in case the software crashed before and didn't do it
        functions.cleanRendersDir(self.l)

        # Object to store options and preferences
        self.options = QtCore.QSettings("options.ini", QtCore.QSettings.IniFormat)

        # Prepare stack for undo
        self.undoStack = QtWidgets.QUndoStack()

        # Define in self different QT actions such as close program, render,...
        self.defineActions()

        # Create the GUI
        self.initUI()
        self.l.debug(f"initUI took {datetime.datetime.now() - diff_time}")

        diff_time = datetime.datetime.now()

        # Define the slots
        QtWidgets.qApp.processEvents()
        self.defineSlots()
        self.l.debug(f"defineSlots took {datetime.datetime.now() - diff_time}")
        diff_time = datetime.datetime.now()

        # Restore the settings
        QtWidgets.qApp.processEvents()
        self.restoreSettings()
        self.l.debug(f"restoreSettings took {datetime.datetime.now() - diff_time}")
        diff_time = datetime.datetime.now()

        QtWidgets.qApp.processEvents()

        self.l.info(f"Boot took {datetime.datetime.now() - start_time}")

        # Dict to store available modules
        self.dic_available_modules = self.listModules()

        # Create an assembly object to store the chem_modules
        self.ass = Assembly(renders_dir=self.renders_dir, logger=self.l)


        # Bool to check if assembly is rendered (unmodified + rendered)
        # Can't export STL if False
        self.rendered = False

        self.show()

    def createUserDirs(self):

        """Create the necessary user's dirs"""

        # Rendering dir
        self.renders_dir = os.path.join(self.DATA_PATH, "renders")
        os.makedirs(self.renders_dir, exist_ok=True)

    def defineActions(self):

        """Define software actions"""

        # Action to create new project (clear canvas) #HPD - 22/11/19
        self.newProjectAction = QtWidgets.QAction("&New project", self)
        self.newProjectAction.setShortcut("Ctrl+N")
        self.newProjectAction.setStatusTip("Start new project")
        self.newProjectAction.triggered.connect(self.newProject)

        # Action to quit
        self.exitAction = QtWidgets.QAction("&Quit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.setStatusTip("Quit")
        self.exitAction.triggered.connect(self.close) #HPD: 19/02/20 - fixed crash when quitting

        # Action to render assembly at high def, for production
        self.renderProdAction = QtWidgets.QAction("&Render for production", self)
        self.renderProdAction.setShortcut("Ctrl+R")
        self.renderProdAction.setStatusTip(
            "Render assembly at high definition, for production"
        )
        self.renderProdAction.triggered.connect(self.renderProd)

        # Action to export assembly as STL
        # self.exportSTLAction = QtWidgets.QAction("&Export as STL", self)
        # self.exportSTLAction.setShortcut("Ctrl+Shift+S")
        # self.exportSTLAction.setStatusTip("Export assembly as STL")
        # self.exportSTLAction.triggered.connect(self.exportSTL)

        # Action to take a screenshot of the stl viewer
        self.screenshotAction = QtWidgets.QAction("Export as image", self)
        self.screenshotAction.setStatusTip("Export an image of the current view")
        self.screenshotAction.triggered.connect(self.screenshot)

        # Action to save current project
        self.saveProjectAction = QtWidgets.QAction("&Save project", self)
        self.saveProjectAction.setShortcut("Ctrl+S")
        self.saveProjectAction.setStatusTip("Save current project")
        self.saveProjectAction.triggered.connect(self.saveProject)

        # Action to import a project (.ccad)
        self.openProjectAction = QtWidgets.QAction("&Open project", self)
        self.openProjectAction.setShortcut("Ctrl+O")
        self.openProjectAction.setStatusTip("Open a CCAD project")
        self.openProjectAction.triggered.connect(self.openProject)

        # Action to set the preferences for assembly angles
        self.preferencesAction = QtWidgets.QAction("&Assembly angle settings", self)
        self.preferencesAction.setStatusTip("Open the ChemSCAD's preferences for assembly angle")
        self.preferencesAction.triggered.connect(lambda: Settings(self))

        # Action to undo
        self.undoAction = self.undoStack.createUndoAction(self, "&Undo")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.setStatusTip("Undo the last action")


        # Action to redo
        self.redoAction = self.undoStack.createRedoAction(self, "&Redo")
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.setStatusTip("Redo the last action")

        # Action to view the filter settings table for FR and DFR modules
        self.filterSettingsAction = QtWidgets.QAction("&Filter settings", self)
        self.filterSettingsAction.setStatusTip("Open the filter settings table")
        self.filterSettingsAction.triggered.connect(lambda: FilterSettings(self))

        # Action to open Git database
        self.openDatabaseAction = QtWidgets.QAction("&Go to database", self)
        self.openDatabaseAction.setStatusTip("Open the Git database")
        self.openDatabaseAction.setShortcut("Ctrl+D")
        self.openDatabaseAction.triggered.connect(self.openDatabaseURL)

        # Action to view the 'About ChemSCAD' window
        #self.aboutAction = QtWidgets.QAction("&About ChemSCAD", self)
        #self.aboutAction.setStatusTip("See information about ChemSCAD")
        #self.aboutAction.triggered.connect(lambda: help_info(self))

        # Action to open help documentation - link to ChemSCAD Git repository
        self.helpAction = QtWidgets.QAction("&Go to the ChemSCAD documentation", self)
        self.helpAction.setStatusTip("Open the ChemSCAD documentation")
        self.helpAction.setShortcut("Ctrl+H")
        self.helpAction.triggered.connect(self.openDocumentationURL)

        # Action separator
        self.separatorAction = QtWidgets.QAction(self)
        self.separatorAction.setSeparator(True)

    def openDatabaseURL(self): # function to open Git database, can also use lambda fucntion with webbrowser.open('url')
        url = QtCore.QUrl('https://gitlab.com/croningroup/reactionware/reactionware_files/-/tree/master') # link to database goes here
        if not QtGui.QDesktopServices.openUrl(url):
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url')

    def openDocumentationURL(self): # function to open ChemSCAD Git repository (documentation in future), can also use lambda fucntion with webbrowser.open('url')
        url = QtCore.QUrl('https://gitlab.com/croningroup/reactionware/chemscad') # link to ChemSCAD repository (documentation)
        if not QtGui.QDesktopServices.openUrl(url):
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url')

    def closeEvent(self, event):

        """
        Method to perform actions before exiting.
        Allows to save the prefs in a file
        """

        # Clean the renders dir from any file
        functions.cleanRendersDir(self.l)

        # Record the window state and appearance
        self.options.beginGroup("Window")

        # Reinitializing the keys
        self.options.remove("")

        self.l.debug("Saving windows state")
        self.options.setValue("window_geometry", self.saveGeometry())
        self.options.setValue("window_state", self.saveState())

        # # Save the state of the window's splitter
        # self.options.setValue("split_exp", self.split_exp.saveState())

        self.options.endGroup()

        # Be sure ini files finished their tasks
        self.options.sync()

        close = QtWidgets.QMessageBox.question(self,
                                         "QUIT",
                                         "Are you sure want to close this project?",
                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if close == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()




    def restoreSettings(self):

        """Restore the prefs of the window"""

        # If windows settings are available, import and use them
        if "Window" in self.options.childGroups():
            self.restoreGeometry(self.options.value("Window/window_geometry"))
            self.restoreState(self.options.value("Window/window_state"))
            # self.split_ana.restoreState(self.options.value("Window/split_ana"))

            # self.split_display_ana.restoreState(
            # self.options.value("Window/split_display_ana"))

    def defineSlots(self):

        """Connect the slots"""

        # self.splitter2.splitterMoved.connect(self.updateCellSize)
        # new_size = self.splitter2.sizes()[0]

        # Add module button connected to dialog box for module choice
        self.button_add_module.clicked.connect(lambda: ChoiceModule(self))
        self.button_add_module.setToolTip('Add a new module')
        # # Button to display main view (preview)
        # self.button_main_view.clicked.connect(lambda: self.displayView("preview.png"))

        # # Display left view (preview)
        # self.button_left_view.clicked.connect(lambda: self.displayView("preview_left.png"))

        # # Display right view (preview)
        # self.button_right_view.clicked.connect(lambda: self.displayView("preview_right.png"))

        # # Display top view (preview)
        # self.button_top_view.clicked.connect(lambda: self.displayView("preview_top.png"))

        # # Display front view (preview)
        # self.button_front_view.clicked.connect(lambda: self.displayView("preview_front.png"))

        # # Display rear view (preview)
        # self.button_rear_view.clicked.connect(lambda: self.displayView("preview_rear.png"))

        # # Display bottom view (preview)
        # self.button_bottom_view.clicked.connect(lambda: self.displayView("preview_bottom.png"))

        # # Render STL files (fs=75 for HD)
        self.button_render.clicked.connect(self.renderProd)
        self.button_render.setToolTip('Render STL')

        # Render Ultra High Res STL files for publication images/figures (fs=200 for UHD)
        self.button_renderUHD.clicked.connect(self.renderProd_UHD)
        self.button_renderUHD.setToolTip('Render UHD STL')

        # Dialog box to select reactors tops to align
        self.button_align_tops.clicked.connect(lambda: AlignTops(self))
        self.button_align_tops.setToolTip('Align reactor tops')

        # Dialog box to select reactors with filters to align
        self.button_align_filters.clicked.connect(lambda: AlignFilters(self))
        self.button_align_filters.setToolTip('Align reactors with filters')

        # Toggle translucent state for mesh in stl viewer
        self.button_translucent.clicked.connect(self.toggleTranslucent)
        self.button_translucent.setToolTip('Toggle X-Ray view')

        # Set the perspective state in STL viewer
        self.button_perspective.clicked.connect(self.togglePerspective)
        self.button_perspective.setToolTip('Toggle perspective view')

        # Save the current project using button
        self.button_save.clicked.connect(self.saveProject)
        self.button_save.setToolTip('Save the current project')

        # Button to toggle the linear assembly state
        self.button_linear.clicked.connect(self.toggleLinearAssembly)
        self.button_linear.setToolTip('Toggle linear assembly')

        # # Undo action
        self.button_undo.clicked.connect(self.undoAction.trigger) #HPD: undo button now working - 19/02/20
        self.button_undo.setToolTip('Undo action')

        # # Redo action
        self.button_redo.clicked.connect(self.redoAction.trigger) #HPD: redo button now working - 19/02/20
        self.button_redo.setToolTip('Redo action')

    def listModules(self) -> Dict[str, str]:

        """
        Build the list of modules by getting names from all name.txt files
        in module_* folders
        """

        dic_modules: Dict[str, str] = dict()

        # In modules/ look for all directories starting with module_
        for entry in os.scandir(os.path.join(self.resource_dir, "gui_modules")):

            if (
                entry.name.startswith("module_") or entry.name.startswith("connector_")
            ) and entry.is_dir():

                # Get the name of the module
                with open(
                    os.path.join(
                        self.resource_dir, "gui_modules", entry.name, "name.txt"
                    ),
                    "r",
                ) as f:
                    name = f.read().strip()

                path_dir_module = os.path.join(
                    self.resource_dir, "gui_modules", entry.name
                )

                # Add the path of the module to PATH
                # Necessary to open a project if each module was initialized
                # by opening the dialog box when creating
                sys.path.append(path_dir_module)

                dic_modules[name] = entry.name

        return dic_modules

    def buildModule(self, cad_object: ObjectCAD):

        """
        ChemModule objects will call this method from their own buildModule
        method. This method handles the display of the new ChemModule, not the
        creation/calculations of the module
        """

        # Now we are using the QtUndo pattern
        command = CommandBuild(cad_object, self.ass, self)
        self.undoStack.push(command)

        # Add the CAD object to assembly
        # Assembly will refresh itself
        # self.ass.appendModule(cad_object)
        # self.refresh()

    def deleteModule(self, cad_object: ObjectCAD):

        """
        ChemModule objects will call this method when deleted.
        This method will delete the module from the assembly.
        """

        # Now we are using the QtUndo pattern
        command = CommandDelete(cad_object, self.ass, self)
        self.undoStack.push(command)
        # # Delete the CAD object from assembly
        # # Assembly will refresh itself
        # self.ass.deleteModule(cad_object)
        # self.refresh()

        # # remove the mesh from the stl_viewer
        # self.stl_viewer.deleteMesh(cad_object.internal_id)
        # self.refresh()

    def openModuleDialog(self, cad_object: ObjectCAD):

        """Open module's dialog box to update parameters"""

        # Import module
        module = __import__(self.dic_available_modules[cad_object.module_type])

        # Build the ChemModule class contained in the module
        # Display the module's window
        module.ChemModule(self, cad_obj=cad_object)

    def refresh(self):

        """
        Called by module_*. Refresh the assembly and the preview when a
        module changes (user entered new parameters)
        """

        # Something changed in the assembly, switching rendered state to False.
        # Can't export stl
        self.rendered = False

        # Refresh assembly
        self.ass.refresh()

        # Refresh dashboard
        self.dashboard.refresh()

        self.renderSTLs()

    def renderSTLs(self):

        """
        Will trigger the rendering of the STLs, for each module.
        These renderings will be started separately in Qt threads
        """

        # TEST
        # return

        self.l.debug("Rendering model")

        # Generathe the scad files (one for each module. generatePreviews
        # generates only one for the entire assembly)
        self.ass.prepareRenderSTLs()

        # Dict to store workers
        # key: file name (necessary to trigger display in STL viewer)
        # value: worker
        self.dict_workers: Dict[str, LittleThread] = dict()

        # Start a timer
        self.render_start_time = datetime.datetime.now()

        # Get the name of the files to be rendered
        list_stl_to_render: List[str] = self.getSTLsToRender()

        # Progress bar to display the progress of the rendering
        self.prog_render = QtWidgets.QProgressDialog(self)
        self.prog_render.setWindowTitle("Rendering modules")
        self.prog_render.setModal(True)
        self.prog_render.setMinimum(0)
        self.prog_render.setMaximum(len(list_stl_to_render))
        self.prog_render.setValue(0)
        self.prog_render.setLabelText(f"0/{len(list_stl_to_render)} modules rendered")
        self.prog_render.show()

        # For each of the scad file, start a thread, and put the thread in the
        # worker dict
        for name in list_stl_to_render:
            worker = LittleThread(self.ass.renderSTL, name)
            self.dict_workers[name] = worker
            worker.start()

        self.checkRenderingStage()

    def renderProd(self):

        """
        Method to render assembly at high definition, for production. Wrappe
        for renderSTLs. Changes assembly.fn before and after rendering - fs = 75
        """

        self.l.debug("Start rendering for production")

        # Tell the assembly to render in HD
        self.ass.switchToHD()

        # Render all modules in HD
        self.renderSTLs()

        # Tell the assembly to render low definition
        self.ass.switchToLD()

        self.l.debug("End endering for production")

    def renderProd_UHD(self, event):

        """
        Method to render assembly at ULTRA high definition, for publication. Wrappe
        for renderSTLs. Changes assembly.fn before and after rendering - fs = 200
        """

        self.l.debug("Start rendering for publicaton")
        rendering_warning = QtWidgets.QMessageBox.question(self,
                                         "WARNING",
                                         "Are you sure want to render the model in UHD? Rendering times can take 10x longer than HD!",
                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if rendering_warning == QtWidgets.QMessageBox.Yes:
            # Tell the assembly to render in UHD
            self.ass.switchToUHD()

            # Render all modules in UHD
            self.renderSTLs()

            # Tell the assembly to render low definition
            self.ass.switchToLD()

            self.l.debug("End rendering for publication")


    def getSTLsToRender(self) -> List[str]:

        """getSTLsToRender

        Returns:
            List[str]: a list of file names to be rendered. Not path, just the name
        """

        self.l.debug("Entering getSTLsToRender")

        list_stl_to_render: List[str] = list()

        for entry in os.scandir(self.renders_dir):

            # Only render "obj_*_to_render.scad" files
            if "_to_render" in entry.name:
                list_stl_to_render.append(entry.name)
                self.l.debug(f"Adding {entry.name} to list of STLs to render")

        return list_stl_to_render

    def checkRenderingStage(self):

        """
        Method called each time a rendering thread finished. Update the
        rendering progress bar, and triggers actions when all threads
        are finished
        """

        # List to store bools. When len(list) = len(dict_workers), all workers
        # are finished. Workers' state can't be checked on the fly, otherwise
        # some instructions might not be executed
        list_bool_finished: List[bool] = list()

        # Freeze the nbr of modules
        nbr_workers = len(self.dict_workers)

        while len(list_bool_finished) != nbr_workers:

            # Update app while workers running
            QtWidgets.qApp.processEvents()

            # Check if workers are still running
            for file_name, worker in list(self.dict_workers.items()):

                if worker.isFinished():

                    list_bool_finished.append(True)
                    del self.dict_workers[file_name]

                    # Load the newly rendered STL file in the STL viewer
                    self.viewSTL(file_name.replace("_to_render", ""))

                    # Update the progress bar
                    nbr_stls_rendered = self.prog_render.value() + 1
                    self.prog_render.setValue(nbr_stls_rendered)
                    self.prog_render.setLabelText(
                        f"{nbr_stls_rendered}/{nbr_workers} modules rendered"
                    )

            time.sleep(0.2)

        total_time = datetime.datetime.now() - self.render_start_time
        self.l.debug(f"All renderings & displays finished in {total_time}")

        # Switching the rendering state to True. Can now export stl
        self.rendered = True

        # Delete the progress bar
        self.prog_render.reset()

        del self.dict_workers
        del self.render_start_time

        # Refresh the STL check boxes (delete and rebuild them) in the STL viewer
        # control center
        self.refreshSTLCheckBoxes()

    def refreshSTLCheckBoxes(self):

        """
        Create a checkbox for each module in assembly, connect it to a method to handle
        state toggling, and add it to the control center (in a dedicated scroll area)
        """

        # Clear all the checkboxes
        self.clearLayout(self.vbox_control_center)

        # Get all the modules in the assembly
        modules_names = list(self.ass.reactors_names.keys()) + list(
            self.ass.connectors_names.keys()
        )

        # Create a checkbox for each module
        for module_name in modules_names:
            checkbox = QtWidgets.QCheckBox(module_name, self.scroll_control_center)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.checkBoxSTLToggled)
            self.vbox_control_center.addWidget(checkbox)

        # Necessary here, otherwise checkboxes don't appear
        self.scroll_control_center.setWidget(self.scrolling_control_center)

    def checkBoxSTLToggled(self):

        """
        A checkbox for each module is present in the control center.
        If the checkbox is checked, the module is displayed in the STL viewer.
        If not, the module is not displayed.

        In the future, a module not displayed will not be exported when user exports
        the final STL
        """

        # Get the module short name from the checkbox that triggered the signal
        module_id = self.ass.getModuleIDFromName(self.sender().text())
        self.stl_viewer.toggleVisibility(module_id)

    def screenshot(self):

        """Ask the STL viewere to take a screenshot"""

        # Let user choose destination file
        dst = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export image", "", "Images (*.png)"
        )

        if not dst[0]:
            self.l.debug("No destination file, exiting func screenshot")
            return

        # Copy merged STL into destination file
        self.stl_viewer.screenshot(dst[0])

    def viewSTL(self, file_name: str):

        """
        This method is called by renderSTLs, and will update the stl viewer
        widget. file_name is the name of the file for the module to be
        loaded in the viewer
        """

        self.l.debug(f"Entering viewSTL with {file_name}")

        self.stl_viewer.viewMesh(file_name)

    def toggleTranslucent(self):

        """Toggle the transparency state of the STL viewer"""

        self.stl_viewer.toggleTranslucent()

        # Change button state
        if self.stl_viewer.translucent:
            self.button_translucent.setChecked(True)
        else:
            self.button_translucent.setChecked(False)

    def togglePerspective(self):

        """
        Toggle the perspective button. Set it to checked or unchecked. Toggle
        the perspective in the STL viewer
        """

        self.stl_viewer.togglePerspective()

        # Change button state
        if self.stl_viewer.perspective:
            self.button_perspective.setChecked(True)
        else:
            self.button_perspective.setChecked(False)

    def toggleLinearAssembly(self):

        """
        Toggle the values of x turn and y turn to equal 1 for a linear assembly. Set it to checked or unchecked.
        """
        self.ass.toggleLinearAssembly()

        # Change button state
        if self.ass.linear:
            self.button_linear.setChecked(True)
            self.ass.turn_x: int = 1
            self.ass.turn_y: int = 1
            self.refresh()
            print('Changed x turn and y turn to 1 i.e. linear')
        else:
            self.button_linear.setChecked(False)
            #self.ass.turn_x: int = 2
            #self.ass.turn_y: int = 2
            Settings().restoreParams()
            self.refresh()
            print('x and y turn values restore to default i.e. = 2')

    def exportSTL(self, stl_filename):

        """Slot called to export assembly as a STL"""

        self.l.debug("Trying to export assembly as STL")

        mes = "Before exporting the assembly as a STL, we first must render it"

        # Check the assembly is rendered
        if not self.rendered:
            self.l.debug("Assembly not rendered, display dailogbox and exit")
            QtWidgets.QMessageBox.warning(self, "Export STL", mes)
            return

        # First we will find the modules where visibility was
        # set to OFF from the checkbox. These won't be rendered
        meshes_ignore = []
        for key, value in self.stl_viewer.meshes.items():
            # if visibility was OFF, then alpha is 0
            # otherwise alpha would be 1
            if value.filter.alpha == 0:
                meshes_ignore.append(key)

        # Merge all the stl files of the modules
        self.ass.mergeSTLs(meshes_ignore)

        # Let user choose destination file
        #dst = QtWidgets.QFileDialog.getSaveFileName(
        #    self, "Export STL", "", "STL files (*.stl *.STL)"
        #)

        #if not dst[0]:
        #    self.l.debug("No destination file, exiting exportSTL")
        #    return

        src = os.path.join(self.renders_dir, "final.stl")

        # Copy merged STL into destination file
        shutil.copyfile(src, stl_filename)

        self.l.debug("Assembly exported as STL")
        self.l.debug(f"Saving project to {stl_filename}")

    def saveProject(self):

        """Save the project (current assembly) in a .ccad file"""

        self.l.debug("Saving project")

        # Let user choose saving file
        dst = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save project", "", "CCAD files (*.ccad *.CCAD)"
        )

        if not dst[0]:
            self.l.debug("No destination file, exiting saveProject")
            return

        self.l.debug(f"Saving project to {dst}")

        # Save main attributes of assembly
        try:
            self.ass.saveProject(dst[0])
            stl_filename = "{}.stl".format(os.path.splitext(dst[0])[0])
            self.exportSTL(stl_filename)
        except Exception as e:
            self.l.error(f"Couldn't save project: {e}", exc_info=True)

        saved = QtWidgets.QMessageBox.information(self,
                                         "SAVED!",
                                         "CCAD and STL files have been saved successfully in the chosen directory",
                                         QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if saved == QtWidgets.QMessageBox.Ok:
            return
        else:
            return



    def openProject(self):

        """Open a project, a pickled assembly stored as a .ccad file"""

        self.l.debug("Opening project")

        fnm = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select a project", "", "CCAD files (*.ccad *.CCAD)"
        )

        if not fnm[0]:
            self.l.debug("openProject, no file selected, exiting")

        self.l.debug(f"openProject, trying to open {fnm[0]}")

        self.ass.openProject(fnm[0])

        self.l.debug(f"openProject, {fnm[0]} opened")

        self.refresh()

    def newProject(self):# creates new ChemCAD window - HPD - 25/11/19
        self.w = NewWindow()
        self.w.show()
        #self.hide()

    def clearLayout(self, layout: QtWidgets.QLayout):

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

        """Build the interface"""

        self.setWindowTitle("ChemSCAD")

        # enable the status bar
        self.statusBar().showMessage('Ready')

        # font = QtGui.QFont()
        # font.setStyleHint(QtGui.QFont.System)
        # font.setPointSize(self.styles.FONT_SIZE)
        # font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        # QtWidgets.qApp.setFont(font)

        # self.l.debug('Font: {}'.format(font.family()))
        # self.l.debug('Font size: {}pt'.format(self.styles.FONT_SIZE))

        # Empty widget acting like a spacer
        # empty_widget = QtWidgets.QWidget()
        # empty_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        # QtWidgets.QSizePolicy.Preferred)

        # ------------------------- DASHBOARD ---------------------------

        # Add the custom widget Dashboard
        self.dashboard = Dashboard(self)

        # ------------------------- PREVIEW AREA ------------------------------

        # https://stackoverflow.com/questions/45964913/how-to-embed-vispy-canvas-in-pyqt5-frame
        # Create the STL viewer widget, with dimensions and watch folder
        # TODO: adapt dimensions depending on window's size
        self.stl_viewer = STLViewer((800, 500), self.renders_dir, self.l)

        # ------------------------- CONTROL CENTER ----------------------------

        # Will create attribute self.scroll_control_center
        self.buildControlCenter()

        # ------------------------- ASSEMBLING THE AREAS ----------------------

        self.split_right = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.split_right.addWidget(self.stl_viewer.native)
        self.split_right.addWidget(self.scroll_control_center)

        self.split_main = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.split_main.addWidget(self.dashboard)
        self.split_main.addWidget(self.split_right)

        self.setCentralWidget(self.split_main)

        self.buildMenuBar()
        self.buildToolBar()

    def buildControlCenter(self):

        """
        Create the scroll area for the checkboxes triggering the display of each module
        """

        # Create the scroll area for the checkboxes triggering the display of
        # each module
        self.scroll_control_center = QtWidgets.QScrollArea()
        self.scroll_control_center.setStyleSheet("border: none;")
        self.scroll_control_center.setWidgetResizable(True)

        # Create a vbox layout to arrange the checkboxes vertically
        self.vbox_control_center = QtWidgets.QVBoxLayout()
        self.vbox_control_center.setAlignment(QtCore.Qt.AlignTop)

        # Assign an intermediate widget to the scroll are, and give it the vbox.
        # It doesn't make any sense to me but that's how items works
        self.scrolling_control_center = QtWidgets.QWidget()
        self.scrolling_control_center.setLayout(self.vbox_control_center)

    def buildMenuBar(self):

        """Build the Menu bar. Called by initUI"""

        self.menubar = self.menuBar()

        # Building files menu
        self.fileMenu = self.menubar.addMenu("&Files")
        # self.fileMenu.addAction(self.settingsAction)
        self.fileMenu.addAction(self.newProjectAction)
        self.fileMenu.addAction(self.openProjectAction)
        self.fileMenu.addAction(self.saveProjectAction)
        #self.fileMenu.addAction(self.exportSTLAction)
        self.fileMenu.addAction(self.renderProdAction)
        self.fileMenu.addAction(self.screenshotAction)
        self.fileMenu.addAction(self.preferencesAction)
        self.fileMenu.addAction(self.filterSettingsAction)
        self.fileMenu.addAction(self.openDatabaseAction)
        self.fileMenu.addAction(self.exitAction)

        # Building tools menu
        # self.toolMenu = self.menubar.addMenu("&Tools")
        # self.toolMenu.addAction(self.parseAction)

        # self.viewMenu = self.menubar.addMenu("&View")
        # self.sortMenu = self.viewMenu.addMenu("Sorting")
        # self.sortMenu.addAction(self.sortingPercentageAction)

        self.editMenu = self.menubar.addMenu("&Edit")
        self.editMenu.addAction(self.undoAction)
        self.editMenu.addAction(self.redoAction)

        self.helpMenu = self.menubar.addMenu("&Help")
        #self.helpMenu.addAction(self.aboutAction)
        self.helpMenu.addAction(self.helpAction)

    def buildToolBar(self):

        """Build the Tool bar. Called by initUI"""

        # ------------------------- TOOLBAR  ----------------------------------

        # Add a toolbar and name it to identiy it
        # Then add the widgets
        self.toolbar = self.addToolBar("toolbar")
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setMovable(False)

        # "Add module" button, with an icon
        plus_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "plus.png"))
        self.button_add_module = QtWidgets.QPushButton(self)
        self.button_add_module.setIcon(plus_icon)
        self.button_add_module.setStatusTip("Add module")
        self.toolbar.addWidget(self.button_add_module)

        # "Align tops" button, with an icon
        align_tops_icon = QtGui.QIcon(
            os.path.join(self.resource_dir, "images", "align_tops.png")
        )
        self.button_align_tops = QtWidgets.QPushButton(self)
        self.button_align_tops.setIcon(align_tops_icon)
        self.button_align_tops.setStatusTip("Align tops")
        self.toolbar.addWidget(self.button_align_tops)

        # "Align filter" button, with an icon
        align_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "align.png"))
        self.button_align_filters = QtWidgets.QPushButton(self)
        self.button_align_filters.setIcon(align_icon)
        self.button_align_filters.setStatusTip("Align filter")
        self.toolbar.addWidget(self.button_align_filters)

        # Button render
        render_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "render.png"))
        self.button_render = QtWidgets.QPushButton("Render model")
        self.button_render = QtWidgets.QPushButton(self)
        self.button_render.setIcon(render_icon)
        self.button_render.setStatusTip("Render model")
        self.toolbar.addWidget(self.button_render)

        # Button for UHD render
        UHD_render_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "UHD-render.png"))
        self.button_renderUHD = QtWidgets.QPushButton("Render UHD model")
        self.button_renderUHD = QtWidgets.QPushButton(self)
        self.button_renderUHD.setIcon(UHD_render_icon)
        self.button_renderUHD.setStatusTip("Render UHD model")
        self.toolbar.addWidget(self.button_renderUHD)

        # Button undo
        undo_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "undo.png"))
        self.button_undo = QtWidgets.QPushButton("Undo action")
        self.button_undo = QtWidgets.QPushButton(self)
        self.button_undo.setIcon(undo_icon)
        self.button_undo.setStatusTip("Undo action")
        self.toolbar.addWidget(self.button_undo)


        # Button redo
        redo_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "redo.png"))
        self.button_redo = QtWidgets.QPushButton("Redo action")
        self.button_redo = QtWidgets.QPushButton(self)
        self.button_redo.setIcon(redo_icon)
        self.button_redo.setStatusTip("Redo action")
        self.toolbar.addWidget(self.button_redo)


        # Button translucent
        self.button_translucent = QtWidgets.QPushButton("X-ray")
        self.button_translucent.setCheckable(True)
        self.button_translucent.setStatusTip("X-ray render")
        self.toolbar.addWidget(self.button_translucent)

        # Button perspective
        self.button_perspective = QtWidgets.QPushButton("Perspective")
        self.button_perspective.setCheckable(True)
        self.button_perspective.setStatusTip("Reset prespective")
        self.toolbar.addWidget(self.button_perspective)

        # Button Save
        save_icon = QtGui.QIcon(os.path.join(self.resource_dir, "images", "save-icon.png"))
        self.button_save = QtWidgets.QPushButton("Save project")
        self.button_save = QtWidgets.QPushButton(self)
        self.button_save.setIcon(save_icon)
        self.button_save.setStatusTip("Save project")
        self.toolbar.addWidget(self.button_save)

        # Button linear
        self.button_linear = QtWidgets.QPushButton("Linear")
        self.button_linear.setCheckable(True)
        self.button_linear.setStatusTip("Linear assembly")
        self.toolbar.addWidget(self.button_linear)

class CommandBuild(QtWidgets.QUndoCommand):
    """
    In order to perform undo and redo from build commands
    """

    def __init__(self, cad: ObjectCAD, ass: Assembly, parent: QtWidgets.QMainWindow):

        super(CommandBuild, self).__init__()
        self.cad_object = cad
        self.ass = ass
        self.parent = parent

        # # if the object is connector we need to save IOs
        # if isinstance(self.cad_object, ConnectorCAD):
        #     self.in_io = self.cad_object.in_io
        #     self.out_io = self.cad_object.out_io

    def redo(self):
        # if the object is a connector
        # we need to refresh ios
        # if isinstance(self.cad_object, ConnectorCAD):
        #     self.cad_object.reconnectIOs(self.in_io, self.out_io)

        self.ass.appendModule(self.cad_object)
        self.parent.refresh()

    def undo(self):
        # delete module from assembly
        self.ass.deleteModule(self.cad_object)
        self.parent.refresh()
        # remove the mesh from the stl_viewer
        self.parent.stl_viewer.deleteMesh(self.cad_object.internal_id)
        self.parent.refresh()

class CommandDelete(QtWidgets.QUndoCommand):
    """
    In order to perform undo and redo from delete commands
    """

    def __init__(self, cad: ObjectCAD, ass: Assembly, parent: QtWidgets.QMainWindow):

        super(CommandDelete, self).__init__()
        self.cad_object = cad
        self.ass = ass
        self.parent = parent

        # # if the object is connector we need to save IOs
        if isinstance(self.cad_object, ConnectorCAD):
            self.in_io = self.cad_object.in_io
            self.out_io = self.cad_object.out_io

    def redo(self):
        # delete module from assembly
        self.ass.deleteModule(self.cad_object)
        self.parent.refresh()
        # remove the mesh from the stl_viewer
        self.parent.stl_viewer.deleteMesh(self.cad_object.internal_id)
        self.parent.refresh()

    def undo(self):
        # if the object is a connector
        # we need to refresh IOs
        if isinstance(self.cad_object, ConnectorCAD):
            self.cad_object.reconnectIOs(self.in_io, self.out_io)

        # Now we add back the reactor or connector
        self.ass.appendModule(self.cad_object)

        # if is a reactor, we need to add the connectors it had (if any)
        if isinstance(self.cad_object, ReactorCAD):
            for _, inp in self.cad_object.inputs.items():
                con_module = inp.connectedTo
                if con_module:
                    con_module.reconnectIOs(con_module._old_in_io,
                        con_module._old_out_io)
                    self.ass.appendModule(con_module)

            for _, outp in self.cad_object.outputs.items():
                con_module = outp.connectedTo
                if con_module:
                    con_module.reconnectIOs(con_module._old_in_io,
                        con_module._old_out_io)
                    self.ass.appendModule(con_module)

        self.parent.refresh()

class NewWindow(MyWindow): #HPD - 25/11/19
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New ChemCAD Window")

    def closeEvent(self, event):
        close = QtWidgets.QMessageBox.question(self,
                                         "QUIT",
                                         "Are you sure want to close this project?",
                                         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if close == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()



def main():
    # logger = MyLog()
    # try:
    app = QtWidgets.QApplication(sys.argv)

    # ex = Fenetre(logger)
    ex = MyWindow()
    app.processEvents()
    sys.exit(app.exec_())
    print("\n".join(repr(w) for w in app.allWidgets()))

if __name__ == "__main__":
    main()
