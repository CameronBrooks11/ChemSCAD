#!/usr/bin/python
# coding: utf-8

import pytest
import numpy as np
import itertools
import subprocess as sp
import trimesh
import os
import solid

from ccad.log import MyLog
from ccad.reactor import ReactorCAD as rea
from ccad.top_in import TopInlet
from ccad.exceptions import *
import ccad.constants as cst


l = MyLog("output_tests_reactor.log", mode="w")

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


@pytest.fixture()
def all_reactors() -> list:

    """
    Fixture:
    return all types of reactors, based on permutations of tops and bottoms
    """

    list_reactors = []

    tops = rea.TOPS
    bottoms = rea.BOTTOMS

    # Generate a list of all possible permutations
    for couple in itertools.product(tops, bottoms):
        list_reactors.append((couple[0], couple[1]))

    l.debug("List of reactors generated:\n")
    l.debug(list_reactors)

    return list_reactors


def test_error_handling():

    """Reactor class must crash if provided with invalid parameters"""

    l.debug("Testing error handling")

    # Raise exception if volume is 0
    with pytest.raises(ValueError):
        rea(0, rea.T_CLOSED_ROUND, rea.B_ROUND_IN_O)
        l.error("Reactor class: no exception raised when invalid volume")

    # Raise exception if volume is < 0
    with pytest.raises(ValueError):
        rea(-10, rea.T_CLOSED_ROUND, rea.B_ROUND_IN_O)
        l.error("Reactor class: no exception raised when invalid volume")

    # Raise exception when setting volume to -30 mL
    with pytest.raises(ValueError):
        r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)
        r.volume = -30
        l.error("Reactor: no exception raised when setting invalid volume")


def test_walls():

    """Tests for wall thickness (property)"""

    l.debug("Testing walls")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND_IN_O)

    # Test if walls thickness returned has valid value
    logAssert(r.walls == 3, "Wrong walls thickness returned")

    r.walls = 4

    # Test if walls thickness returned has valid value
    logAssert(r.walls == 4, "Wrong walls thickness after change")

    h = r.outputs["default"].height

    # Changing wall thickness should update dafault output height
    logAssert(h == 5.5, "Default output at wrong h {} after changing walls".format(h))

    # Walls must be at least 3 mm if threaded top
    r = rea(20, rea.T_2_QUA_INCH, rea.B_ROUND_IN_O, walls=2)
    logAssert(r.walls == 3, "Wrong walls thickness w/ threaded top")

    # Walls must be at least 3mm if ext outlet
    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND_EX_O)
    r.walls = 2

    logAssert(r.walls == 3, "Wrong walls thickness w/ ext outlet")


def test_volume():

    """Tests for volume (property)"""

    l.debug("Testing volume")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)

    # Test if volume returned has proper value (should return volume in mL)
    logAssert(r.volume == 20.0, "Wrong volume returned")

    r.volume = 30

    # Test if volume returned has proper value, after modifying it
    logAssert(r.volume == 30.0, "Wrong volume returned after modif")

    logAssert(
        np.isclose(r._r, 12.79, 1e-2), "Wrong r after changing volume {}".format(r._r)
    )
    logAssert(
        np.isclose(r._h, 41.37, 1e-2), "Wrong h after changing volume {}".format(r._h)
    )

    # Change internal radius
    r.r = 14

    # Test if volume returned has proper value, after constraining r
    logAssert(r.volume == 30.0, "Wrong volume after constraining r")

    # Test h was properly modified when constraining r
    logAssert(
        np.isclose(r._h, 30.05, 1e-2), "Wrong h after constraining r {}".format(r._h)
    )


def test_d_can():

    """Tests for diameter of canula (property)"""

    l.debug("Testing d_can")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND_IN_O)

    # Test if diameter for canula has valid value
    logAssert(r.d_can == 3, "Wrong d_can returned")

    # Change canula's diameter
    r.d_can = 5

    # Test if canula has proper diameter
    logAssert(r.d_can == 5, "Wrong d_can diameter returned after modif")

    # Check default output is updated when changing d_can
    logAssert(
        r.outputs["default"].height == 5.5,
        "Wrong height for default output after d_can modif",
    )


