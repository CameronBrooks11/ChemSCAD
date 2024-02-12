#!/usr/bin/python
# coding: utf-8

import os
import pytest
import numpy as np
import itertools
import subprocess as sp
import trimesh
import solid.utils as su

from ccad.log import MyLog
from ccad.reactor import ReactorCAD as rea
from ccad.siphon import SiphonCAD
import ccad.constants as cst
from ccad.exceptions import *


l = MyLog("output_tests_siphon.log", mode="w")

l.debug("---------------------- START NEW RUN OF TESTS ----------------------")
l.debug("\n")


def logAssert(test, msg):

    """
    Function to log the result of an assert
    http://stackoverflow.com/questions/24892396/py-test-logging-messages-and-test-results-assertions-into-a-single-file
    """

    if not test:
        l.error(msg)
        assert test, msg


def test_error_handling():

    """
    Siphon class must crash if instantiated with an input and output w
    different diameters, or if input/output are too close to each other,
    or any invalid parameter
    """

    l.debug("Testing error handling")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Create 2 inputs at the same height
    r_a.addOutputPercentage("test")
    r_b.addInputPercentage("test")

    # Check that exp is raised if I/O vertically too close
    with pytest.raises(ConstraintError):
        SiphonCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])
        l.error("Siphon: no exception raised when I/O vertically too close")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Create 2 inputs with different diameters
    r_a.addOutputPercentage("test", height_per=20, diameter=2)
    r_b.addInputPercentage("test", diameter=3)

    # Check that exp is raised if I/O have different diameters
    with pytest.raises(IncompatibilityError):
        SiphonCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])
        l.error("Siphon: I/O with different diameters")


def test_properties():

    """Make sure properties (setters/getters) work properly"""

    # TODO: tests on offsets_type

    l.debug("Testing properties")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Create 2 inputs with different diameters
    r_a.addOutputPercentage("test", height_per=20)
    r_b.addInputPercentage("test")

    c = SiphonCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])

    # Test values returned for properties
    logAssert(
        np.isclose(c.length, 10.33, 1e-2),
        "Properties: wrong length {} returned".format(c.length),
    )

    logAssert(c.width == 9, "Properties: wrong width {} returned".format(c.width))

    logAssert(
        np.isclose(c.height, 36.64, 1e-2),
        "Properties: wrong height returned: {}".format(c.height),
    )

    c.length = 20

    x = np.array(r_b.coo["x"])

    logAssert(c.length == 20, "Properties: wrong length after modif")

    # After modifying length, 2nd reactor must have moved
    logAssert(
        np.isclose(x, -49.73, 1e-2),
        "Properties: wrong x for 2nd reactor after modif length {}".format(x),
    )


def test_translations():

    """
    Check that the siphon will properly translate the objects it connects
    """

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test")

    c = SiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

    x = np.array(r_b.coo["x"])

    # First test, 2 reactors aligned on x axis
    logAssert(
        np.isclose(x, 40.06, 1e-2), "Translation: wrong x {} for 2nd reactor".format(x)
    )

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test")

    c = SiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

    x = np.array(r_b.coo["x"])
    y = np.array(r_b.coo["y"])

    # 2 reactors, first one has its output at 30°
    logAssert(
        np.isclose(x, 34.69, 1e-2),
        "Translation: wrong x {} for 2nd reactor, output 1st at 30°".format(x),
    )
    logAssert(
        np.isclose(y, 20.03, 1e-2),
        "Translation: wrong y {} for 2nd reactor, output 1st at 30°".format(y),
    )

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)
    r_c = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)

    r_b.addInputPercentage("test", angle=-30)
    r_c.addInputPercentage("test")

    c = SiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])
    c_2 = SiphonCAD(r_b, r_b.outputs["default"], r_c, r_c.inputs["test"])

    x = np.array(r_c.coo["x"])
    y = np.array(r_c.coo["y"])
    angle = np.array(r_c.coo["angle"])

    # 3 reactors, first one has its output at 30°, 2nd one has its input at
    # -30° (30 ° from its output). Results in collision between 1st and 3rd
    # reactor
    logAssert(
        np.isclose(x, 14.66, 1e-2),
        "Translation: wrong x {}for 3rd reactor, ultimate test".format(x),
    )
    logAssert(
        np.isclose(y, -14.66, 1e-2),
        "Translation: wrong y {} for 3rd reactor, ultimate test".format(y),
    )
    logAssert(
        np.isclose(angle, 240, 1e-2),
        "Translation: wrong angle {}, ultimate test".format(angle),
    )


def test_valid_stl():

    """
    Render the STL file for 2 reactors, one siphon
    Then test the validity of the STL file:
    - Check if watertight (True if there is non non-manifold surfaces)
    - Check valid volume
    """

    l.debug("Testing STLs validity")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test")

    c = SiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

    su.scad_render_to_file(r_a.cad + r_b.cad + c.cad, "test.scad")

    # Render the reactor into a stl file
    cmd = sp.Popen(
        ["openscad", "-o", "test.stl", "test.scad"], stdout=sp.PIPE, stderr=sp.PIPE
    )

    # Wait until rendering is finished
    out, err = cmd.communicate()

    # Check if rendering succeeded, crash the test otherwise
    if cmd.returncode != 0:
        l.error("Failed to render STL for 2 reactors, 1 siphon")
        pytest.fail("Failed to render STL for 2 reactors, 1 siphon")

    # Generate the mesh from STL file
    mesh = trimesh.load_mesh("test.stl")

    logAssert(mesh.is_watertight is True, "2 reactors, 1 siphon, not watertight")

    logAssert(mesh.volume > 0, "2 reactors, 1 siphon, negative volume")

    # Remove files to not polute dir
    os.remove("test.scad")
    os.remove("test.stl")


if __name__ == "__main__":
    pass
