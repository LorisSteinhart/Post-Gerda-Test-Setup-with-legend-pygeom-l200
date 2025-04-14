"""Construct the LEGEND-200/GERDA tank including the water volume."""


from __future__ import annotations

from math import pi

import pyg4ometry.geant4 as g4

from . cryo import cryo_radius, cryo_access_radius, cryo_access_wall, cryo_access_height, access_overlap

cryo_radius = cryo_radius / 10 # Umrechnung in cm 
cryo_access_radius = cryo_access_radius / 10
cryo_access_wall = cryo_access_wall / 10
cryo_access_height = cryo_access_height / 10
access_overlap = access_overlap / 10


tank_radius = 500
tank_wall_thickness = 0.7
tank_tub_height = 890
z_position_tank_top = tank_tub_height*10/2

def construct_tank(metal_steel: g4.Material, reg: g4.Registry) -> g4.LogicalVolume:
    tank_tub = g4.solid.Tubs(
        "tank_tub",
        0,
        tank_radius + tank_wall_thickness,
        tank_tub_height,
        0,
        2 * pi,
        reg,
        "cm"
    )
    tank_top = g4.solid.Tubs(
        "tank_top",
        0,
        tank_radius + tank_wall_thickness,
        tank_wall_thickness,
        0,
        2 * pi,
        reg,
        "cm"
    )
    tank_bottom = g4.solid.Tubs(
        "tank_bottom",
        0,
        tank_radius + tank_wall_thickness,
        tank_wall_thickness,
        0,
        2 * pi,
        reg,
        "cm"
    )
    tank_access_tub = g4.solid.Tubs(
        "tank_access_tub",
        0,
        cryo_access_radius + cryo_access_wall,
        14.6*2,
        0,
        2 * pi,
        reg,
        "cm",
    ) 


    
    tank1 = g4.solid.Union("tank1", tank_tub, tank_top, [[0, 0, 0], [0, 0, z_position_tank_top]], reg)
    tank2 = g4.solid.Union("tank2", tank1, tank_access_tub, [[0, 0, 0], [0, 0, z_position_tank_top]], reg)
    tank = g4.solid.Union("tank", tank2, tank_bottom, [[0, 0, 0], [0, 0, - z_position_tank_top]], reg)
    


    return g4.LogicalVolume(tank, metal_steel, "tank", reg)


def place_tank(
    tank_lv: g4.LogicalVolume,
    wl: g4.LogicalVolume,
    tank_displacement_z: float,
    reg: g4.Registry,
) -> g4.PhysicalVolume:
    tank_pv = g4.PhysicalVolume(
        [0, 0, 0], [0, 0, tank_displacement_z], tank_lv, "tank", wl, reg
    )
    tank_lv.pygeom_color_rgba = [0.192, 0.192, 0.192, 0]
    return tank_pv


def construct_water(water_material: g4.Material, reg: g4.Registry) -> g4.LogicalVolume:
    
    water = g4.solid.Tubs(
        "water",
        0,
        tank_radius, # because of overlaps
        tank_tub_height,
        0,
        2 * pi,
        reg,
        "cm"
    )
    water_tub = g4.solid.Tubs(
        "water_tub",
        0,
        cryo_access_radius + cryo_access_wall,
        14.6*2,
        0,
        2 * pi,
        reg,
        "cm",
    ) 
    water_with_tub = g4.solid.Union("water_with_tub", water, water_tub, [[0, 0, 0], [0, 0, + z_position_tank_top]], reg)

   
    return g4.LogicalVolume(water_with_tub, water_material, "water", reg)


def place_water(
    water_lv: g4.LogicalVolume,
    tank_lv: g4.LogicalVolume,
    tank_displacement_z: float,
    reg: g4.Registry,
) -> g4.PhysicalVolume:
    water_pv = g4.PhysicalVolume([0, 0, 0], [0, 0, 0], water_lv, "water", tank_lv, reg)
    water_lv.pygeom_color_rgba = [0, 0, 1, 0]
    return water_pv