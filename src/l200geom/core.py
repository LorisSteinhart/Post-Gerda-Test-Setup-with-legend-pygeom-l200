from __future__ import annotations

from importlib import resources

from legendmeta import LegendMetadata, TextDB
from pyg4ometry import geant4

from . import calibration, cryo, fibers, ga_string, hpge_strings, materials, top, wlsr, tank, sphericalDetector

import json, math
from pathlib import Path
from . hpge_strings import replaced_string_ids
from . sphericalDetector import sphericalDetector_radius
# Which pge_string should be replaced by the ga_stirng?
# replaced_string_id = "1"

lmeta = LegendMetadata()
configs = TextDB(resources.files("l200geom") / "configs")

# All
DEFINED_ASSEMBLIES = ["wlsr", "strings", "calibration", "fibers", "top", "tank", "ga_string"]
print(DEFINED_ASSEMBLIES)
# DEFINED_ASSEMBLIES = ["strings", "tank", "ga_string_gerda"]
print(DEFINED_ASSEMBLIES)
def construct(
    assemblies: list[str] = DEFINED_ASSEMBLIES,
    use_detailed_fiber_model: bool = False,
) -> geant4.Registry:
    """Construct the LEGEND-200 geometry and return the pyg4ometry Registry containing the world volume."""
    if set(assemblies) - set(DEFINED_ASSEMBLIES) != set():
        msg = "invalid geometrical assembly specified"
        raise ValueError(msg)

    reg = geant4.Registry()
    mats = materials.OpticalMaterialRegistry(reg)

    # Create the world volume
    world_material = geant4.MaterialPredefined("G4_Galactic")
    world = geant4.solid.Box("world", 20, 20, 21, reg, "m")
    world_lv = geant4.LogicalVolume(world, world_material, "world", reg)
    reg.setWorld(world_lv)

    # TODO: Shift the global coordinate system that z=0 is a reasonable value for defining hit positions.
    coordinate_z_displacement = 0

    # Create basic structure with tank and water.
    if "tank" in assemblies:
        tank_lv = tank.construct_tank(mats.metal_steel, reg)
        tank.place_tank(tank_lv, world_lv, coordinate_z_displacement, reg)

        water = geant4.MaterialPredefined("G4_WATER")
        water_lv = tank.construct_water(water, reg)
        tank.place_water(water_lv, tank_lv, coordinate_z_displacement, reg)


    # Create basic structure with argon and cryostat.
    cryostat_lv = cryo.construct_cryostat(mats.metal_steel, reg)
    cryo.place_cryostat(cryostat_lv, water_lv, coordinate_z_displacement, reg)

    lar_lv = cryo.construct_argon(mats.liquidargon, reg)
    lar_pv = cryo.place_argon(lar_lv, cryostat_lv, coordinate_z_displacement, reg)

    if "wlsr" in assemblies:
        # Place the WLSR into the cryostat.
        wlsr_lvs = wlsr.construct_wlsr(
            mats.metal_copper,
            mats.tetratex,
            mats.tpb_on_tetratex,
            reg,
        )
        wlsr_pvs = wlsr.place_wlsr(*wlsr_lvs, lar_lv, 3 * 180, reg) 
        wlsr.add_surfaces_wlsr(*wlsr_pvs[1:], lar_lv, mats, reg)
        # # Edited
        # wlsr_pvs = wlsr.place_wlsr(*wlsr_lvs, world_lv, 3 * 180, reg) 
        # wlsr.add_surfaces_wlsr(*wlsr_pvs[1:], world_lv, mats, reg)

    if "sphericalDetector" in assemblies:
        # Construct the sphericalDetector
        sphericalDetector_lv = sphericalDetector.construct_sphericalDetector(
            mats.liquidargon,  # Use liquid argon as the material
            reg                # Registry to track geometry elements
        )
        
        # Place the sphericalDetector inside the lar_lv volume
        x_pos_SD = -90
        y_pos_SD = -40
        radial_pos_SD = math.sqrt(x_pos_SD**2 + y_pos_SD**2)

        sphericalDetector.place_sphericalDetector(
            sphericalDetector_lv,  # Logical volume of the detector
            lar_lv,                # Logical volume of the liquid argon (LAr)
            x_pos_SD,              # Displacement in the X-direction
            y_pos_SD,              # Displacement in the Y-direction
            1000,                  # Displacement in the Z-direction
            reg                    # Registry to track placement
        )
        print(f"radial_pos_SD: {radial_pos_SD:.2f}") 

    if "sphericalDetectorArray" in assemblies:
        # Konstruktion des sphärischen Detektorarrays
        sphericalDetector_lv = sphericalDetector.construct_sphericalDetector(
            mats.liquidargon,  # Verwende flüssiges Argon als Material
            reg                # Registry zur Nachverfolgung der Geometrieelemente
        )
        
        # Parameter für die Anordnung der Detektoren
        string_id = "10"      # Radius des Strings
        distance_kette = 0.1     # Abstand der Detektorkette vom String
        z_pos = 1000.0           # Z-Position der Detektoren

        # Platzieren der Detektoren
        sphericalDetector.place_sphericalDetectorArray(
            sphericalDetector_lv,  # Logisches Volumen der sphärischen Detektoren
            lar_lv,                # Logisches Volumen des Flüssigargonbehälters (LAr)
            string_id,             # ID des Strings um den das Array gelegt wird
            sphericalDetector_radius,       # Radius der sphärischen Detektoren
            distance_kette,        # Abstand der Detektorkette vom String
            z_pos,                 # Z-Position der Detektoren
            reg                    # Registry zur Nachverfolgung der Platzierungen
        )
        
    channelmap = lmeta.channelmap("20230311T235840Z")

    # print(channelmap)

    # Place the germanium detector array inside the liquid argon
    hpge_string_config = configs.on("20230311T235840Z")

    # top of the top plate, this is still a dummy value!
    top_plate_z_pos = 1700

    # Orginal
    if "strings" in assemblies:
        hpge_strings.place_hpge_strings(channelmap, hpge_string_config, top_plate_z_pos, lar_lv, mats, reg)
    if "calibration" in assemblies:
        calibration.place_calibration_system(top_plate_z_pos, lar_lv, mats, reg)
    if "top" in assemblies:
        top.place_top_plate(top_plate_z_pos, lar_lv, mats, reg)
    if "ga_string" in assemblies:
        # Create basic structure with string and gadolinium.
        home_directory = Path.home()
        config_path = home_directory / "pyg4ometry/legend-pygeom-l200/src/l200geom/configs/l200-p03-r%-T%-all-config.json"

        # Lade die Konfiguration aus der JSON-Datei
        with config_path.open() as f:
            config_data = json.load(f)
        
        # Germanium Strings durch Gadolinium Strings ersetzen
        for idx, string_id in enumerate(replaced_string_ids):
            # Zugriff auf die Größen des Strings
            string_config = config_data["hpge_string"][string_id]
            print()
            radius_in_mm = string_config["radius_in_mm"]
            angle_in_deg = string_config["angle_in_deg"]
            minishroud_radius_in_mm = string_config["minishroud_radius_in_mm"]
            angle_in_rad = math.pi * angle_in_deg / 180
            x_pos = radius_in_mm * math.cos(angle_in_rad)
            y_pos = -radius_in_mm * math.sin(angle_in_rad)
            
            # Z-Position für den aktuellen String
            ga_string_z_pos = top_plate_z_pos / 2 - 10
            
            # Dynamischer Name-Suffix basierend auf dem Index oder der ID
            name_suffix = f"_{string_id}_side"
            
            # Konstruktion und Platzierung der Gadolinium-Strings
            string_lv_side = ga_string.construct_ga_string(
                mats.metal_steel, minishroud_radius_in_mm / 10, 100, reg, name_suffix=name_suffix
            )
            ga_string.place_ga_string(
                string_lv_side, lar_lv, x_pos, y_pos, ga_string_z_pos - 30, reg, name_suffix=name_suffix
            )
            
            ga_lv_side = ga_string.construct_gadolinium(
                mats.gadolinium_loaded_PE, minishroud_radius_in_mm / 10, 100, reg, name_suffix=name_suffix
            )
            ga_string.place_gadolinium(
                ga_lv_side, string_lv_side, 0, 0, 0, reg, name_suffix=name_suffix
            )

        # # Zugriff auf die Größen des String 
        string_config = config_data["hpge_string"]["3"]
        radius_in_mm = string_config["radius_in_mm"]
        angle_in_deg = string_config["angle_in_deg"]
        minishroud_radius_in_mm = string_config["minishroud_radius_in_mm"]
        rod_radius_in_mm = string_config["rod_radius_in_mm"]
        angle_in_rad = math.pi * angle_in_deg / 180

        ga_string_z_pos = top_plate_z_pos / 2 - 10
        x_pos_6 = radius_in_mm * math.cos(angle_in_rad + 0.5 * math.pi)
        y_pos_6 = -radius_in_mm * math.sin(angle_in_rad + 0.5 *math.pi)
        x_pos_12 = radius_in_mm * math.cos(angle_in_rad - 0.5 * math.pi)
        y_pos_12 = -radius_in_mm * math.sin(angle_in_rad - 0.5 *math.pi)

        # Side Gadolinium String 6
        string_lv_center = ga_string.construct_ga_string(mats.metal_steel, minishroud_radius_in_mm/10, 100, reg, name_suffix="_6_side")
        ga_string.place_ga_string(string_lv_center, lar_lv, x_pos_6, y_pos_6, ga_string_z_pos-30, reg, name_suffix="_6_side")

        ga_lv_center = ga_string.construct_gadolinium(mats.gadolinium_loaded_PE, minishroud_radius_in_mm/10, 100, reg, name_suffix="_6_side")
        ga_string.place_gadolinium(ga_lv_center, string_lv_center, 0, 0, 0, reg, name_suffix="_6_side")

        # Side Gadolinium String 12
        string_lv_center = ga_string.construct_ga_string(mats.metal_steel, minishroud_radius_in_mm/10, 100, reg, name_suffix="_12_side")
        ga_string.place_ga_string(string_lv_center, lar_lv, x_pos_12, y_pos_12, ga_string_z_pos-30, reg, name_suffix="_12_side")
    
        ga_lv_center = ga_string.construct_gadolinium(mats.gadolinium_loaded_PE, minishroud_radius_in_mm/10, 100, reg, name_suffix="_12_side")
        ga_string.place_gadolinium(ga_lv_center, string_lv_center, 0, 0, 0, reg, name_suffix="_12_side")

        # Center Gadolinium String
        string_lv_center = ga_string.construct_ga_string(mats.metal_steel, minishroud_radius_in_mm/10, 100, reg, name_suffix="_center")
        ga_string.place_ga_string(string_lv_center, lar_lv, 0, 0, ga_string_z_pos-30, reg, name_suffix="_center")

        ga_lv_center = ga_string.construct_gadolinium(mats.gadolinium_loaded_PE, minishroud_radius_in_mm/10, 100, reg, name_suffix="_center")
        ga_string.place_gadolinium(ga_lv_center, string_lv_center, 0, 0, 0, reg, name_suffix="_center")

    if "ga_string_gerda" in assemblies:
        gerda_ga_string_z_pos = top_plate_z_pos / 2 + 300 - 60
        h_Steel = 454 #mm
        d_Steel = 114 #mm
        h_Gd = 450 #mm
        d_Gd = 110 #mm
        h_PE = 420 #mm
        d_PE = 100 #mm

        # Gerda CaptureTubeHolder out of Steel 
        string_lv_gerda = ga_string.construct_ga_string(mats.metal_steel, (d_Steel-4)/10/2, (h_Steel-2)/10, reg, name_suffix="_gerda")
        ga_string.place_ga_string(string_lv_gerda, lar_lv, 0, 0, gerda_ga_string_z_pos, reg, name_suffix="_gerda")
        
        # Gerda CaptureTube Gd2O3 Powder
        ga_lv_gerda = ga_string.construct_gadolinium(mats.gd2o3_powder, d_Gd/10/2, h_Gd/10, reg, name_suffix="_gerda")
        ga_string.place_gadolinium(ga_lv_gerda, string_lv_gerda, 0, 0, 0, reg, name_suffix="_gerda")
        
        # Gerda CaptureModerator PE
        moderator_lv_gerda = ga_string.construct_moderator(mats.polyethylene, d_PE/10/2, h_PE/10, reg, name_suffix="_gerda")
        ga_string.place_moderator(moderator_lv_gerda, ga_lv_gerda, 0, 0, 0, reg, name_suffix="_gerda")

    # build fiber modules
    if "fibers" in assemblies:
        fiber_modules = lmeta.hardware.detectors.lar.fibers
        fibers.place_fiber_modules(
            fiber_modules, channelmap, top_plate_z_pos, lar_lv, lar_pv, mats, reg, use_detailed_fiber_model
        )
    
    # # Edited
    # if "strings" in assemblies:
    #     hpge_strings.place_hpge_strings(channelmap, hpge_string_config, top_plate_z_pos, world, mats, reg)
    # if "calibration" in assemblies:
    #     calibration.place_calibration_system(top_plate_z_pos, world, mats, reg)
    # if "top" in assemblies:
    #     top.place_top_plate(top_plate_z_pos, world, mats, reg)
    
    # # build fiber modules
    # if "fibers" in assemblies:
    #     fiber_modules = lmeta.hardware.detectors.lar.fibers
    #     fibers.place_fiber_modules(
    #         fiber_modules, channelmap, top_plate_z_pos, world_lv, world_lv, mats, reg, use_detailed_fiber_model
    #     )

    return reg
