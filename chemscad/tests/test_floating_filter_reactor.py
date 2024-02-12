#!/usr/bin/python
# coding: utf-8

import pytest
import numpy as np
import itertools
import subprocess as sp
import trimesh
import os

from ccad.log import MyLog
from ccad.reactor import ReactorCAD as rea
from ccad.floating_filter_reactor import FloatingFilterReactorCAD as ffr
from ccad.exceptions import ConstraintError


l = MyLog("output_tests_floating_filter_reactor.log", mode="w")

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


def test_volume_constraints():

    l.debug("Testing top and bottom volume constraints")

    # Negative top volume
    with pytest.raises(ConstraintError):
        ffr(10, -1, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)
        l.error("No exception raised for negative top volume")

    # Negative bottom volume
    with pytest.raises(ConstraintError):
        ffr(-1, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)
        l.error("No exception raised for negative bottom volume")


def test_coherent_filter_value_properties():

    l.debug("Testing z filter coherence")

    t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)

    test_z_top_filter = t.z_bottom_filter + t.h_filter
    test_z_bottom_filter = t.z_top_filter - t.h_filter

    logAssert(
        t.z_top_filter == test_z_top_filter,
        "Failed: Test: {} Actual: {}".format(test_z_top_filter, t.z_top_filter),
    )

    logAssert(
        t.z_bottom_filter == test_z_bottom_filter,
        "Failed: Test: {} Actual: {}".format(test_z_bottom_filter, t.z_bottom_filter),
    )


def test_volumetric_units():

    l.debug("Testing volumes are in mL and not mm3")

    t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)

    logAssert(
        t.volume_bottom == 10, "Failed: Test: {} Actual: {}".format(10, t.volume_bottom)
    )

    logAssert(
        t.volume_bottom == 10, "Failed: Test: {} Actual: {}".format(20, t.volume_top)
    )


def test_d_h_filter_values():

    l.debug("Testing D and H filter values match when created")

    t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)

    logAssert(t.d_filter == 10, "Failed: Test: {} Actual: {}".format(10, t.d_filter))

    logAssert(t.h_filter == 10, "Failed: Test: {} Actual: {}".format(10, t.h_filter))

    t2 = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=15, h_filter=20)

    logAssert(t2.d_filter == 15, "Failed: Test: {} Actual: {}".format(15, t2.d_filter))

    logAssert(t2.h_filter == 20, "Failed: Test: {} Actual: {}".format(20, t2.h_filter))


def test_radius_raises_exception():

    l.debug("Testing setting r property raises error")

    # Check radius setting
    with pytest.raises(NotImplementedError):
        t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)
        t.r = 50
        l.error("Expected exception not thrown for setting radius")


def test_percentage_raises_exception():

    l.debug("Testing output and input percentage raises error")

    # Adding input percentage
    with pytest.raises(AttributeError):
        t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)
        t.addInputPercentage("TEST", 75)

    # Addint output percentage
    with pytest.raises(AttributeError):
        t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)
        t.addOutputPercentage("TEST", 50)


def test_volume_accuracy():

    l.debug("Testing volume = volume_top + volume_bottom")

    t = ffr(10, 20, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=10, h_filter=10)

    total_volume = t.volume_top + t.volume_bottom

    logAssert(
        t.volume == total_volume,
        "Calculated volume does not match Test: {} Actual: {}".format(
            t.volume, total_volume
        ),
    )


def test_io_percentage_bottom():

    l.debug("Testing accuracy of adding IO% @ bottom")

    t = ffr(6, 4, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=20, h_filter=3)

    # Input Bottom 0%
    l.debug("Testing input percentage bottom 0%")
    t.addInputPercentageBottom("I_BOTTOM_0", 0)
    logAssert("I_BOTTOM_0" in t.inputs.keys(), "Input 0%% failed to create")

    io1 = t.inputs["I_BOTTOM_0"]
    t_dict = {
        "height": 13.5,
        "diameter": 3,
        "chamber": "bottom",
        "angle": 180.0,
        "external": False,
    }

    logAssert(io1.infos == t_dict, f"Dictionaries do not match, got: {io1.infos}")

    # Input Bottom 100%
    l.debug("Testing input percentage bottom 100%")

    t.addInputPercentageBottom("I_BOTTOM_100", 100)
    logAssert("I_BOTTOM_100" in t.inputs.keys(), "Input 100%% failed to create")

    io2 = t.inputs["I_BOTTOM_100"]
    t_dict = {
        "external": False,
        "angle": 180.0,
        "diameter": 3,
        "chamber": "bottom",
        "height": 37.406769517776766,
    }

    logAssert(io2.infos == t_dict, f"Dictionaries do not match, got: {io2.infos}")

    # Output Bottom 0%
    l.debug("Testing Output percentage bottom 0%")
    t.addOutputPercentageBottom("O_BOTTOM_0", 0)
    logAssert("O_BOTTOM_0" in t.outputs.keys(), "Output 0%% failed to create")

    io3 = t.outputs["O_BOTTOM_0"]
    t_dict = {
        "chamber": "bottom",
        "external": False,
        "height": 13.5,
        "diameter": 3,
        "angle": 180.0,
    }

    logAssert(io3.infos == t_dict, f"Dictionaries do not match, got: {io3.infos}")

    # Output Bottom 100%
    l.debug("Testing Output percentage bottom 100%")
    t.addOutputPercentageBottom("O_BOTTOM_100", 100)
    logAssert("O_BOTTOM_100" in t.outputs.keys(), "Output 100%% failed to create")

    io4 = t.outputs["O_BOTTOM_100"]
    t_dict = {
        "diameter": 3,
        "external": False,
        "angle": 180.0,
        "chamber": "bottom",
        "height": 37.406769517776766,
    }

    logAssert(io4.infos == t_dict, f"Dictionaries do not match, got: {io3.infos}")


