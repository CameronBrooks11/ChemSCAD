import os
import pytest
import numpy as np
import itertools
import subprocess as sp
import trimesh
import solid.utils as su

from ccad.log import MyLog
from ccad.reactor import ReactorCAD as rea
from ccad.tube_connector import TubeConnectorCAD
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


def test_output_constraint():

    """Crash if output too high"""

    l.debug("Testing constraints on outputs")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_a.addOutputPercentage("test", height_per=50)
    r_b.addInputPercentage("test", height_per=50)

    t = TubeConnectorCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])


def test_vertical_translation():
    l.debug("Testing vertical translations")
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test", height_per=100)

    t = TubeConnectorCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"], conflicts="lift_in_obj")

    logAssert(
        np.isclose(np.array(r_a.coo["z"]), 40.55, 1e-2),
        "Z does not match if lift in obj!"
    )  

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test", height_per=0)
    r_a.addOutputPercentage("test", height_per=100)

    t = TubeConnectorCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"], conflicts="lift_out_obj")

    logAssert(
        np.isclose(np.array(r_b.coo["z"]), 34.55, 1e-2),
        "Z does not match if lift out obj!"
    )  


def test_properties():
    """Test Length, width, and Height of TC
    """
    l.debug("Testing properties")

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_a.addOutputPercentage("test", height_per=50)
    r_b.addInputPercentage("test", height_per=50)

    t = TubeConnectorCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])

    logAssert(
        np.isclose(t.length, 1.33, 1e-2),
        "Properties: Wrong length: {}".format(t.length),
    )

    logAssert(t.width == 9, "Properties: Wrong width: {}".format(t.width))

    logAssert(
        np.isclose(t.height, 9.00, 1e-2),
        "Properties: Wrong height: {}".format(t.height),
    )

    t.length = 10
    logAssert(t.length == 10, "Properties: Wrong length: {}".format(t.length))

    x = np.array(r_b.coo["x"])
    logAssert(
        np.isclose(x, -39.72, 1e-2),
        "Worng x after modification of reactor 2: {}".format(x),
    )


def test_translations():

    """
    Check that the siphon will properly translate the objects it connects
    """

    l.debug("Testing Translations")
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test", height_per=50)
    t = TubeConnectorCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])
    x = np.array(r_b.coo["x"])

    logAssert(
        np.isclose(x, 31.06, 1e-2), "Translation: Wrong x for 2nd reactor: {}".format(x)
    )

    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r_b.addInputPercentage("test", height_per=50)
    t = TubeConnectorCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])

    x = np.array(r_b.coo["x"])
    y = np.array(r_b.coo["y"])

    logAssert(
        np.isclose(x, 26.89, 1e-2),
        "Translation: Wrong x {} for 2nd reactor, output 1st at 30deg".format(x),
    )

    logAssert(
        np.isclose(y, 15.53, 1e-2),
        "Translation: Wrong y {} for 2nd reactor, output 1st at 30deg".format(y),
    )

    # 3 reactors, first one has its output at 30°, 2nd one has its input at
    # -30° (30 ° from its output). Results in collision between 1st and 3rd
    # reactor
    r_a = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 30)
    r_b = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)
    r_c = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O, 0)

    r_b.addInputPercentage("test", height_per=50, angle=-30)
    r_c.addInputPercentage("test", height_per=50)

    t1 = TubeConnectorCAD(r_a, r_a.outputs["default"], r_b, r_b.inputs["test"])
    t2 = TubeConnectorCAD(r_b, r_b.outputs["default"], r_c, r_c.inputs["test"])

    x = np.array(r_c.coo["x"])
    y = np.array(r_c.coo["y"])
    angle = np.array(r_c.coo["angle"])

    logAssert(
        np.isclose(x, 11.36, 1e-2), "Translation: Wrong x {} for 3rd reactor".format(x)
    )

    logAssert(
        np.isclose(y, -11.36, 1e-2), "Translation: Wrong y {} for 3rd reactor".format(y)
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

    r_b.addInputPercentage("test", height_per=50)
    r_a.addOutputPercentage("test", height_per=50)

    c = TubeConnectorCAD(r_a, r_a.outputs["test"], r_b, r_b.inputs["test"])
    c.length = 5

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
