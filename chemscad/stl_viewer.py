#!/usr/bin/python
# coding: utf-8

from vispy.visuals.shaders import Function, Varying
from vispy.color import colormap, Color
import os
from vispy import app, geometry, gloo
import vispy.scene
from vispy.scene import visuals
from vispy.app import use_app
from chemscad.log import MyLog
from typing import Tuple, Union, Dict
from vispy.visuals.filters import Alpha
import vispy.io
from vispy.gloo.util import _screenshot
import numpy as np
from chemscad.app_constants import colours_module_type_short
from glob import glob

use_app("PyQt5")


class STLViewer(vispy.scene.SceneCanvas):

    """"
    Class to view a STL file. Camera is embedded, so rotations/translations are
    possible
    https://github.com/vispy/vispy/issues/1425
    https://github.com/vispy/vispy/issues/1479
    """

    # Initial direction for light, for all meshes
    INI_LIGHT_DIR = (0, -1, 0)

    # Alpha value when a module is transparent
    TRANSPARENT_ALPHA_CST = 0.4

    def __init__(
        self,
        size: Tuple[int, int] = (800, 500),
        watch_dir: str = ".",
        logger: Union[None, MyLog] = None,
    ) -> None:

        """
        size is the size in pixels (x, y). watch_dir is the path to watch
        for new STL files
        """

        vispy.scene.SceneCanvas.__init__(
            self, size=size, bgcolor="black", #keys="interactive",
        )

        # Unfreeze the class, so adding attributes is possible
        self.unfreeze()

        if logger is None:
            self.l = MyLog("activity.log")
        else:
            self.l = logger

        self.watch_dir = watch_dir

        # Create a dict to store several meshes
        # Meshes are stored with their names so they can be reloaded/reviewed
        # namely
        self.meshes: Dict[str, visuals.Mesh] = dict()

        # Add an 'arcball' camera
        self.view = self.central_widget.add_view()
        self.view.camera = "arcball"

        # Unzoom by default. Otherwise, too close to object at creation
        self.view.camera.scale_factor = 220

        # Store if perspective is enabled. Used by main window
        self.perspective = False

        # Translucent state for Meshes
        self.translucent = False



        # Inverse transform of the initial light dir. Needed to undo the
        # initial orientation of the camera
        direction = self.view.camera.transform.imap(self.INI_LIGHT_DIR)[:3]

        # Compensate for shift (translations) of the camera. This way the
        # light direction only depends of the local orientation of the camera,
        # not on the point it is looking at. For more details, see issue
        # vispy's issue #1479
        self.ini_light_dir = np.concatenate((direction, [0]))

        # Freeze the class again. Might not be necessary
        self.freeze()

    def togglePerspective(self):

        """Toggle the perspective view"""

        self.perspective = not self.perspective

        if self.perspective:
            self.view.camera.fov = 50
        else:
            self.view.camera.fov = 0

    def toggleTranslucent(self):

        """Toggle the translucent state of all the meshes. Called X-ray in GUI"""

        self.translucent = not self.translucent

        for mesh in self.meshes.values():

            # Change the alpha value of the mesh's alpha filter
            # Disable depht_test when translucent, better visual
            # https://github.com/vispy/vispy/issues/1482
            if self.translucent:
                self.view.camera.fov = 50 #HPD - fix x-ray view overlap issue by adding FOV
                if mesh.filter.alpha != 0:
                    mesh.filter.alpha = self.TRANSPARENT_ALPHA_CST
                    mesh.set_gl_state(depth_test=False)
            else:
                self.view.camera.fov = 0 #HPD - as above for FOV
                if mesh.filter.alpha != 0:
                    mesh.filter.alpha = 1
                    mesh.set_gl_state(depth_test=True)

        # Update the scene immediately
        self.view.scene.update()

    def viewMesh(self, file_name: str):

        """
        Will load the file file_name in the STL viewer. If the mesh didn't
        exist before, it will be created. Else, it will be updated
        """

        # file_name is passed wo extension, so add .stl
        file_name = file_name + ".stl"

        file_to_view = os.path.join(self.watch_dir, file_name)

        self.l.debug(f"Trying to load STL file {file_to_view}")

        try:
            # Load the stl file. Works with binary or ascii stl files
            raw_mesh = vispy.io.stl.load_stl( open(file_to_view, 'r') )
            mdata = geometry.MeshData(raw_mesh['vertices'], raw_mesh['faces'])


        except Exception as e:
            self.l.error(
                f"{e}: Failed to load STL {file_to_view} in Canvas", exc_info=True
            )
            return

        # Try to update the mesh, if it doesn't exist, create it
        try:
            self.meshes[file_name].set_data(meshdata=mdata)
            self.l.debug(f"Updating STL {file_name}")
        except KeyError:
            self.l.debug(f"Mesh for {file_name} doesn't exist yet, creating")

            module_type_short = file_name.split(".scad")[0]
            module_type_short = "".join(
                [i for i in module_type_short if not i.isdigit()]
            )

            # Create a Mesh visual, with the view as parent
            mesh = visuals.Mesh(
                meshdata=mdata,
                shading="flat",
                parent=self.view.scene,
                color=colours_module_type_short[module_type_short],
            )

            # Set up the shininess (0 means mat)
            # set up the initial light direction for the mesh
            # Create an alpha filter. alpha=1
            mesh.light_dir = self.INI_LIGHT_DIR
            mesh.shininess = 0
            translucent_filter = Alpha()

            self.meshes[file_name] = mesh

            # Unfreeze the mesh, and make the alpha filter one of
            # its attributes
            self.meshes[file_name].unfreeze()
            self.meshes[file_name].filter = translucent_filter
            self.meshes[file_name].attach(translucent_filter)
            self.meshes[file_name].freeze()

            # Disable depth_test when translucent, better visual
            if self.translucent:
                mesh.set_gl_state(depth_test=False)

    def deleteMesh(self, file_name: str):
        """
        Deletes a mesh from meshes dict. This is invoked when a user
        deletes one of the modules
        """

        # First we will delete the mesh of the acutal object to delete
        dict_key = file_name+".scad.stl"

        try:
            mesh = self.meshes[dict_key]
            mesh.parent = None # based on vispy this is what actually deletes it
            del mesh
            del self.meshes[dict_key]
            self.l.debug(f"Deleting mesh {dict_key}")
        except KeyError:
            self.l.debug(f"Mesh for {dict_key} doesn't exist yet. Cannot delete")

        # Now, because JP doesn't want to show disconnected objects, his code
        # automatically deletes all the STLs and SCADs of disconnected objects.
        # Meaning that if the object to delete would create disconnected objects
        # their files will be deleted and we should also remove them from the mesh.
        # Therefore we will the files left in the render folder, and delete
        # the meshes that don't have a file in render.
        # Disconnected objects that were not user-deleted are still part of
        # the assembly, and showed in the dashboard, but not show in the
        # 3D visualization

        # first obtain the stl files still in the watch folder
        stls = [os.path.basename(stl) for stl in
            glob(self.watch_dir+'/*.stl')]

        # now delete the meshes without an associated stl file
        for dict_key in list(self.meshes):

            # if the mesh doesnt have a file in renders, delete it
            if dict_key not in stls:
                try:
                    mesh = self.meshes[dict_key]
                    mesh.parent = None
                    del mesh
                    del self.meshes[dict_key]
                    self.l.debug(f"Deleting mesh {dict_key}")
                except KeyError:
                    self.l.debug(f"Mesh for {dict_key} doesn't exist yet. Cannot delete")

        self.view.scene.update()

    def toggleVisibility(self, module_id: str):

        """
        If switch_state == True make Mesh associated with file name visible,
        otherwise make the Mesh invisible.
        """

        # Forge the file_name from the module_id
        file_name = module_id + ".scad.stl"
        mesh = self.meshes[file_name]

        # Toggle visibility by changing alpha
        if mesh.filter.alpha != 0:
            mesh.filter.alpha = 0
            mesh.set_gl_state(depth_test=False)
        else:
            if self.translucent:
                mesh.filter.alpha = self.TRANSPARENT_ALPHA_CST
                mesh.set_gl_state(depth_test=False)
            else:
                mesh.filter.alpha = 1
                mesh.set_gl_state(depth_test=True)

        self.view.scene.update()

    def screenshot(self, path: str):

        """
        Render the current canvas to an image and save the image
        https://stackoverflow.com/questions/28732937/how-to-export-vispy-result-as-png-image
        """

        img = _screenshot()
        vispy.io.write_png(path, img)

    def on_mouse_move(self, event):

        """
        Called when mouse is clicked and is moving. Sub-classed to make
        the light follow the camera
        """

        transform = self.view.camera.transform

        for name, mesh in self.meshes.items():

            # Forward transform on light dir, light follows camera
            mesh.light_dir = transform.map(self.ini_light_dir)[:3]

    # def on_mouse_release(self, event):

    # self.screenshot()

    # """Attempt to change the light of the mesh when mouse is released"""

    # for mesh in self.meshes.values():
    # Doesn't work bc position of light_dir follows the mesh
    # mesh.light_dir = (0, -50, 50)

    # self.view.scene.update()


if __name__ == "__main__":
    win = STLViewer()
    win.viewMesh("R1.scad")
    win.show()

    import sys

    if sys.flags.interactive != 1:
        app.run()
        print(app)
