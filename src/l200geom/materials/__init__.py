"""Subpackage to provide all implemented materials and their (optical) material properties."""

from __future__ import annotations

import legendoptics.fibers
import legendoptics.lar
import legendoptics.nylon
import legendoptics.pen
import legendoptics.tpb
import pint
import pyg4ometry.geant4 as g4

from .surfaces import OpticalSurfaceRegistry


class OpticalMaterialRegistry:
    def __init__(self, g4_registry: g4.Registry):
        self.g4_registry = g4_registry
        self.lar_temperature = 88.8

        self._elements = {}
        self._elements_cb = {}
        self._define_elements()

        self.surfaces = OpticalSurfaceRegistry(g4_registry)

    def get_element(self, symbol: str) -> g4.Element:
        if (symbol in self._elements_cb) and (symbol not in self._elements):
            self._elements[symbol] = (self._elements_cb[symbol])()
        return self._elements[symbol]

    def _add_element(self, name: str, symbol: str, Z: int, A: float) -> None:
        """Lazily define an element on the current registry."""
        assert symbol not in self._elements_cb
        self._elements_cb[symbol] = lambda: g4.ElementSimple(
            name=name, symbol=symbol, Z=Z, A=A, registry=self.g4_registry
        )

    def _define_elements(self) -> None:
        """Lazily define all used elements."""
        self._add_element(name="Hydrogen", symbol="H", Z=1, A=1.00794)
        self._add_element(name="Carbon", symbol="C", Z=6, A=12.011)
        self._add_element(name="Nitrogen", symbol="N", Z=7, A=14.01)
        self._add_element(name="Oxygen", symbol="O", Z=8, A=16.00)
        self._add_element(name="Fluorine", symbol="F", Z=9, A=19.00)
        self._add_element(name="Silicon", symbol="Si", Z=14, A=28.09)
        self._add_element(name="argon", symbol="Ar", Z=18, A=39.95)
        self._add_element(name="Chromium", symbol="Cr", Z=24, A=51.9961)
        self._add_element(name="Manganese", symbol="Mn", Z=25, A=54.93805)
        self._add_element(name="Iron", symbol="Fe", Z=26, A=55.845)
        self._add_element(name="Indium", symbol="In", Z=49, A=114.82)
        self._add_element(name="Cobalt", symbol="Co", Z=27, A=58.9332)
        self._add_element(name="Nickel", symbol="Ni", Z=28, A=58.6934)
        self._add_element(name="Copper", symbol="Cu", Z=29, A=63.55)
        self._add_element(name="Gadolinium", symbol="Gd", Z=64.7, A=157.25)
        # self._add_element(name="Water", symbol="H2O", geant4.MaterialPredefined("G4_WATER"))

        

    

    @property
    def liquidargon(self) -> g4.Material:
        """LEGEND liquid argon."""
        if hasattr(self, "_liquidargon"):
            return self._liquidargon

        self._liquidargon = g4.Material(
            name="LiquidArgon",
            density=1.390,  # g/cm3
            number_of_components=1,
            state="liquid",
            temperature=self.lar_temperature,  # K
            pressure=1.0 * 1e5,  # pascal
            registry=self.g4_registry,
        )
        self._liquidargon.add_element_natoms(self.get_element("Ar"), natoms=1)

        u = pint.get_application_registry().get()
        legendoptics.lar.pyg4_lar_attach_rindex(
            self._liquidargon,
            self.g4_registry,
        )
        legendoptics.lar.pyg4_lar_attach_attenuation(
            self._liquidargon,
            self.g4_registry,
            self.lar_temperature * u.K,
        )
        legendoptics.lar.pyg4_lar_attach_scintillation(
            self._liquidargon,
            self.g4_registry,
            triplet_lifetime_method="legend200-llama",
        )
        # added myself
        self._liquidargon.addConstProperty("SCINTILLATIONYIELD", 20000)

        if not hasattr(self._liquidargon, "SCINTILLATIONYIELD"):
            print("SCINTILLATIONYIELD is NOT defined")
        #until here

        return self._liquidargon

    @property
    def metal_steel(self) -> g4.Material:
        """Stainless steel of the GERDA cryostat."""
        if hasattr(self, "_metal_steel"):
            return self._metal_steel

        self._metal_steel = g4.Material(
            name="metal_steel",
            density=7.9,
            number_of_components=5,
            registry=self.g4_registry,
        )
        self._metal_steel.add_element_massfraction(self.get_element("Si"), massfraction=0.01)
        self._metal_steel.add_element_massfraction(self.get_element("Cr"), massfraction=0.20)
        self._metal_steel.add_element_massfraction(self.get_element("Mn"), massfraction=0.02)
        self._metal_steel.add_element_massfraction(self.get_element("Fe"), massfraction=0.67)
        self._metal_steel.add_element_massfraction(self.get_element("Ni"), massfraction=0.10)

        return self._metal_steel

    @property
    def metal_silicon(self) -> g4.Material:
        """Silicon."""
        if hasattr(self, "_metal_silicon"):
            return self._metal_silicon

        self._metal_silicon = g4.Material(
            name="metal_silicon",
            density=2.330,
            number_of_components=5,
            registry=self.g4_registry,
        )
        self._metal_silicon.add_element_natoms(self.get_element("Si"), natoms=1)

        return self._metal_silicon

    @property
    def metal_copper(self) -> g4.Material:
        """Copper structures.

        .. warning:: For full optics support, a reflective surface is needed, see
            :py:func:`surfaces.OpticalSurfaceRegistry.to_copper`.
        """
        if hasattr(self, "_metal_copper"):
            return self._metal_copper

        self._metal_copper = g4.Material(
            name="metal_copper",
            density=8.960,
            number_of_components=1,
            registry=self.g4_registry,
        )
        self._metal_copper.add_element_natoms(self.get_element("Cu"), natoms=1)

        return self._metal_copper

    @property
    def pmma(self) -> g4.Material:
        """PMMA for the inner fiber cladding layer."""
        if hasattr(self, "_pmma"):
            return self._pmma

        self._pmma = g4.Material(name="pmma", density=1.2, number_of_components=3, registry=self.g4_registry)
        self._pmma.add_element_natoms(self.get_element("H"), natoms=8)
        self._pmma.add_element_natoms(self.get_element("C"), natoms=5)
        self._pmma.add_element_natoms(self.get_element("O"), natoms=2)

        legendoptics.fibers.pyg4_fiber_cladding1_attach_rindex(
            self._pmma,
            self.g4_registry,
        )

        return self._pmma

    @property
    def pmma_out(self) -> g4.Material:
        """PMMA for the outer fiber cladding layer."""
        if hasattr(self, "_pmma_out"):
            return self._pmma_out

        self._pmma_out = g4.Material(
            name="pmma_cl2",
            density=1.2,
            number_of_components=3,
            registry=self.g4_registry,
        )
        self._pmma_out.add_element_natoms(self.get_element("H"), natoms=8)
        self._pmma_out.add_element_natoms(self.get_element("C"), natoms=5)
        self._pmma_out.add_element_natoms(self.get_element("O"), natoms=2)

        legendoptics.fibers.pyg4_fiber_cladding2_attach_rindex(
            self._pmma_out,
            self.g4_registry,
        )

        return self._pmma_out

    @property
    def ps_fibers(self) -> g4.Material:
        """Polystyrene for the fiber core."""
        if hasattr(self, "_ps_fibers"):
            return self._ps_fibers

        self._ps_fibers = g4.Material(
            name="ps_fibers",
            density=1.05,
            number_of_components=2,
            registry=self.g4_registry,
        )
        self._ps_fibers.add_element_natoms(self.get_element("H"), natoms=8)
        self._ps_fibers.add_element_natoms(self.get_element("C"), natoms=8)

        legendoptics.fibers.pyg4_fiber_core_attach_rindex(
            self._ps_fibers,
            self.g4_registry,
        )
        legendoptics.fibers.pyg4_fiber_core_attach_absorption(
            self._ps_fibers,
            self.g4_registry,
        )
        legendoptics.fibers.pyg4_fiber_core_attach_wls(
            self._ps_fibers,
            self.g4_registry,
        )

        return self._ps_fibers

    def _tpb(self, name: str, **wls_opts) -> g4.Material:
        t = g4.Material(
            name=name,
            density=1.08,
            number_of_components=2,
            state="solid",
            registry=self.g4_registry,
        )
        t.add_element_natoms(self.get_element("H"), natoms=22)
        t.add_element_natoms(self.get_element("C"), natoms=28)

        legendoptics.tpb.pyg4_tpb_attach_rindex(t, self.g4_registry)
        legendoptics.tpb.pyg4_tpb_attach_wls(t, self.g4_registry, **wls_opts)

        return t

    @property
    def tpb_on_fibers(self) -> g4.Material:
        """Tetraphenyl-butadiene wavelength shifter (evaporated on fibers)."""
        if hasattr(self, "_tpb_on_fibers"):
            return self._tpb_on_fibers

        self._tpb_on_fibers = self._tpb("tpb_on_fibers")

        return self._tpb_on_fibers

    @property
    def tpb_on_tetratex(self) -> g4.Material:
        """Tetraphenyl-butadiene wavelength shifter (evaporated on Tetratex)."""
        if hasattr(self, "_tpb_on_tetratex"):
            return self._tpb_on_tetratex

        self._tpb_on_tetratex = self._tpb("tpb_on_tetratex")

        return self._tpb_on_tetratex

    @property
    def tpb_on_nylon(self) -> g4.Material:
        """Tetraphenyl-butadiene wavelength shifter (in nylon matrix)."""
        if hasattr(self, "_tpb_on_nylon"):
            return self._tpb_on_nylon

        # as a base, use the normal TPB properties.
        self._tpb_on_nylon = self._tpb(
            "tpb_on_nylon",
            # For 30% TPB 70% PS the WLS light yield is reduced by 30% [Alexey]
            quantum_efficiency=0.7 * legendoptics.tpb.tpb_quantum_efficiency(),
            # the emission spectrum differs significantly.
            emission_spectrum="polystyrene_matrix",
        )

        # add absorption length from nylon.
        legendoptics.nylon.pyg4_nylon_attach_absorption(self._tpb_on_nylon, self.g4_registry)

        return self._tpb_on_nylon

    @property
    def tetratex(self) -> g4.Material:
        """Tetratex diffuse reflector.

        .. warning:: For full optics support, a reflective surface is needed, see
            :py:func:`surfaces.OpticalSurfaceRegistry.wlsr_tpb_to_tetratex`.
        """
        if hasattr(self, "_tetratex"):
            return self._tetratex

        self._tetratex = g4.Material(
            name="tetratex",
            density=0.35,
            number_of_components=2,
            registry=self.g4_registry,
        )
        self._tetratex.add_element_massfraction(self.get_element("F"), massfraction=0.76)
        self._tetratex.add_element_massfraction(self.get_element("C"), massfraction=0.24)

        return self._tetratex

    @property
    def nylon(self) -> g4.Material:
        """Nylon (from Borexino)."""
        if hasattr(self, "_nylon"):
            return self._nylon

        self._nylon = g4.Material(
            name="nylon",
            density=1.15,
            number_of_components=4,
            registry=self.g4_registry,
        )
        self._nylon.add_element_natoms(self.get_element("H"), natoms=2)
        self._nylon.add_element_natoms(self.get_element("N"), natoms=2)
        self._nylon.add_element_natoms(self.get_element("O"), natoms=3)
        self._nylon.add_element_natoms(self.get_element("C"), natoms=13)

        legendoptics.nylon.pyg4_nylon_attach_rindex(self._nylon, self.g4_registry)
        legendoptics.nylon.pyg4_nylon_attach_absorption(self._nylon, self.g4_registry)

        return self._nylon

    @property
    def pen(self) -> g4.Material:
        """PEN wavelength-shifter and scintillator."""
        if hasattr(self, "_pen"):
            return self._pen

        self._pen = g4.Material(
            name="pen",
            density=1.3,
            number_of_components=3,
            registry=self.g4_registry,
        )
        self._pen.add_element_natoms(self.get_element("C"), natoms=14)
        self._pen.add_element_natoms(self.get_element("H"), natoms=10)
        self._pen.add_element_natoms(self.get_element("O"), natoms=4)

        legendoptics.pen.pyg4_pen_attach_rindex(self._pen, self.g4_registry)
        legendoptics.pen.pyg4_pen_attach_attenuation(self._pen, self.g4_registry)
        legendoptics.pen.pyg4_pen_attach_wls(self._pen, self.g4_registry)
        legendoptics.pen.pyg4_pen_attach_scintillation(self._pen, self.g4_registry)

        return self._pen
    
    @property
    def water(self) -> g4.Material:
        """Create water material."""
        if hasattr(self, "_water"):
            return self._water
        
        self._water = g4.Material(
            name="water",
            density=1.000,  # g/cm³
            number_of_components=2,
            registry=self.g4_registry
        )
        self._water.add_element_massfraction(self.get_element("H"), massfraction=0.111)
        self._water.add_element_massfraction(self.get_element("O"), massfraction=0.889)

        return self._water
    
    @property
    def gadolinium_solution(self) -> g4.Material:
        """gadolinium solution for the center string"""
        if hasattr(self, "_gadolinium_solution"):
            return self._gadolinium_solution

        self._gadolinium_solution = g4.Material(
            name="gadolinium_solution",
            density=1,
            number_of_components=2,
            registry=self.g4_registry,
        )
        self._gadolinium_solution.add_element_massfraction(self.get_element("Gd"), massfraction=0.002)
        self._gadolinium_solution.add_material(g4.MaterialPredefined("G4_WATER"), fractionmass=0.998)

        return self._gadolinium_solution
    
    @property
    def gadolinium_loaded_PE(self) -> g4.Material:
        """gadolinium solution for the center string"""
        if hasattr(self, "_gadolinium_loaded_PE"):
            return self._gadolinium_loaded_PE
        
        self._gadolinium_loaded_PE = g4.Material(
            name="gadolinium_loaded_PE",
            density=0.94,  # typical density of polyethylene
            number_of_components=2,
            registry=self.g4_registry,
        )

        polyethylene = g4.Material(
            name="polyethylene",
            density=0.94,  # typical density of polyethylene
            number_of_components=2,
            registry=self.g4_registry,
        )
        polyethylene.add_element_natoms(self.get_element("C"), natoms=2)
        polyethylene.add_element_natoms(self.get_element("H"), natoms=4)


        gadolinium_oxide = g4.Material(
            name="Gadolinium(III) Oxide",
            density=7.41,  # Density of Gd₂O₃ in g/cm³
            number_of_components=2,
            registry=self.g4_registry,
        )    
        # Gd₂O₃ has 2 Gd atoms and 3 O atoms
        gadolinium_oxide.add_element_natoms(self.get_element("Gd"), natoms=2)
        gadolinium_oxide.add_element_natoms(self.get_element("O"), natoms=3)

        self._gadolinium_loaded_PE.add_material(gadolinium_oxide, fractionmass=0.002)
        self._gadolinium_loaded_PE.add_material(polyethylene, fractionmass=0.998)

        return self._gadolinium_loaded_PE

    @property
    def gd2o3_powder(self) -> g4.Material:
        """Define Gd2O3 Powder with density 7.407 g/cm³."""
        if hasattr(self, "_gd2o3_powder"):
            return self._gd2o3_powder

        # Material für Gd₂O₃ erstellen
        self._gd2o3_powder = g4.Material(
            name="Gadolinium(III) Oxide (Powder)",
            density=7.407,  # Dichte in g/cm³ bei 20 °C
            number_of_components=2,  # Gd und O
            registry=self.g4_registry,
        )

        # Elemente hinzufügen
        self._gd2o3_powder.add_element_natoms(self.get_element("Gd"), natoms=2)  # 2 Gd-Atome
        self._gd2o3_powder.add_element_natoms(self.get_element("O"), natoms=3)   # 3 O-Atome

        return self._gd2o3_powder

    @property
    def polyethylene(self) -> g4.Material:
        """Define pure polyethylene."""
        if hasattr(self, "_polyethylene"):
            return self._polyethylene

        # Polyethylen-Material erstellen
        self._polyethylene = g4.Material(
            name="polyethylene",
            density=0.94,  # typische Dichte von Polyethylen in g/cm³
            number_of_components=2,  # C und H
            registry=self.g4_registry,
        )

        # Elemente hinzufügen
        self._polyethylene.add_element_natoms(self.get_element("C"), natoms=2)  # C2
        self._polyethylene.add_element_natoms(self.get_element("H"), natoms=4)  # H4

        return self._polyethylene