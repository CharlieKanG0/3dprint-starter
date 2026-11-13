"""Shovel on rail -- WORKED EXAMPLE of an assembly: two shovel_mount parts on a rail,
with the bolts and the shovel handle as reference geometry.

What this scene answers: do both mounts sit on the rail, does the handle drop
into the cradles with clearance on every side, and is nothing printed sharing
volume with anything else. Delete it together with parts/shovel_mount/.

API: common/assembly.py.

Run:  ./venv/bin/python scripts/view.py shovel_on_rail      (own viewer + tab)
      ./venv/bin/python scripts/render.py shovel_on_rail    (PNGs in exports/)
      ./venv/bin/python scripts/build_all.py shovel_on_rail (checks only)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *

from common.assembly import Assembly
from common.hardware import COUNTERBORE
from common.tolerances import FIT

# ---------------------------------------------------------------------------
# Parameters -- the shovel_mount numbers this scene depends on are repeated
# here on purpose and checked below; a real project would put shared numbers
# in a common/ module both scripts import.
# ---------------------------------------------------------------------------

RAIL = (600.0, 40.0, 20.0)  # length X, width Y, height Z; top face at Z=0
MOUNT_SPACING = 300.0  # centre to centre, along the rail
M6_SPACING = 60.0  # shovel_mount's bolt pitch
M6_SHANK_DIA = 6.0
M6 = COUNTERBORE["M6"]
BASE_THICKNESS = 10.0  # shovel_mount's base plate
HANDLE_DIA = 32.4  # shovel handle, measured
CRADLE_FLOOR = 4.0
HANDLE_AXIS_Z = BASE_THICKNESS + HANDLE_DIA / 2 + FIT["loose"].radial + CRADLE_FLOOR
HANDLE_LENGTH = 700.0

asm = Assembly("shovel_on_rail")

# --- Reference geometry (not printed)
asm.ref("rail", Box(*RAIL), at=(0, 0, -RAIL[2] / 2), group="rail")
asm.ref(
    "handle",
    Cylinder(HANDLE_DIA / 2, HANDLE_LENGTH, rotation=(0, 90, 0)),
    at=(0, 0, HANDLE_AXIS_Z),
    group="handle",
    alpha=0.5,
)
bolt_top = BASE_THICKNESS - M6.counterbore_depth  # head seats on the counterbore floor
bolt = Cylinder(M6_SHANK_DIA / 2, bolt_top + RAIL[2], align=(Align.CENTER, Align.CENTER, Align.MAX))

# --- Printed parts
mount = asm.part("shovel_mount")
for name, x in (("mount left", -MOUNT_SPACING / 2), ("mount right", MOUNT_SPACING / 2)):
    asm.add(name, mount, at=(x, 0, 0), group="mounts")
    for dx in (-M6_SPACING / 2, M6_SPACING / 2):
        asm.ref(f"bolt {name} {dx:+.0f}", bolt, at=(x + dx, 0, bolt_top), group="bolts")

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

asm.check_overlaps(allow=[("bolts", "rail")])  # the rail's channel isn't modelled
asm.assert_each_touches("mounts", "rail")
asm.assert_gap("handle", "mounts", 0.1, 1.0)  # loose fit: clears, but not sloppy
asm.assert_gap("bolts", "mounts", 0.2, None)  # shank clears its hole

asm.finish()
