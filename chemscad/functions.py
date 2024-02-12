#!/usr/bin/python
# coding: utf-8


import sys
import os
from typing import Tuple
from pathlib import Path

import chemscad.app_constants as cst


def getRightDirs() -> Tuple[str, str]:

    """Get the DATA_PATH and the resource_dir pathes.
    DATA_PATH is on the user side if CB is frozen"""

    root_path = os.path.dirname(os.path.abspath(__file__))

    if getattr(sys, "frozen", False):
        # resource_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        resource_dir = sys._MEIPASS
        DATA_PATH = cst.DATA_PATH
    else:
        resource_dir = root_path
        DATA_PATH = root_path

    return resource_dir, DATA_PATH


def getVersion() -> str:

    """This is a function JP copy/pasted from ChemBrows
    Therefore it needs to be rewritten, but it is never
    used in the main code."""

    resource_dir, DATA_PATH = getRightDirs()

    with open(
        os.path.join(resource_dir, "config/version.txt"), "r", encoding="utf-8"
    ) as version_file:

        version = version_file.read().strip()

    return version


def cleanRendersDir(logger):

    """
    Clean the renders directory. Will be called when ChemCAD is about to
    be closed
    https://stackoverflow.com/questions/185936/how-to-delete-the-contents-of-a-folder-in-python
    """

    logger.debug("Cleaning rendering directory")

    resource_dir, DATA_PATH = getRightDirs()

    folder = os.path.join(DATA_PATH, "renders")

    for file_del in os.listdir(folder):
        file_path = os.path.join(folder, file_del)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logger.debug(f"Removing {file_del} from render dir")
        except Exception as e:
            logger.error(e, exc_info=True)


if __name__ == "__main__":
    pass
