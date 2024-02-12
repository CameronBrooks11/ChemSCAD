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
from ccad.filter_reactor import FilterReactorCAD as f_rea
from ccad.top_in import TopInlet
from ccad.exceptions import *


l = MyLog("output_tests_filter_reactor.log", mode="w")

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

    # Raise exception if simple round bottom selected
    with pytest.raises(NotImplementedError):
        f_rea(20, rea.T_CLOSED_ROUND, rea.B_ROUND, d_filter=20, h_filter=3)
        l.error("f_rea class: no exception raised when round bottom")

    # Raise excpetion when constrained radius is too small for filter
    with pytest.raises(ConstraintError):
        f_rea(10, rea.T_2_QUA_INCH, rea.B_FLAT_IN_O, d_filter=30, h_filter=3)
        l.error("f_rea class: no exp when constrained r too small")


def test_h_r_filter_too_small(all_reactors: list):

    """
    For a 20 mL reactor, check that h and R are right, depending on the
    shape of the reactor. Filter is too small for these tests
    """

    l.debug("Testing h and r")

    for couple in all_reactors:

        l.debug(
            "Testing h and r for couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        # Round bottom is passed, not possible
        if couple[1] == rea.B_ROUND:
            continue

        r = f_rea(20, couple[0], couple[1], d_filter=20, h_filter=3)

        # Closed top, round bottom (without or with inlet)
        if couple[0] in rea.CLOSED_TOPS and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 36.41, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 11.25, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        elif couple[0] == rea.T_OPEN and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 38.36, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 11.85, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Closed tops, flat bottoms (with or without inlet)
        elif couple[0] in rea.CLOSED_TOPS and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 37.97, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 11.73, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Open top, flat bottom (without or with inlet)
        elif couple[0] in rea.T_OPEN and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 40.41, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 12.49, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # 1/2 inch threaded top, flat bottom
        elif couple[0] == rea.T_2_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 63.02, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 10, "R {} is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_2_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 58.80, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 10, "R {} is wrong for couple {}".format(r._r, couple))

        # 3/4 inch threaded top, flat bottom
        elif couple[0] == rea.T_3_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 43.77, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 12, "R {} is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_3_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 37.11, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 12, "R {} is wrong for couple {}".format(r._r, couple))

        # 1 inch threaded top, flat bottom
        elif couple[0] == rea.T_4_QUA_INCH and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 24.62, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 16, "R {} is wrong for couple {}".format(r._r, couple))

        # 1/2 inch threaded top, round bottom
        elif couple[0] == rea.T_4_QUA_INCH and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 14.54, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(r._r == 16, "R {} is wrong for couple {}".format(r._r, couple))

        else:
            l.error("output: unrecognized couple: {}; {}".format(couple[0], couple[1]))
            pytest.fail(
                "Output test failed for unrecognized couple: {}; {}".format(
                    couple[0], couple[1]
                )
            )


def test_h_r_filter_not_too_small(all_reactors: list):

    """
    For a 10 mL reactor, check that h and R are right, depending on the
    shape of the reactor. Filter is NOT too small for these tests
    """

    l.debug("Testing h and r")

    for couple in all_reactors:

        # Pass simple round bottom, not possible at all
        if couple[1] == rea.B_ROUND:
            continue

        # Pass threaded tops, radius is constrained and 20mm filter is
        # too small
        if couple[0] in rea.THREADED_TOPS:
            continue

        l.debug(
            "Testing h and r for couple Top: {}; Bottom: {}".format(
                couple[0], couple[1]
            )
        )

        # Test exception is raised if volume is too small for round bottoms
        if couple[1] in rea.ROUND_BOTS:
            with pytest.raises(ImpossibleAction):
                r = f_rea(10, couple[0], couple[1], d_filter=20, h_filter=3)
                l.error(
                    "f_rea: no exp w/ round bot & filter not too small {}".format(
                        couple
                    )
                )
            continue

        r = f_rea(10, couple[0], couple[1], d_filter=20, h_filter=3)

        # Closed top, round bottom (without or with inlet)
        # This block will never be executed, round bottoms when filter is
        # not too small are not permitted
        if couple[0] in rea.CLOSED_TOPS and couple[1] in rea.ROUND_BOTS:
            pass

        # Open top, round bottoms
        elif couple[0] == rea.T_OPEN and couple[1] in rea.ROUND_BOTS:

            logAssert(
                np.isclose(r._h, 38.36, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 11.85, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Closed tops, flat bottoms (with or without inlet)
        elif couple[0] in rea.CLOSED_TOPS and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 42.23, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 8.43, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        # Open top, flat bottom (without or with inlet)
        elif couple[0] in rea.T_OPEN and couple[1] in rea.FLAT_BOTS:

            logAssert(
                np.isclose(r._h, 47.84, 1e-2),
                "h {} is wrong for couple {}".format(r._h, couple),
            )
            logAssert(
                np.isclose(r._r, 8.43, 1e-2),
                "R {} is wrong for couple {}".format(r._r, couple),
            )

        else:
            l.error("output: unrecognized couple: {}; {}".format(couple[0], couple[1]))
            pytest.fail(
                "Output test failed for unrecognized couple: {}; {}".format(
                    couple[0], couple[1]
                )
            )


def test_infos():

    """Make sure the dict 'infos' returns proper values"""

    l.debug("Testing filter reactor's infos")

    # Testing with filter too small
    r = f_rea(20, rea.T_OPEN, rea.B_ROUND_IN_O, 20, 3)

    logAssert(r.infos["z_top_filter"] == 12, "infos: wrong z_top_filter")
    logAssert(r.infos["z_bottom_filter"] == 9, "infos: wrong z_top_filter")
    logAssert(r.infos["h_filter"] == 3, "infos: wrong h_filter")
    logAssert(r.infos["d_filter"] == 20, "infos: wrong d_filter")
    logAssert(r.infos["filter_too_small"] is True, "infos: wrong filter_too_small")

    # Testing with filter NOT too small
    r = f_rea(10, rea.T_OPEN, rea.B_FLAT_IN_O, 20, 3)

    logAssert(r.infos["z_top_filter"] == 12, "infos 2): wrong z_top_filter")
    logAssert(r.infos["z_bottom_filter"] == 9, "infos 2): wrong z_top_filter")
    logAssert(r.infos["h_filter"] == 3, "infos 2): wrong h_filter")
    logAssert(r.infos["d_filter"] == 20, "infos 2): wrong d_filter")
    logAssert(r.infos["filter_too_small"] is False, "infos 2): wrong filter_too_small")


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

        # Round bottom is passed, not possible
        if couple[1] == rea.B_ROUND:
            continue

        # Build the reactor
        r = f_rea(20, couple[0], couple[1], 20, 3)

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
