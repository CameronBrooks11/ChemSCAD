#!/usr/bin/python
# coding: utf-8

import pytest
import os
import sys
import shutil

from ccad.log import MyLog
from ccad.exceptions import *
from ccad.assembly import Assembly
from ccad.reactor import ReactorCAD as rea
from ccad.siphon import SiphonCAD as siph


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
def dummy_ass():

    """Dummy function for demo/test, create an assembly with 9 reactors"""

    ass = Assembly()

    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    r_2 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_2.addInputPercentage("input_test")
    ass.appendModule(r_2)

    con1 = siph(r_1, r_1.outputs["default"], r_2, r_2.inputs["input_test"])
    ass.appendModule(con1)

    r_3 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_3.addInputPercentage("input_test")
    ass.appendModule(r_3)

    con2 = siph(r_2, r_2.outputs["default"], r_3, r_3.inputs["input_test"])
    ass.appendModule(con2)

    r_4 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_4.addInputPercentage("input_test")
    ass.appendModule(r_4)

    con3 = siph(r_3, r_3.outputs["default"], r_4, r_4.inputs["input_test"])
    ass.appendModule(con3)

    r_5 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_5.addInputPercentage("input_test")
    ass.appendModule(r_5)

    con4 = siph(r_4, r_4.outputs["default"], r_5, r_5.inputs["input_test"])
    ass.appendModule(con4)

    r_6 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_6.addInputPercentage("input_test")
    ass.appendModule(r_6)

    con5 = siph(r_5, r_5.outputs["default"], r_6, r_6.inputs["input_test"])
    ass.appendModule(con5)

    r_7 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_7.addInputPercentage("input_test")
    ass.appendModule(r_7)

    con6 = siph(r_6, r_6.outputs["default"], r_7, r_7.inputs["input_test"])
    ass.appendModule(con6)

    r_8 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_8.addInputPercentage("input_test")
    ass.appendModule(r_8)

    con7 = siph(r_7, r_7.outputs["default"], r_8, r_8.inputs["input_test"])
    ass.appendModule(con7)

    r_9 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_9.addInputPercentage("input_test")
    ass.appendModule(r_9)

    con8 = siph(r_8, r_8.outputs["default"], r_9, r_9.inputs["input_test"])
    ass.appendModule(con8)

    ass.refresh()

    # ass.saveProject("Dummy.ccad")
    # print(ass)
    # ass.renderToFile("dummy_assembly.scad")
    # print(ass)

    return ass


def test_reactor_name_property(dummy_ass):

    l.debug("Testing assembly reactor names")

    ass = dummy_ass

    # Create target lists to compare to
    comparison = ["R{}".format(x) for x in range(1, 10)]

    # Get names for reactors in assembly
    names = ass.reactors_names.keys()

    for name, comp in zip(names, comparison):
        logAssert(name == comp, "Name {} does not match!".format(name))

    # Change name of first reactor
    ass.list_reactors[0].module_name = "Reactor test"

    names = list(ass.reactors_names.keys())

    logAssert(names[0] == "Reactor test", "Name does not match after renaming reactor")


def test_reactor_internal_id_property(dummy_ass):

    l.debug("Testing assembly reactor id")

    ass = dummy_ass

    # Create target lists to compare to
    comparison = ["R{}".format(x) for x in range(1, 10)]

    # Get IDs for reactors in assembly
    internal_ids = ass.reactors_internal_ids.keys()

    for internal_id, comp in zip(internal_ids, comparison):
        logAssert(internal_id == comp, "ID {} does not match!".format(internal_id))

    # Change name of first reactor
    ass.list_reactors[0].module_name = "Reactor test"

    internal_ids = list(ass.reactors_internal_ids.keys())

    logAssert(internal_ids[0] == "R1", "ID does not match after renaming reactor")


def test_connector_name_property(dummy_ass):

    l.debug("Testing assembly connector names")

    ass = dummy_ass

    # Create target lists to compare to
    comparison = ["S{}".format(x) for x in range(1, 9)]

    # Get names for connectors in assembly
    names = ass.connectors_names.keys()

    for name, comp in zip(names, comparison):
        logAssert(name == comp, "Connector {} does not match!".format(name))

    # Change name of first reactor
    ass.list_connectors[0].module_name = "Connector test"

    names = list(ass.connectors_names.keys())

    logAssert(
        names[0] == "Connector test", "Name does not match after renaming connector"
    )


def test_connector_internal_id_property(dummy_ass):

    l.debug("Testing assembly connector IDs")

    ass = dummy_ass

    # Create target lists to compare to
    comparison = ["S{}".format(x) for x in range(1, 9)]

    # Get names for connectors in assembly
    internal_ids = ass.connectors_internal_ids.keys()

    for internal_id, comp in zip(internal_ids, comparison):
        logAssert(
            internal_id == comp, "Connector {} does not match!".format(internal_id)
        )

    # Change name of first reactor
    ass.list_connectors[0].module_name = "Connector test"

    internal_ids = list(ass.connectors_internal_ids.keys())

    logAssert(internal_ids[0] == "S1", "ID does not match after renaming connector")