def test_type_top():

    """Tests for top type (property)"""

    l.debug("Testing top type")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)

    # Test if types of top is properly returned
    logAssert(r.type_top == rea.T_CLOSED_ROUND, "Wrong top type returned")

    r.type_top = rea.T_OPEN

    # Test that changing top type updates h
    logAssert(
        np.isclose(r._h, 38.09, 1e-2), "Wrong h after changing top {}".format(r._h)
    )
    logAssert(
        np.isclose(r._r, 11.77, 1e-2), "Wrong r after changing top {}".format(r._r)
    )


def test_type_bottom():

    """Tests for bottom type (property)"""

    l.debug("Testing bottom type")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)

    # Test if types of top and bottom are properly returned
    logAssert(r.type_bottom == rea.B_ROUND, "Properties: wrong bottom type returned")

    # Change type bottom
    r.type_bottom = rea.B_FLAT_EX_O

    # Create an input to check if it's shifted when changing type_bottom
    r.addInputPercentage("test")

    # Test that changing bottom type updates h
    logAssert(
        np.isclose(r._h, 38.09, 1e-2), "Wrong h after changing top {}".format(r._h)
    )
    logAssert(
        np.isclose(r._r, 11.77, 1e-2), "Wrong r after changing top {}".format(r._r)
    )

    # Check there is a default output after changing type_bottom
    # Check default output is at right height
    logAssert(
        r.outputs["default"].height == 5.5,
        "Wrong h for def output after modif type_bottom",
    )

    # CHange type bottom
    r.type_bottom = rea.B_FLAT_IN_O

    logAssert(
        r.outputs["default"].height == 4.5,
        "Wrong h for def output after 2nd modif type_bottom",
    )

    # Check input 'test' was shifted
    logAssert(
        np.isclose(r.inputs["test"].height, 45.59, 1e-2),
        "Wrong h {} for input 'test' after modif type_bottom".format(
            r.inputs["test"].height
        ),
    )


def test_def_out_angle():

    """Tests for angle for default output (property)"""

    l.debug("Testing default output angle")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND_IN_O)

    # Test original angle for def_out_angle
    logAssert(r.def_out_angle == 0, "Properties: wrong value for def_out_angle")

    # Test modification of def_out_angle
    r.def_out_angle = 30

    logAssert(
        np.isclose(np.array(r.def_out_angle), 30, 10e-2),
        "Properties: wrong value for def_out_angle after modif",
    )
    logAssert(
        np.isclose(np.array(r.outputs["default"].angle), 30, 10e-2),
        "Outputs: wrong value for def_out_angle after modif",
    )


def test_types():

    """
    Make sure some important properties have the right type and are returned
    properly
    """

    l.debug("Testing properties")

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)

    # Test that property cad is an openscadobject
    logAssert(
        type(r.cad) is solid.objects.translate,
        "Properties: wrong type for reactor.cad: {}".format(type(r.cad)),
    )

    # The CAD code must be a string
    logAssert(type(r.code) is str, "Properties: wrong type for reactor.code")