def test_io_percentage_top():

    l.debug("Testing accuracy of adding IO% @ top")
    t = ffr(6, 4, ffr.T_CLOSED_ROUND, ffr.B_FLAT_EX_O, d_filter=20, h_filter=3)

    # Input Top 0%
    l.debug("Testing input percentage top 0%")
    t.addInputPercentageTop("I_TOP_0", 0)
    logAssert("I_TOP_0" in t.inputs.keys(), "Input 0%% failed to create")

    io1 = t.inputs["I_TOP_0"]
    t_dict = {
        "diameter": 3,
        "external": False,
        "angle": 180.0,
        "height": 43.409769517776766,
        "chamber": "top",
    }

    logAssert(io1.infos == t_dict, f"Dictionaries do not match, got: {io1.infos}")

    # Input Top 100%
    l.debug("Testing input percentage top 100%")
    t.addInputPercentageTop("I_TOP_100", 100)
    logAssert("I_TOP_100" in t.inputs.keys(), "Input 100%% failed to create")

    io2 = t.inputs["I_TOP_100"]
    t_dict = {
        "height": 52.72794919629462,
        "chamber": "top",
        "diameter": 3,
        "angle": 180.0,
        "external": False,
    }

    logAssert(io2.infos == t_dict, f"Dictionaries do not match, got: {io2.infos}")

    # Output Top 0%
    l.debug("Testing output percentage top 0%")
    t.addOutputPercentageTop("O_TOP_0", 0)
    logAssert("O_TOP_0" in t.outputs.keys(), "Input 0%% failed to create")

    io3 = t.outputs["O_TOP_0"]
    t_dict = {
        "height": 43.409769517776766,
        "diameter": 3,
        "external": False,
        "chamber": "top",
        "angle": 180.0,
    }

    logAssert(io3.infos == t_dict, f"Dictionaries do not match, got: {io3.infos}")

    # Output Top 100%
    l.debug("Testing output percentage top 100%")
    t.addOutputPercentageTop("O_TOP_100", 100)
    logAssert("O_TOP_100" in t.outputs.keys(), "Input 100%% failed to create")

    io4 = t.outputs["O_TOP_100"]
    t_dict = {
        "external": False,
        "height": 52.72794919629462,
        "chamber": "top",
        "diameter": 3,
        "angle": 180.0,
    }

    logAssert(io4.infos == t_dict, f"Dictionaries do not match, got: {io4.infos}")


def test_h_r(all_reactors: list):

    """
    For a 20 mL reactor, check that h and R are right, depending on the
    shape of the reactor
    """

    l.debug("Testing h and r")

    for couple in all_reactors:

        # Pass threaded tops, radius is constrained by the filter
        if couple[0] in rea.THREADED_TOPS:
            continue

        l.debug(
            "Testing h and r for couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        r = ffr(6, 4, couple[0], couple[1], d_filter=20, h_filter=3)

        # Open top, round bottoms OR Closed tops, flat bottoms. Same h and r
        if (
            couple[0] == ffr.T_OPEN
            and couple[1] in ffr.ROUND_BOTS
            or couple[0] in ffr.CLOSED_TOPS
            and couple[1] in ffr.FLAT_BOTS
        ):

            logAssert(
                np.isclose(r._h, 42.23, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 8.43, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Open top, flat bottoms
        elif couple[0] == ffr.T_OPEN and couple[1] in ffr.FLAT_BOTS:
            logAssert(
                np.isclose(r._h, 47.84, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 8.43, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Closed tops, closed bottoms
        elif couple[0] in ffr.CLOSED_TOPS and couple[1] in ffr.ROUND_BOTS:
            logAssert(
                np.isclose(r._h, 36.61, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 8.43, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )


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

        # Pass threaded tops, radius is constrained by the filter
        if couple[0] in rea.THREADED_TOPS:
            continue

        l.debug(
            "Building and rendering couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        # Build the reactor
        r = ffr(6, 4, couple[0], couple[1], 20, 3)

        # Add inputs to check for non-manifolds
        r.addInputPercentageBottom("i1", 0)
        r.addInputPercentageBottom("i2", 100)
        r.addInputPercentageTop("i3", 0)
        r.addInputPercentageTop("i4", 100)

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
