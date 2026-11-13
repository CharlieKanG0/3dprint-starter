"""Standard hardware dimensions: counterbored bolts, heat-set inserts.

Clearance-hole and counterbore values are the usual ISO medium-fit numbers
for ISO 4762 socket-head cap screws (ISO 273 clearance class "medium",
counterbore diameter = nominal head diameter + ~1mm, counterbore depth =
nominal head height with no extra margin -- the screw head sits flush with
the counterbore floor).

Heat-set insert hole dimensions vary meaningfully by brand and length --
treat HEATSET as a starting point and confirm against the specific insert's
datasheet before cutting a part you intend to actually use. Update the
table with what you measure works.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CounterboreSpec:
    clearance_dia: float  # through-hole diameter for the bolt shank
    counterbore_dia: float  # recess diameter, clears the screw head
    counterbore_depth: float  # recess depth


COUNTERBORE: dict[str, CounterboreSpec] = {
    "M3": CounterboreSpec(clearance_dia=3.4, counterbore_dia=6.5, counterbore_depth=3.0),
    "M4": CounterboreSpec(clearance_dia=4.5, counterbore_dia=8.0, counterbore_depth=4.0),
    "M5": CounterboreSpec(clearance_dia=5.5, counterbore_dia=9.5, counterbore_depth=5.0),
    "M6": CounterboreSpec(clearance_dia=6.6, counterbore_dia=11.0, counterbore_depth=6.0),
    "M8": CounterboreSpec(clearance_dia=9.0, counterbore_dia=14.0, counterbore_depth=8.0),
}


@dataclass(frozen=True)
class HexNutSpec:
    across_flats: float  # wrench size, nominal
    thickness: float  # standard (non-nyloc) nut height


# ISO 4032 regular hex nuts. Pocket these with FIT["slip"] added to each side
# of the across-flats so the nut drops in but can't spin.
HEX_NUT: dict[str, HexNutSpec] = {
    "M5": HexNutSpec(across_flats=8.0, thickness=4.7),
    "M6": HexNutSpec(across_flats=10.0, thickness=5.2),
    "M8": HexNutSpec(across_flats=13.0, thickness=6.8),
    "M10": HexNutSpec(across_flats=16.0, thickness=8.4),
}

# ISO 10511 nyloc (prevailing-torque) nuts: same across-flats, taller.
NYLOC_NUT: dict[str, HexNutSpec] = {
    "M5": HexNutSpec(across_flats=8.0, thickness=5.0),
    "M8": HexNutSpec(across_flats=13.0, thickness=8.0),
}

# ISO 4017 hex-head bolt heads, for a pocket that captures the head so the bolt
# can't spin (thickness = head height).
HEX_HEAD: dict[str, HexNutSpec] = {
    "M5": HexNutSpec(across_flats=8.0, thickness=3.5),
    "M6": HexNutSpec(across_flats=10.0, thickness=4.0),
    "M8": HexNutSpec(across_flats=13.0, thickness=5.3),
}


@dataclass(frozen=True)
class HeatsetSpec:
    hole_dia: float
    hole_depth: float


HEATSET: dict[str, HeatsetSpec] = {
    "M3": HeatsetSpec(hole_dia=4.2, hole_depth=5.0),
    "M4": HeatsetSpec(hole_dia=5.6, hole_depth=6.0),
    "M5": HeatsetSpec(hole_dia=6.4, hole_depth=8.0),
    "M6": HeatsetSpec(hole_dia=8.1, hole_depth=9.5),
}
