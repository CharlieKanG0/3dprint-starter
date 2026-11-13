"""<Part name> -- layout schematic: the "sketch before you model" record (CLAUDE.md step 0).

Copy next to the part script as parts/<name>/layout.py, fill it in, run it, open
layout.svg in a browser, screenshot it and check it yourself, then send it to the
user. They confirm by letter plus corrections. Draw each candidate layout as its
own Sketch; add a side/section Sketch (axes=("X", "Z")) when heights matter.

Rules for a good schematic:
  - true positions and true scale, in mm, in the part's own axes
  - every dimension that drives the design is drawn as a dim(...) with its value
  - every number gets a source in sk.notes(): measured / datasheet / ASSUMED
  - things that are unknown are written as unknown, not guessed and drawn

Run:     ../../venv/bin/python layout.py
Output:  layout.svg (next to this script)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from common.sketch import Sketch

# The user's decision, filled in ONLY after they answer: the letter they picked, their
# corrections, and the date. The part script refuses to build while this is empty
# (common/verify.py require_layout).
CONFIRMED = ""

# ---------------------------------------------------------------------------
# Dimensions (mm) -- same names as the part script where they overlap
# ---------------------------------------------------------------------------

# TODO: e.g. RAIL_W = 70.0, HOLE_PITCH = 30.0, ...

# ---------------------------------------------------------------------------
# Candidate A -- top view.   Roles: existing, feature, part, cutout, hardware, carried, guide
# ---------------------------------------------------------------------------

a = Sketch("<Part> -- layout A, top view (confirm before modelling)", size=200)

# TODO: draw what exists first, then the part, then the hardware, then dimensions:
#   a.rect(cx, cy, w, h, "existing", label="...")      a.slot(cx, cy, length, width, "feature", angle=90)
#   a.circle(cx, cy, r, "hardware")                    a.bar(p0, p1, width, "part")
#   a.dim(p0, p1, "270  what it is", offset=-30)       a.text(x, y, "label")
a.notes(
    "Sources: <dimension> = measured / datasheet / ASSUMED.",
    "Unknown: <anything still to measure>.",
)
a.save(Path(__file__).parent / "layout.svg")

# For a second candidate or a side view, make another Sketch and save it as
# layout_b.svg / layout_side.svg (a side view: Sketch("...", axes=("X", "Z"))).