def test_h_r(all_reactors: list):

    """
    For a 20 mL reactor, check that h and R are right, depending on the
    shape of the reactor
    """

    l.debug("Testing h and r")

    for couple in all_reactors:

        l.debug(
            "Testing h and r for couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        r = rea(20, couple[0], couple[1])

        # Closed top, round bottom (without or with inlet)
        if couple[0] in rea.CLOSED_TOPS and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 36.14, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(
                np.isclose(r._r, 11.17, 1e-2),
                "R is wrong for couple {}".format(r._r, couple),
            )

        # Treat these cases together: the inside of the reactor has the
        # same shape: closed top and flat bottom, or open top and round bottom
        elif (
            couple[0] in rea.CLOSED_TOPS
            and couple[1] in rea.FLAT_BOTS
            or couple[0] == rea.T_OPEN
            and couple[1] in rea.ROUND_BOTS
        ):

            logAssert(
                np.isclose(r._h, 38.09, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(
                np.isclose(r._r, 11.77, 1e-2),
                "R is wrong for couple {}".format(r._r, couple),
            )

        # Open top, flat bottom (without or with inlet)
        elif couple[0] in rea.T_OPEN and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 40.55, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(
                np.isclose(r._r, 12.53, 1e-2),
                "R is wrong for couple {}".format(r._r, couple),
            )

        # 1/2 inch threaded top, flat bottom
        elif couple[0] == rea.T_2_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 63.67, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 10, "R is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_2_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 56.99, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 10, "R is wrong for couple {}".format(r._r, couple))

        # 3/4 inch threaded top, flat bottom
        elif couple[0] == rea.T_3_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            print(r._r)
            print(r._h)

            logAssert(
                np.isclose(r._h, 44.21, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 12, "R is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_3_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 36.21, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 12, "R is wrong for couple {} {}".format(r._r, couple))

        # 1 inch threaded top, flat bottom
        elif couple[0] == rea.T_4_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 24.87, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 16, "R is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_4_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 14.20, 1e-2), "h is wrong for couple {}".format(couple)
            )
            logAssert(r._r == 16, "R is wrong for couple {}".format(r._r, couple))

        else:
            l.error("output: unrecognized couple: {}; {}".format(couple[0], couple[1]))
            pytest.fail(
                "Output test failed for unrecognized couple: {}; {}".format(
                    couple[0], couple[1]
                )
            )


def test_infos():

    """Make sure the dict 'infos' returns proper values"""

    l.debug("Testing reactor's infos")

    r = rea(20, rea.T_OPEN, rea.B_ROUND)

    t_dict = {
        "r_ex": 14.771641655355797,
        "r": 11.771641655355797,
        "height": 52.865474258855315,
        "height_wo_inlet": 52.865474258855315,
        "height_body": 38.093832603499514,
        "height_bottom": 14.771641655355797,
        "inputs": 0,
        "outputs": 0,
        "walls": 3,
        "type_top": "Open",
        "type_bottom": "Round",
        "volume": 20.0,
        "d_can": 3,
        "align_top_strategy": "expand",
    }

    logAssert(
        t_dict == r.infos,
        "reactor.infos: dicts don't match. Test: {}; \n Target: {}".format(
            r.infos, t_dict
        ),
    )

    # Test that changing walls thickness changes r_ex
    r.walls = 4

    t_dict = {
        "r_ex": 15.771641655355797,
        "r": 11.771641655355797,
        "height": 53.865474258855315,
        "height_wo_inlet": 53.865474258855315,
        "height_body": 38.093832603499514,
        "height_bottom": 15.771641655355797,
        "inputs": 0,
        "outputs": 0,
        "walls": 4,
        "type_top": "Open",
        "type_bottom": "Round",
        "volume": 20.0,
        "d_can": 3,
        "align_top_strategy": "expand",
    }

    logAssert(
        t_dict == r.infos,
        "reactor.infos: dicts don't match. Test: {}; \n Target: {}".format(
            r.infos, t_dict
        ),
    )

    r = rea(20, rea.T_CLOSED_ROUND_O, rea.B_ROUND_IN_O)

    t_dict = {
        "r_ex": 14.168810962106537,
        "r": 11.168810962106537,
        "height": 74.48065342543465,
        "height_wo_inlet": 70.48065342543465,
        "height_body": 36.143031501221586,
        "height_bottom": 20.168810962106537,
        "inputs": 0,
        "outputs": 1,
        "walls": 3,
        "type_top": "Closed round with outlet",
        "type_bottom": "Round with internal outlet",
        "volume": 20.0,
        "d_can": 3,
        "align_top_strategy": "expand",
    }

    logAssert(
        t_dict == r.infos,
        "reactor.infos: dicts don't match. Test: {}; \n Target: {}".format(
            r.infos, t_dict
        ),
    )


def test_describe():

    l.debug("Testing reactor's text description")

    r = rea(60, rea.T_4_QUA_INCH, rea.B_FLAT_EX_O)
    r.addInputPercentage("test")

    comp = "type_top: Threaded cap 1 inch\n"
    comp += "type_bottom: Flat with external outlet\n"
    comp += "volume: 60.0\n"
    comp += "d_can: 3\n"
    comp += "align_top_strategy: expand\n"
    comp += "walls: 3\n"
    comp += "inputs: 1\n"
    comp += "outputs: 1\n"
    comp += "r_ex: 19\n"
    comp += "r: 16\n"
    comp += "height: 99.60387957432594\n"
    comp += "height_wo_inlet: 99.60387957432594\n"
    comp += "height_body: 74.60387957432594\n"
    comp += "height_bottom: 10.0\n"
    comp += "----- Input(s) -----\n"
    comp += "test: {'height': 80.10387957432594, 'diameter': 3, 'angle': 180.0, "
    comp += "'external': False, 'chamber': None}\n"
    comp += "----- Output(s) ----\n"
    comp += "default: {'height': 5.5, 'diameter': 3, 'angle': 0.0, 'external': True, "
    comp += "'chamber': None}"

    logAssert(repr(r.describe()) == repr(comp), "Reactor's description doesn't match")


def test_output():

    """
    Test that reactor has proper output. Just test the height of the output,
    should be enough
    """

    l.debug("Testing reactor's default output")

    # Test only bottoms with inlet
    all_bottoms = [rea.B_ROUND_IN_O, rea.B_ROUND_EX_O, rea.B_FLAT_IN_O, rea.B_FLAT_EX_O]

    for bottom in all_bottoms:

        # Type of top doesn't affect output's height, so only use open top
        r = rea(20, rea.T_OPEN, bottom)

        h = np.array(r.outputs["default"].height)

        if bottom == rea.B_ROUND_EX_O:
            logAssert(
                np.isclose(h, 5.5, 1e-2),
                "Bottom: {}, wrong output h {}".format(bottom, h),
            )

        elif bottom == rea.B_ROUND_IN_O:
            logAssert(
                np.isclose(h, 4.5, 1e-2),
                "Bottom: {}, wrong output h {}".format(bottom, h),
            )

        elif bottom == rea.B_FLAT_EX_O:
            logAssert(
                np.isclose(h, 5.5, 1e-2),
                "Bottom: {}, wrong output h {}".format(bottom, h),
            )

        elif bottom == rea.B_FLAT_IN_O:
            logAssert(
                np.isclose(h, 4.5, 1e-2),
                "Bottom: {}, wrong output h {}".format(bottom, h),
            )

        else:
            l.error("output: unrecognized  bottom".format(bottom))
            pytest.fail("Output test failed for unrecognized bottom: {}".format(bottom))


def test_add_input():

    """Test that inputs are properly added to a reactor"""

    l.debug("Testing add input feature")

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Check exception is raised when negative value for input height, or
    # if height > 100%
    with pytest.raises(ValueError):
        r.addInputPercentage("new", height_per=-10)
        l.error("Input: no exception raised when height_per < 0")
    with pytest.raises(ValueError):
        r.addInputPercentage("new", height_per=110)
        l.error("Input: no exception raised height_per > 100")

    # Add an input with default params
    r.addInputPercentage("test")

    t_dict = {
        "external": False,
        "angle": 180.0,
        "chamber": None,
        "diameter": 3,
        "height": 45.04822038391718,
    }
    logAssert(r.inputs["test"].infos == t_dict, "Dictionaries do not match")

    # After adding an input, reactor.cad still has the right type
    logAssert(type(r.cad) is solid.objects.translate, "Input: wrong type for reactor")

    # Test the input is a the right place (open top)
    h = np.array(r.inputs["test"].height)
    logAssert(
        np.isclose(h, 45.04, 1e-2),
        "Input: default input at the wrong place (open top) {}".format(h),
    )

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)
    r.addInputPercentage("test", 100)

    t_dict = {
        "diameter": 3,
        "angle": 180.0,
        "height": 48.81184246332812,
        "external": False,
        "chamber": None,
    }
    logAssert(r.inputs["test"].infos == t_dict, "Dicitonaries do not match")

    # Test the input is a the right place (closed top)
    h = np.array(r.inputs["test"].height)
    logAssert(
        np.isclose(h, 48.81, 1e-2),
        "Input: default input at the wrong place (closed top) {}".format(h),
    )

    # Change angle of input, and check it's at the right place
    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r.addInputPercentage("test", angle=230)

    t_dict = {
        "external": False,
        "diameter": 3,
        "height": 45.04822038391718,
        "angle": 229.99999999999997,
        "chamber": None,
    }
    logAssert(r.inputs["test"].infos == t_dict, "Dictionaries do not match")

    h = np.array(r.inputs["test"].height)
    logAssert(
        np.isclose(h, 45.05, 1e-2),
        "Input: h input with angle 230° at the wrong place {}".format(h),
    )

    # Change height of input, and check it's at the right place
    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r.addInputPercentage("test", height_per=0)

    t_dict = {
        "chamber": None,
        "diameter": 3,
        "height": 10.5,
        "angle": 180.0,
        "external": False,
    }
    logAssert(r.inputs["test"].infos == t_dict, "Dictionaries do not match")

    h = np.array(r.inputs["test"].height)
    logAssert(
        np.isclose(h, 10.5, 1e-2),
        "Input: h input with height_per=0 at the wrong place {}".format(h),
    )


def test_add_output():

    """Test that outputs are properly added to a reactor"""

    l.debug("Testing add output feature")

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Check exception is raised when negative value for output height, or
    # if height > 100%
    with pytest.raises(ValueError):
        r.addOutputPercentage("new", height_per=-10)
        l.error("Output: no exception raised when height_per < 0")
    with pytest.raises(ValueError):
        r.addOutputPercentage("new", height_per=110)
        l.error("Output: no exception raised height_per > 100")

    # Add an output with default params
    r.addOutputPercentage("test")

    t_dict = {
        "diameter": 3,
        "external": False,
        "height": 45.04822038391718,
        "chamber": None,
        "angle": 180.0,
    }
    logAssert(r.outputs["test"].infos == t_dict, "Dictionaries do not match")

    # After adding an input, reactor.cad still has the right type
    logAssert(type(r.cad) is solid.objects.translate, "Output: wrong type for reactor")

    # Test the input is a the right place (open top)
    h = np.array(r.outputs["test"].height)
    logAssert(
        np.isclose(h, 45.05, 1e-2),
        "Output: h default output at the wrong place (open top) {}".format(h),
    )

    r = rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND)
    r.addOutputPercentage("test", 100)

    t_dict = {
        "external": False,
        "diameter": 3,
        "chamber": None,
        "angle": 180.0,
        "height": 48.81184246332812,
    }
    logAssert(r.outputs["test"].infos == t_dict, "Dictionaries do not match")

    # Test the output is a the right place (closed top)
    h = np.array(r.outputs["test"].height)
    logAssert(
        np.isclose(h, 48.81, 1e-2),
        "Output: h default input at the wrong place (closed top) {}".format(h),
    )

    # Change angle of input, and check it's at the right place
    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r.addOutputPercentage("test", angle=230)

    t_dict = {
        "angle": 229.99999999999997,
        "diameter": 3,
        "external": False,
        "chamber": None,
        "height": 45.04822038391718,
    }
    logAssert(r.outputs["test"].infos == t_dict, "Dictionaries do not match")

    h = np.array(r.outputs["test"].height)
    logAssert(
        np.isclose(h, 45.05, 1e-2),
        "Output: h input with angle 230° at the wrong place {}".format(h),
    )

    # Change height of input, and check it's at the right place
    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r.addOutputPercentage("test", height_per=0)

    t_dict = {
        "chamber": None,
        "external": False,
        "angle": 180.0,
        "diameter": 3,
        "height": 10.5,
    }
    logAssert(r.outputs["test"].infos == t_dict, "Dictionaries do not match")

    h = np.array(r.outputs["test"].height)
    logAssert(
        np.isclose(h, 10.5, 1e-2),
        "Output: h input with height_per=0 at the wrong place {}".format(h),
    )


def test_addLuerTopInlet():

    """
    Test that creating a Luer top inlet works. Don't test createCustomTopInlet
    as this method already calls it
    """

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    # Creating Luer top inlet with open top must crash
    with pytest.raises(IncompatibilityError):
        r.addLuerTopInlet("test")
        l.error("Reactor: no exc raised top Luer + not custom top")

    # Create a reactor with custom top, add a Luer top inlet, and check
    # that inlet has proper values
    r = rea(20, rea.T_CUSTOM, rea.B_FLAT_IN_O)
    r.addLuerTopInlet("test")

    # Convert inlet to dict for comparison
    io = r.top_inlets["test"]
    dict_io = {
        "diameter": io.diameter,
        "length": io.length,
        "walls": io.walls,
        "x": io.x,
        "y": io.y,
    }
    compare = {"diameter": 5, "length": 7, "walls": 3, "x": 0, "y": 0}

    logAssert(dict_io == compare, "Luer top inlet not properly created")


def test_getHeightPercentage():

    """Test getting height percentage for InputOutput object works properly"""

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)
    r.addInputPercentage("test", height_per=50)

    height_per = r.getHeightPercentage(r.inputs["test"])

    logAssert(height_per == 50, "getHeightPercentage didn't return proper %")


def test_liftReactor():

    """
    Test the liftReactor method. Make sure infos is properly updated
    after lifting
    """

    l.debug("Testing liftReactor feature")

    r = rea(20, rea.T_CLOSED_ROUND_O, rea.B_ROUND)
    r.liftReactor(20)

    logAssert(
        np.isclose(r.infos["height"], 88.48, 1e-2),
        "reactor.infos: wrong height after lifting",
    )

    # Height without inlet should be the same since T_CLOSED_ROUND has no inlet
    logAssert(
        np.isclose(r.infos["height_wo_inlet"], 84.48, 1e-2),
        "reactor.infos: wrong height wo inlet after lifting",
    )

    logAssert(r.coo["z"] == 20, "reactor.coo: wrong z after lifting")


def test_expandVertically():

    """
    Test the expandVertically method. Make sure volume and height are
    updated after expansion
    """

    l.debug("Testing expandVertically feature")

    r = rea(20, rea.T_CLOSED_ROUND_O, rea.B_ROUND)
    r.expandVertically(20)

    logAssert(
        np.isclose(r.infos["height_wo_inlet"], 84.48, 1e-2),
        "expandVertically: wrong height after expansion",
    )

    logAssert(
        np.isclose(r.volume, 27.84, 1e-2),
        "expandVertically: wrong volume after expansion",
    )


def test_is_connected():

    l.debug("Testing is_connected")

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    r.addInputPercentage("new")

    # Simulate connection to input (simply switch a bool)
    r.inputs["new"].connected = True

    logAssert(r.isConnected() is True, "Reactor not connected")


def test_has_internal_input():

    l.debug("Testing if reactor has internal connected input")

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    logAssert(r.hasConnectedInternalInput() is False, "Reactor doesn't have any input")

    r.addInputPercentage("new")

    logAssert(
        r.hasConnectedInternalInput() is False,
        "Reactor: pb w internal, unconnected input",
    )

    r.inputs["new"].connected = True

    logAssert(
        r.hasConnectedInternalInput() is True, "Reactor: pb w internal, connected input"
    )

    r.inputs["new"].external = True

    logAssert(r.hasConnectedInternalInput() is False, "Reactor has an external input")


def test_has_internal_connected_output():

    l.debug("Testing if reactor has internal connected output")

    r = rea(20, rea.T_OPEN, rea.B_FLAT_IN_O)

    logAssert(
        r.hasInternalConnectedOutput() is False,
        "Reactor has internal but unconnected output",
    )

    r.outputs["default"].connected = True

    logAssert(
        r.hasInternalConnectedOutput() is True, "Reactor has internal connected output"
    )

    r = rea(20, rea.T_OPEN, rea.B_FLAT_EX_O)

    logAssert(r.hasInternalConnectedOutput() is False, "Reactor has external output")


def test_valid_stl(all_reactors: list):

    """
    Generate all possible shapes of reactor, and render the STL files.
    Then test the validity of each STL file:
    - Check if watertight (True if there is non non-manifold surfaces)
    - Check if valid volume
    - Check if valid winding
    """

    l.debug("Testing STLs validity")

    for couple in all_reactors:

        l.debug(
            "Building and rendering couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        # Build the reactor
        r = rea(20, couple[0], couple[1])

        # Add inputs to check for non-manifolds
        r.addInputPercentage("i1", 0)
        r.addInputPercentage("i2", 100)

        # Forge the name of the file
        name = "{} {}".format(couple[0], couple[1])
        name = name.replace(" ", "_")
        name = name.replace("/", "_")
        r.renderToFile(name + ".scad")

        # Render the reactor into a stl file
        cmd = sp.Popen(
            ["openscad", "-o", name + ".stl", name + ".scad"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )

        # Wait until rendering is finished
        out, err = cmd.communicate()

        # Check if rendering succeeded, crash the test otherwise
        if cmd.returncode != 0:
            l.error(
                "Failed to render STL for couple Top {}; Bottom: {}".format(
                    couple[0], couple[1]
                )
            )
            pytest.fail(
                "Failed to render STL for couple Top: {}; Bottom: {}".format(
                    couple[0], couple[1]
                )
            )

        # Generate the mesh from STL file
        mesh = trimesh.load_mesh(name + ".stl")

        logAssert(
            mesh.is_watertight,
            "Couple Top: {}; Bottom: {} has non-manifold surfaces".format(
                couple[0], couple[1]
            ),
        )

        logAssert(
            mesh.is_volume,
            "Couple Top: {}; Bottom: {} has a negative volume".format(
                couple[0], couple[1]
            ),
        )

        logAssert(
            mesh.is_winding_consistent,
            "Couple Top: {}; Bottom: {} has unconsistent winding".format(
                couple[0], couple[1]
            ),
        )

        # Remove files to not polute dir
        os.remove(name + ".scad")
        os.remove(name + ".stl")


if __name__ == "__main__":
    pass
