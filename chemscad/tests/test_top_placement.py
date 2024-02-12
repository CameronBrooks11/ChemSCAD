#!/usr/bin/python
# coding: utf-8

import pytest
import numpy as np
import itertools
import subprocess as sp
import trimesh
import os
import solid as solid

from ccad.log import MyLog
from ccad.tops_placement import get_positions
from ccad.top_in import TopInlet


l = MyLog("output_tests_top_placement.log", mode="w")

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


def test_get_positions():

    """
    Test the autoplacement of several top inlets. Check that the autoplacement
    function works for different numbers of inlets: 1, 2, 3, 4, 5
    """

    io1 = TopInlet(5, 7, 3, "custom", 0, 0)
    io2 = TopInlet(5, 7, 3, "custom", 0, 0)
    io3 = TopInlet(5, 7, 3, "custom", 0, 0)
    io4 = TopInlet(5, 7, 3, "custom", 0, 0)
    io5 = TopInlet(5, 7, 3, "custom", 0, 0)

    positions = get_positions(16, [io1])
    logAssert(positions == [(0, 0)], "Bad placement for 1 inlet")

    positions = get_positions(16, [io1, io2])
    logAssert(positions == [(-8.0, 0), (8.0, 0)], "Bad placement for 2 inlets")

    positions = get_positions(16, [io1, io2, io3])
    logAssert(
        positions
        == [
            (7.4256258422040737, 4.2871870788979622),
            (-7.4256258422040737, 4.2871870788979622),
            (-1.5750869800554844e-15, -8.5743741577959263),
        ],
        "Bad placement for 3 inlets",
    )

    positions = get_positions(16, [io1, io2, io3, io4])
    logAssert(
        positions
        == [
            (6.6274169979695206, 6.6274169979695188),
            (-6.6274169979695188, 6.6274169979695206),
            (-6.6274169979695214, -6.6274169979695188),
            (6.6274169979695179, -6.6274169979695214),
        ],
        "Bad placement for 4 inlets",
    )

    positions = get_positions(16, [io1, io2, io3, io4, io5])
    logAssert(
        positions
        == [
            (5.9230705305400022, 8.1524071919108607),
            (-5.9230705305400013, 8.1524071919108607),
            (-9.583729436176597, -3.1139424571808605),
            (-1.8511019130011733e-15, -10.076929469459998),
            (9.5837294361765952, -3.113942457180864),
        ],
        "Bad placement for 5 inlets",
    )


if __name__ == "__main__":
    pass
