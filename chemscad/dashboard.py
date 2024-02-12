#!/usr/bin/python
# coding: utf-8

# https://stackoverflow.com/questions/12576454/python-and-matplotlib-and-annotations-with-mouse-hover
# https://stackoverflow.com/questions/7908636/possible-to-make-labels-appear-when-hovering-over-a-point-in-matplotlib


import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from matplotlib.figure import Figure
from typing import Dict, Tuple, List

# matplotlib.use("Qt5Agg")

from ccad.object import ObjectCAD
from ccad import ReactorCAD
import chemscad.app_constants as app_cst


class Dashboard(FigCanvas):

    """
    A canvas. Will be used as a dashboard to display the assembly. Has mouse hovering
    and mouse clicking feature.  Snake case is used in this module for compatibility
    purposes with matplotlib function names. Methods called by GUI will use Camel case
    """

    def __init__(
        self, parent=None, width: int = 5, height: int = 4, dpi: int = 100
    ) -> None:

        fig = Figure(figsize=(width, height), dpi=dpi)
        super(Dashboard, self).__init__(fig)
        gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[1, 3])
        self.axes = fig.add_subplot(gs[1])
        self.axes_info = fig.add_subplot(gs[0])

        # Remove axes
        self.axes.axis("off")
        self.axes_info.axis("off")

        # Initialise info text
        self.info_text = self.axes_info.text(0, 0, "")

        # # Display grid
        self.axes.grid(True)

        # self.setParent(parent)
        self.parent = parent

        FigCanvas.setSizePolicy(
            self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        FigCanvas.updateGeometry(self)

        # Connect the event to internal callbacks: mouse hovering and
        # mouse clicking
        self.mpl_connect("motion_notify_event", self._on_move)
        fig.canvas.mpl_connect("pick_event", self._on_pick)

        # Dict to associate a patch (circle, rectangle, etc) to a cad object
        self.dict_buttons: Dict[plt.Circle, Tuple[ReactorCAD, str]] = dict()

        self.x_min = 0
        self.y_min = 0

    def _draw_reactors(self):

        """Methods to draw the reactor-like objects (not the connectors)"""

        # Store unconnected reactors
        list_unconnected: List[ReactorCAD] = list()

        for index, reactor in enumerate(self.parent.ass.list_reactors):

            # If the reactor is not connected, don't draw it now.
            # Store it and deal with it later
            if not reactor.isConnected():
                list_unconnected.append(reactor)
                continue

            # Get the coordinates of the reactor and its radius
            x, y, r = reactor.coo["x"], reactor.coo["y"], reactor.infos["r_ex"]

            # Get proper colour for module
            colour = self._get_module_colour(reactor.module_type)

            # Create a circle at the coo of the reactor, with r of the reactor.
            # Picker is True to activate mouse click events
            circle = plt.Circle((x, y), radius=r, picker=True, fc=colour, ec="k")

            # Rotate the circle, for aesthetics purposes
            # (the CAD process expands the assembly towards -y, rotate to
            # expand towards +x)
            t = mpl.transforms.Affine2D().rotate_deg(-90) + self.axes.transData
            circle.set_transform(t)

            # Calculate (x, y) for input of input object
            # Calculate new x,y coordinates by using a transformation matrix
            # rotation of -90°
            a = np.deg2rad(-90)
            rotation = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
            coo = np.array([x, y])

            x, y = np.dot(rotation, coo)

            # Find short name for reactor. Use assembly
            for name, module in self.parent.ass.reactors_names.items():
                if reactor is module:
                    module_name = name

            self.axes.annotate(
                module_name, xy=(x, y), ha="center", va="center", fontsize=20
            )

            # Associate the circle to the CAD object, and to its name
            self.dict_buttons[circle] = (reactor, reactor.module_type)

            # Add the circle to the axes
            self.axes.add_patch(circle)

        self._update_figure()

        # Now draw unconnected reactors separately
        self._draw_unconnected_reactor(list_unconnected)

    def _draw_unconnected_reactor(self, list_unconnected: List[ReactorCAD]):

        """
        Method to draw the unconnected reactors. Called from _draw_reactors
        """

        # Deal with the unconnected reactors
        for reactor in list_unconnected:

            # index = self.parent.ass.list_reactors.index(reactor)

            # Get x axis max limit
            _, x_max = self.axes.get_xlim()

            # Assign coordinates to unconnected reactor (don't simply use
            # (0, 0))
            x, y, r = x_max, 0, reactor.infos["r_ex"]

            # Add some space in x before drawing reactor
            x = x + 2 * r

            # Get proper colour for module
            colour = self._get_module_colour(reactor.module_type)

            # Create a circle at the coo of the reactor, with r of the reactor.
            # Picker is True to activate mouse click events
            # circle = plt.Circle((x, y), radius=r, picker=True)
            circle = plt.Circle((x, y), radius=r, picker=True, fc=colour, ec="k")

            # Find short name for reactor. Use assembly
            for name, module in self.parent.ass.reactors_names.items():
                if reactor is module:
                    module_name = name

            self.axes.annotate(
                module_name, xy=(x, y), ha="center", va="center", fontsize=20
            )

            # Associate the circle to the CAD object, and to its name
            self.dict_buttons[circle] = (reactor, reactor.module_type)

            # Add the circle to the axes
            self.axes.add_patch(circle)

            # Update the graph in the loop, to always get x_max right after
            # adding an unconnected reactor
            self._update_figure()

    def _draw_connectors(self):

        """Methods to draw the connectors objects"""

        for con in self.parent.ass.list_connectors:

            x, y, angle = con.coo["x"], con.coo["y"], con.coo["angle"]
            length, width = con.length, con.width

            # Translate rectangles properly (origin of rectangle is lower
            # left corner)
            x = x + (width / 2) * np.sin(np.deg2rad(abs(angle)))
            y = y - (width / 2) * np.cos(np.deg2rad(abs(angle)))

            # Get proper colour for module
            colour = self._get_module_colour(con.module_type)

            rect = plt.Rectangle(
                (x, y), length, width, fc=colour, angle=angle, picker=True, ec="k"
            )

            # Rotate the rectangle, for aesthetics purposes
            # (the CAD process expands the assembly towards -y, rotate to
            # expand towards +x)
            t = mpl.transforms.Affine2D().rotate_deg(-90) + self.axes.transData
            rect.set_transform(t)

            # Add the rectangle to the axes
            self.axes.add_patch(rect)

            # Associate the rect to the CAD object, and to its name
            self.dict_buttons[rect] = (con, con.module_type)

        self._update_figure()

    def _get_module_colour(self, module_type: str) -> str:

        """
        Return the colour for `module_type`. Uses a dict defined in the
        app_constants. If the module type is unknown, use white. Return a
        hexadecimal colour
        """

        dict_colours = app_cst.colours_modules

        # Get colour for module. If unknown module, use white
        hex_colour = dict_colours.get(module_type, "#FFFFFF")

        return hex_colour

    def _clear_figure(self):

        """Clear the graph"""

        self.axes.clear()
        self._update_figure()

    def _update_figure(self):

        """Update the graph. Necessary, to call after each plot"""

        # Reset the axes aspect
        self.axes.set_aspect("equal", adjustable="box")
        self.axes.autoscale_view()
        self.axes.axis("off")

        self.draw()

    def _clear_info_text(self):

        """Clear info text subplot"""

        self.info_text.set_text("")

    def _on_move(self, event):

        """
        Method to handle mouse hovering. Subclassed from matplotlib Canvas
        """

        self._clear_info_text()
        # For all the pacthes in the canvas
        for patch, couple in self.dict_buttons.items():

            # TODO: different colours depending on module_type
            module_type = couple[1]

            # If the pacth contains the mouse, change colour of patch to
            # show selection. Also change colour of all the other patches,
            # to show unselection
            if patch.contains(event)[0]:
                self._clear_info_text()
                self.info_text.set_text(self._get_info_text(couple[0]))
                patch.set_facecolor("#FF6962")
            else:
                colour = self._get_module_colour(module_type)
                patch.set_facecolor(colour)
        self._update_figure()

    def _on_pick(self, event):

        """
        Method to handle click event on the pacthes. Subclassed from
        matplotlib Canvas
        """

        # From the patch clicked, get the CAD object and its type
        cad_obj, module_type = self.dict_buttons[event.artist]

        # Open the dialog box corresponding to the type of the CAD object
        self.parent.openModuleDialog(cad_obj)

    def refresh(self):

        """
        Refresh the canvas. Called by parent (GUI) when assembly is modified
        """

        # Reset the dict of objects, will be rebuilt
        del self.dict_buttons
        self.dict_buttons = dict()

        self.x_min = 0
        self.y_min = 0

        # Clear the canvas
        self._clear_figure()

        # Draw the reactors
        self._draw_reactors()

        # Draw the connectors
        self._draw_connectors()

    def _get_info_text(self, module: ObjectCAD):

        """Return str presenting info of given module"""

        infos = module.infos
        info_text = ""

        for key, value in infos.items():

            # v_str is the vlaue properly formatted (2 decimals if float)
            if isinstance(value, float):
                v_str = f"{value:.2f}"
            else:
                v_str = str(value)

            info_text += f"{key}: {v_str}\n"

        return info_text
