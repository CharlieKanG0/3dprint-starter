"""<Assembly name> -- <which parts go together, on what>.

<What this scene answers: does the lid clear the latch, do the brackets land
on the rail, does the box fit where it has to...>

Copy to assemblies/<name>/<name>.py (the folder and file names must match).
API: common/assembly.py. Worked example: assemblies/shovel_on_rail/shovel_on_rail.py.

Run:  ../../venv/bin/python <name>.py                 (viewer, OCP_PORT)
      ./venv/bin/python scripts/view.py <name>        (own viewer + tab)
      ./venv/bin/python scripts/render.py <name>      (PNGs in exports/)
      ./venv/bin/python scripts/build_all.py <name>   (checks only)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *

from common.assembly import Assembly

# ---------------------------------------------------------------------------
# Parameters -- import shared numbers (rack, purchased items) from a common/
# module rather than retyping them; name every clearance you assert below.
# ---------------------------------------------------------------------------

# TODO

asm = Assembly("<name>")

# --- Reference geometry: what exists and isn't printed (rack, bought items,
# placeholders for parts not designed yet). Boxes are fine; dimension them.
# asm.ref("slat", Box(1200, 70, 30), at=(0, 0, -15), group="slats")

# --- Printed parts. asm.part() builds the part fresh from its current script
# (multi-variant parts: pass the exported STEP stem). Undo any print-orientation
# flip before placing. Placement kwargs: at=(x, y, z), rotate=(rx, ry, rz) in
# degrees, mirror=Plane.XZ -- applied mirror, then rotate, then move.
# bracket = asm.part("<part>")
# asm.add("bracket left", bracket, at=(-100, 0, 0), group="brackets")
# asm.add("bracket right", bracket, mirror=Plane.YZ, at=(100, 0, 0), group="brackets")

# ---------------------------------------------------------------------------
# Checks -- selectors are a group name, or an fnmatch glob on instance names
# ---------------------------------------------------------------------------

asm.check_overlaps()  # allow=[("bolt*", "bracket*")] for intended interference
# asm.assert_each_touches("brackets", "slats")      # each one actually sits on it
# asm.assert_gap("brackets", "<thing>", 5.0, None)  # min/max clearance, mm

asm.finish()
