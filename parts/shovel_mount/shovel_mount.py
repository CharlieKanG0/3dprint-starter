"""
Shovel clamp base -- WORKED EXAMPLE of a finished part in this repo's style.
Read it next to parts/templates/part_template.py, then delete it (and
assemblies/shovel_on_rail/) whenever you like.

A base plate bolts flat onto an M6 channel/rail slot via two counterbored
M6 holes. A half-pipe cradle on top accepts the shovel's round handle.
Two clamping ears flank the cradle, each carrying an M4 hole sized for a
brass heat-set insert -- a separate strap/cap (not modeled here) bolts
across the top of the shovel into these ears to clamp it into the cradle.

Material:  ASA-CF -- flat mating face against the channel, wants dimensional
           stability more than impact resistance.
Printer:   see common/printer.py
Requires:  build123d (see requirements.txt; ./setup.sh installs it)
Run:       ../../venv/bin/python shovel_mount.py
Output:    shovel_mount.step (next to this script)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *

from common.hardware import COUNTERBORE, HEATSET
from common.output import export_part, show_part
from common.tolerances import FIT
from common.verify import assert_holes, assert_single_solid, assert_volume, bed_fit

# ---------------------------------------------------------------------------
# Parameters (all dimensions in mm)
# ---------------------------------------------------------------------------

# Shovel / cradle
SHOVEL_DIA = 32.4
SHOVEL_RADIUS = SHOVEL_DIA / 2
CRADLE_RADIUS = SHOVEL_RADIUS + FIT["loose"].radial  # hand-inserted, no press fit

# Base plate -- mounts flat against the channel slot
BASE_WIDTH = 40.0  # given
BASE_LENGTH = 90.0  # fits 60mm bolt spacing with 15mm edge margin each side
BASE_THICKNESS = 10.0

# M6 mounting bolts, into the channel slot
M6_SPACING = 60.0
M6_BOLT = COUNTERBORE["M6"]

# Cradle boss, sits on top of the base plate and carries the groove
CRADLE_FLOOR = 4.0  # material left under the groove
BOSS_HEIGHT = CRADLE_RADIUS + CRADLE_FLOOR  # groove axis lands flush with boss top
BOSS_LENGTH = 50.0  # shorter than BASE_LENGTH so it clears the M6 holes

# Clamping ears, carry M4 heat-set inserts for the clamp strap
EAR_LENGTH = 20.0  # along X
EAR_EXTENSION = 15.0  # how far the ear projects past the boss side, in Y
EAR_THICKNESS = 10.0  # in Z, measured down from the boss top
M4_INSERT = HEATSET["M4"]

# Drainage slot, straight down from the lowest point of the cradle groove,
# so water/mud doesn't pool in the channel
DRAIN_SLOT_WIDTH = 5.0
DRAIN_SLOT_LENGTH = 24.0  # overall end-to-end length, along the cradle's axis

# Printability: 45-degree chamfer on the base plate's bottom perimeter, so
# the bed-facing edge doesn't catch and lift during FDM printing
BASE_BOTTOM_CHAMFER = 3.0

assert M6_SPACING / 2 + M6_BOLT.counterbore_dia / 2 <= BASE_LENGTH / 2, (
    "M6 holes fall off the edge of the base plate"
)
assert BOSS_LENGTH / 2 < M6_SPACING / 2, "cradle boss overlaps the M6 holes"
assert 2 * CRADLE_RADIUS < BASE_WIDTH, "cradle groove is wider than the base plate"
assert DRAIN_SLOT_LENGTH < BOSS_LENGTH, "drainage slot longer than the cradle boss"
assert BASE_BOTTOM_CHAMFER < BASE_THICKNESS / 2, "chamfer too deep for the base plate"

boss_top_z = BASE_THICKNESS + BOSS_HEIGHT  # also the groove's cylindrical axis height
ear_y_center = BASE_WIDTH / 2 + EAR_EXTENSION / 2
groove_bottom_z = boss_top_z - CRADLE_RADIUS  # lowest point of the cradle channel

# Built standalone (outside the BuildPart context below) so it is never
# auto-added to the part -- it is only ever used as a subtraction tool.
groove_cutter = Cylinder(
    radius=CRADLE_RADIUS,
    height=BOSS_LENGTH + 10,
    rotation=(0, 90, 0),
).locate(Location((0, 0, boss_top_z)))

with BuildPart() as shovel_mount:
    # --- Base plate ---
    with BuildSketch(Plane.XY):
        Rectangle(BASE_LENGTH, BASE_WIDTH)
    extrude(amount=BASE_THICKNESS)

    # --- M6 mounting holes (counterbored), through the base plate ---
    with Locations((M6_SPACING / 2, 0, BASE_THICKNESS), (-M6_SPACING / 2, 0, BASE_THICKNESS)):
        CounterBoreHole(
            radius=M6_BOLT.clearance_dia / 2,
            counter_bore_radius=M6_BOLT.counterbore_dia / 2,
            counter_bore_depth=M6_BOLT.counterbore_depth,
            depth=BASE_THICKNESS,
        )

    # --- Cradle boss on top of the base plate ---
    with BuildSketch(Plane.XY.offset(BASE_THICKNESS)):
        Rectangle(BOSS_LENGTH, BASE_WIDTH)
    extrude(amount=BOSS_HEIGHT)

    # --- Clamping ears, either side of the cradle, flush with the boss top ---
    for sign in (1, -1):
        with BuildSketch(Plane.XY.offset(boss_top_z - EAR_THICKNESS)):
            with Locations((0, sign * ear_y_center)):
                Rectangle(EAR_LENGTH, EAR_EXTENSION)
        extrude(amount=EAR_THICKNESS)

    # --- Half-pipe groove for the shovel handle ---
    shovel_mount.part -= groove_cutter

    # --- M4 heat-set insert holes in each ear ---
    with Locations((0, ear_y_center, boss_top_z), (0, -ear_y_center, boss_top_z)):
        Hole(radius=M4_INSERT.hole_dia / 2, depth=M4_INSERT.hole_depth)

    # --- Drainage slot, straight down from the groove's lowest point ---
    with BuildSketch(Plane.XY):
        SlotOverall(DRAIN_SLOT_LENGTH, DRAIN_SLOT_WIDTH)
    extrude(amount=groove_bottom_z, mode=Mode.SUBTRACT)

    # --- 45-degree chamfer on the base plate's bottom perimeter ---
    bottom_face = shovel_mount.faces().sort_by(Axis.Z)[0]
    chamfer(bottom_face.outer_wire().edges(), length=BASE_BOTTOM_CHAMFER)

# ---------------------------------------------------------------------------
# Verify before exporting -- cheap checks that catch silent boolean bugs
# ---------------------------------------------------------------------------

assert_single_solid(shovel_mount.part)
assert_volume(shovel_mount.part, 55000, 60000)
assert_holes(shovel_mount.part, M6_BOLT.clearance_dia / 2, [(M6_SPACING / 2, 0), (-M6_SPACING / 2, 0)])
print(bed_fit(shovel_mount.part).summary())

export_part(shovel_mount.part, Path(__file__).parent / "shovel_mount.step")
print(f"shovel_mount  |  volume={shovel_mount.part.volume:.1f} mm^3")
print(f"Bounding box: {shovel_mount.part.bounding_box()}")

show_part(shovel_mount.part)
