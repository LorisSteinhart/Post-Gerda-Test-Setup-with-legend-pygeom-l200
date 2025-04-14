"""Construct the Gadolinium String."""


from __future__ import annotations

from math import pi

import pyg4ometry.geant4 as g4



string_wall_thickness = 0.2
# string_tub_height = 100
# gd_height = 70
string_radius = 5

def construct_ga_string(
    metal_steel: g4.Material, 
    string_radius: float,
    string_tub_height: float,
    reg: g4.Registry, 
    name_suffix: str = ""
) -> g4.LogicalVolume:
    string_top = g4.solid.Tubs(
        f"string_top{name_suffix}",
        0,
        string_radius + string_wall_thickness,
        string_wall_thickness,
        0,
        2 * pi,
        reg,
        "cm",
    )  
    string_tube = g4.solid.Tubs(
        f"string_tube{name_suffix}",
        0,
        string_radius + string_wall_thickness,
        string_tub_height,
        0,
        2 * pi,
        reg,
        "cm"
    )
    string_bottom = g4.solid.Tubs(
        f"string_bottom{name_suffix}",
        0,
        string_radius + string_wall_thickness,
        string_wall_thickness,
        0,
        2 * pi,
        reg,
        "cm",
    ) 
    string1 = g4.solid.Union(f"string1{name_suffix}", string_tube, string_top, [[0, 0, 0], [0, 0, string_tub_height * 10 / 2]], reg)
    string = g4.solid.Union(f"string{name_suffix}", string1, string_bottom, [[0, 0, 0], [0, 0, -string_tub_height * 10 / 2]], reg)
   

    return g4.LogicalVolume(string, metal_steel, f"string{name_suffix}", reg)


def place_ga_string(
    string_lv: g4.LogicalVolume,
    wl: g4.LogicalVolume,
    string_displacement_x: float,
    string_displacement_y: float,
    string_displacement_z: float,
    reg: g4.Registry,
    name_suffix: str = ""
) -> g4.PhysicalVolume:

    string_pv = g4.PhysicalVolume(
        [0, 0, 0], 
        [string_displacement_x, string_displacement_y, string_displacement_z], 
        string_lv, 
        f"string{name_suffix}", 
        wl, 
        reg
    )
    string_lv.pygeom_color_rgba = [0.75, 0.75, 0.75, 0.5]
    return string_pv


def construct_gadolinium(
    gadolinium_solution: g4.Material, 
    string_radius: float,    
    string_tub_height: float,
    reg: g4.Registry,
    name_suffix: str = ""
) -> g4.LogicalVolume:
    
    gadolinium = g4.solid.Tubs(
        f"gadolinium{name_suffix}",
        0,
        string_radius,
        string_tub_height,
        0,
        2 * pi,
        reg,
        "cm"
    )    
    return g4.LogicalVolume(gadolinium, gadolinium_solution, f"gadolinium{name_suffix}", reg)


def place_gadolinium(
    gadolinium_lv: g4.LogicalVolume,
    string_lv: g4.LogicalVolume,
    string_displacement_x: float,
    string_displacement_y: float,    
    string_displacement_z: float,
    reg: g4.Registry,
    name_suffix: str = ""
) -> g4.PhysicalVolume:
    gadolinium_pv = g4.PhysicalVolume([0, 0, 0], [string_displacement_x, string_displacement_y, string_displacement_z], gadolinium_lv, f"gadolinium{name_suffix}", string_lv, reg)
    gadolinium_lv.pygeom_color_rgba = [1, 0, 0, 0.5]
    return gadolinium_pv

def construct_moderator(
    moderator_material: g4.Material, 
    string_radius: float,    
    string_tub_height: float,
    reg: g4.Registry,
    name_suffix: str = ""
) -> g4.LogicalVolume:
    
    gadolinium = g4.solid.Tubs(
        f"moderator{name_suffix}",
        0,
        string_radius,
        string_tub_height,
        0,
        2 * pi,
        reg,
        "cm"
    )    
    return g4.LogicalVolume(gadolinium, moderator_material, f"moderator{name_suffix}", reg)

def place_moderator(
    moderator_lv: g4.LogicalVolume,
    gadolinium_lv: g4.LogicalVolume,
    string_displacement_x: float,
    string_displacement_y: float,    
    string_displacement_z: float,
    reg: g4.Registry,
    name_suffix: str = ""
) -> g4.PhysicalVolume:
    moderator_pv = g4.PhysicalVolume([0, 0, 0], [string_displacement_x, string_displacement_y, string_displacement_z], moderator_lv, f"moderator{name_suffix}", gadolinium_lv, reg)
    moderator_lv.pygeom_color_rgba = [0, 1, 0, 0.5]
    return moderator_pv