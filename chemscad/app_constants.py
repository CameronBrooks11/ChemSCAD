#!/usr/bin/python
# coding: utf-8

# Define constants for OpenSCAD's rendering
# https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Other_Language_Features#$fa,_$fs_and_$fn
fn = 0
fs = 0.5

#HPD - 21/11/19 - changing colours of modules in ChemCAD for consistency, more flat
colours_modules = {
    "Reactor": "#4285F4",
    "Filter reactor": "#F4B400",
    "Floating filter reactor": "#DB4437",
    "Double filter reactor": "#0F9D58",
    "S connector": "#dddddd",
    "Siphon connector": "#aaaaaa",
    "Tube connector": "#e4be9e",
    "Flow reactor": "#2ca25f",
}

colours_module_type_short = {
    "DS": colours_modules["Siphon connector"],
    "FR": colours_modules["Filter reactor"],
    "FW": colours_modules["Flow reactor"],
    "FFR": colours_modules["Floating filter reactor"],
    "DFR": colours_modules["Double filter reactor"],
    "R": colours_modules["Reactor"],
    "S": colours_modules["S connector"],
    "TC": colours_modules["Tube connector"],
}

if __name__ == "__main__":
    pass