def test_get_module_id_from_name(dummy_ass):

    l.debug("Testing getting ID from module's name")

    ass = dummy_ass

    # Change name of first reactor
    ass.list_reactors[0].module_name = "Reactor test"

    logAssert(ass.getModuleIDFromName("Reactor test") == "R1", "Can't get ID from name")


def test_io_naming_properties(dummy_ass):

    l.debug("Testing Input and Output naming properties")

    ass = dummy_ass

    inputs = ["Input 'input_test' from R{}".format(x) for x in range(2, 10)]
    outputs = ["Output 'default' from R{}".format(x) for x in range(1, 10)]

    for test, target in zip(inputs, ass.inputs.keys()):
        logAssert(test == target, "{} is not present!".format(test))

    for test, target in zip(outputs, ass.outputs.keys()):
        logAssert(test == target, "{} is not present!".format(test))


def test_openscad_path(dummy_ass):

    l.debug("Testing openscad path")

    ass = dummy_ass

    if sys.platform == "linux":
        logAssert(ass.openscad_path == "openscad", "Openscad paths do not match!!")
    elif sys.platform == "osx" or sys.platform == "macosx":
        with pytest.raises(NotImplementedError):
            ass.openscad_path
    elif sys.platform == "win32":
        logAssert(
            "/ccad/ccad/bin/win/openscad." in ass.openscad_path,
            "Windows OpenSCAD path does not match!",
        )


def test_merge_stl(dummy_ass):

    l.debug("Testing merging of STLs")

    ass = dummy_ass
    ass.renders_dir = os.path.join("tests", "test_renders")
    ass.mergeSTLs()

    # final_target is the reference, compare the current rendering to it
    final_test = os.path.join("tests", "test_renders", "final_target.stl")

    # Forge path for the stl file just rendered
    final = os.path.join("tests", "test_renders", "final.stl")

    l.debug("Comparing test file to generated file")
    with open(final, "rb") as f1:
        with open(final_test, "rb") as f2:

            # Remove file being compared
            os.remove(final)

            content1 = f1.readlines()
            content2 = f2.readlines()

            logAssert(content1 == content2, "STL files do not match!")

    l.debug("Comparison passes")


def test_export_to_dict(dummy_ass):

    dico = dummy_ass.exportAssemblyToDict()

    logAssert(dico["turn_x"] == 2, "Wrong turn_x after export")
    logAssert(dico["turn_y"] == 2, "Wrong turn_y after export")

    logAssert(len(dico["list_reactors"]) == 9, "Wrong nbr of reactors after export")
    logAssert(len(dico["list_connectors"]) == 8, "Wrong nbr of reactors after export")

    logAssert(not dico["list_align_tops"], "List align tops: pb after export")
    logAssert(not dico["list_align_filters"], "List align filter: pb after export")


def test_save_project(dummy_ass):

    l.debug("Testing saving project")

    ass = dummy_ass
    ass.saveProject("test.ccad")

    proper_save = os.path.join("tests", "test_renders", "proper_save.ccad")

    with open(proper_save, "rb") as f1:
        content1 = f1.readlines()

    with open("test.ccad", "rb") as f2:
        os.remove("test.ccad")
        content2 = f2.readlines()

    logAssert(content1 == content2, "Saved Projects do not match!")


def test_load_project(dummy_ass):

    l.debug("Testing loading project")

    ass = dummy_ass

    proper_save = os.path.join("tests", "test_renders", "proper_save.ccad")
    test_ass = Assembly()
    test_ass.openProject(proper_save)

    logAssert(ass.turn_x == test_ass.turn_x, "Turn X does not match!")
    logAssert(ass.turn_y == test_ass.turn_y, "Turn Y does not match!")

    for test_r, target_r in zip(test_ass.list_reactors, ass.list_reactors):
        logAssert(test_r.infos == target_r.infos, "Reactors do not match!")

    for test_c, target_c in zip(test_ass.list_connectors, ass.list_connectors):
        logAssert(test_c.infos == target_c.infos, "Connectors do not match!")

    for test_at, target_at in zip(test_ass.list_align_tops, ass.list_align_tops):
        logAssert(test_at == target_at, "Align tops do not match!")

    for test_af, target_af in zip(test_ass.list_align_filters, ass.list_align_filters):
        logAssert(test_af == target_af, "Align filters do not match!")


