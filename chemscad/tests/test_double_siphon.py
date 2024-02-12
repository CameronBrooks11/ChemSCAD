
import os
import pytest
import numpy as np
import subprocess as sp
import trimesh
import solid.utils as su

from ccad.log import MyLog
from ccad.reactor import ReactorCAD as rea
from ccad.double_siphon import DoubleSiphonCAD
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


def test_output_height_constraint():

    """
    Crash if output too high
    """
    l.debug("Testing height constraint")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_a.addOutputPercentage("test", height_per=10)
    r_b.addInputPercentage("test")

    with pytest.warns(UserWarning):
        d = DoubleSiphonCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])

    logAssert(
        np.isclose(d._height, 49.55, 1e-2), "Wrong height for DS after adapting height"
    )


def test_properties():

    """Test Length, width, and height of DS
    """
    l.debug("Testing properties")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_a.addOutputPercentage("test", height_per=20)
    r_b.addInputPercentage("test")

    d = DoubleSiphonCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])

    logAssert(
        np.isclose(d.length, 16.33, 1e-2),
        "Properties: Wrong length: {}".format(d.length),
    )

    logAssert(d.width == 9, "Properties: Wrong width: {}".format(d.width))

    logAssert(
        np.isclose(d.height, 49.55, 1e-2),
        "Properties: Wrong height: {}".format(d.height),
    )

    d.length = 30
    logAssert(d.length == 30, "Wrong length: {}".format(d.length))

    x = np.array(r_b.coo["x"])
    logAssert(
        np.isclose(x, -59.72, 1e-2),
        "Wrong x after modification for reactor 2: {}".format(x),
    )


def test_translations():

    """
    Check that the siphon will properly translate the objects it connects
    """
    l.debug("Testing Translations")
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test")

    c = DoubleSiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])
    x = np.array(r_b.coo["x"])

    logAssert(
        np.isclose(x, 46.06, 1e-2), "Translation: Wrong x for 2nd reactor: {}".format(x)
    )

    # 2 reactors, first one has its output at 30°
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test")

    c = DoubleSiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

    x = np.array(r_b.coo["x"])
    y = np.array(r_b.coo["y"])

    logAssert(
        np.isclose(x, 39.88, 1e-2),
        "Translation: Wrong x {} for 2nd reactor, output 1st at 30deg".format(x),
    )

    logAssert(
        np.isclose(y, 23.03, 1e-2),
        "Translation: Wrong y {} for 2nd reactor, output 1st at 30deg".format(y),
    )

    # 3 reactors, first one has its output at 30°, 2nd one has its input at
    # -30° (30 ° from its output). Results in collision between 1st and 3rd
    # reactor
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)
    r_c = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)

    r_b.addInputPercentage("test", angle=-30)
    r_c.addInputPercentage("test")

    c = DoubleSiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])
    c_2 = DoubleSiphonCAD(r_b, r_b.outputs["default"], r_c, r_c.inputs["test"])

    x = np.array(r_c.coo["x"])
    y = np.array(r_c.coo["y"])
    angle = np.array(r_c.coo["angle"])

    logAssert(
        np.isclose(x, 16.85, 1e-2), "Translation: Wrong x {} for 3rd reactor".format(x)
    )

    logAssert(
        np.isclose(y, -16.85, 1e-2), "Translation: Wrong y {} for 3rd reactor".format(y)
    )

    logAssert(np.isclose(angle, 240, 1e-2), "Translation: Wrong angle {}".format(angle))


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

    c = DoubleSiphonCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

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