def test_obj_must_be_rendered():

    l.debug("Testing object render checks")

    ass = Assembly()
    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)

    r_2 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_2.addInputPercentage("input_test")

    ass.appendModule(r_1)
    logAssert(ass._objMustBeRendered(r_1) is True, "Render Error, returned False")

    ass.appendModule(r_2)
    logAssert(ass._objMustBeRendered(r_2) is False, "Render Error, returned True")

    con1 = siph(r_1, r_1.outputs["default"], r_2, r_2.inputs["input_test"])
    ass.appendModule(con1)
    logAssert(ass._objMustBeRendered(r_1) is True, "render error, returned false")
    logAssert(ass._objMustBeRendered(r_2) is True, "Render error, returned false")


def test_obj_is_new():

    l.debug("Testing object is new")

    ass = Assembly()
    ass.renders_dir = os.path.join("tests", "test_renders")

    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    logAssert(ass._objIsNew(r_1) is True, "Obj is new but comparison failed")


def test_obj_has_changed():

    l.debug("Testing object has changed")

    ass = Assembly()
    ass.renders_dir = os.path.join("tests", "test_renders")

    # R1_has_changed is a scad file for a 20 mL reactor. Duplicate it as R1.scad
    # file. Mimics the process of rendering the object
    src = os.path.join(ass.renders_dir, "R1_has_changed.scad")
    dst = os.path.join(ass.renders_dir, "R1.scad")

    shutil.copyfile(src, dst)

    # Create a 21 mL reactor, to be compared to the 20 mL reactor in the scad file
    r_1 = rea(21, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    logAssert(
        ass._objHasChanged(r_1) is True, "Obj must be rendered but comparison failed"
    )

    # Clean render dir, remove R1.scad to not mess up other tests
    os.remove(dst)


def test_find_first_reactor_in_chain():

    l.debug("Testing assembly can find 1st reactor in chain")

    ass = Assembly()

    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    r_2 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_2.addInputPercentage("input_test")
    ass.appendModule(r_2)

    con1 = siph(r_1, r_1.outputs["default"], r_2, r_2.inputs["input_test"])
    ass.appendModule(con1)

    r_3 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_3.addInputPercentage("input_test")
    ass.appendModule(r_3)

    con2 = siph(r_2, r_2.outputs["default"], r_3, r_3.inputs["input_test"])
    ass.appendModule(con2)

    r_4 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_4.addInputPercentage("input_test")
    ass.appendModule(r_4)

    con3 = siph(r_3, r_3.outputs["default"], r_4, r_4.inputs["input_test"])
    ass.appendModule(con3)

    ass.refresh()

    # ass.renderToFile("test_first.scad")

    logAssert(
        ass._findFirstReactorInChain() is r_1,
        "Assembly didn't find the right 1st reactor in chain",
    )


def test_find_next_connector():

    l.debug("Testing assembly can find next connector")

    ass = Assembly()

    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    r_2 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_2.addInputPercentage("input_test")
    ass.appendModule(r_2)

    con1 = siph(r_1, r_1.outputs["default"], r_2, r_2.inputs["input_test"])
    ass.appendModule(con1)

    r_3 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_3.addInputPercentage("input_test")
    ass.appendModule(r_3)

    con2 = siph(r_2, r_2.outputs["default"], r_3, r_3.inputs["input_test"])
    ass.appendModule(con2)

    r_4 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_4.addInputPercentage("input_test")
    ass.appendModule(r_4)

    con3 = siph(r_3, r_3.outputs["default"], r_4, r_4.inputs["input_test"])
    ass.appendModule(con3)

    ass.refresh()

    # ass.renderToFile("test_first.scad")

    logAssert(
        ass._findNextConnector(r_2) is con2,
        "Assembly didn't find the right next connector for r_2",
    )


def test_reorder_connectors():

    l.debug("Testing assembly can reorder connectors")

    ass = Assembly()

    r_1 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    ass.appendModule(r_1)

    r_2 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_2.addInputPercentage("input_test")
    ass.appendModule(r_2)

    r_3 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_3.addInputPercentage("input_test")
    ass.appendModule(r_3)

    r_4 = rea(20, rea.T_OPEN, rea.B_ROUND_IN_O)
    r_4.addInputPercentage("input_test")
    ass.appendModule(r_4)

    con1 = siph(r_2, r_2.outputs["default"], r_3, r_3.inputs["input_test"])
    ass.appendModule(con1)

    con2 = siph(r_1, r_1.outputs["default"], r_2, r_2.inputs["input_test"])
    ass.appendModule(con2)

    con3 = siph(r_3, r_3.outputs["default"], r_4, r_4.inputs["input_test"])
    ass.appendModule(con3)

    ass._reorderConnectors()

    logAssert(
        ass.list_connectors == [con2, con1, con3],
        "Assembly didn't reorder connectors properly",
    )


if __name__ == "__main__":
    dummy_ass()
