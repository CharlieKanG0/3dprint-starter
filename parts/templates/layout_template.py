"""<Part name> -- layout schematic: the "sketch before you model" record (AGENTS.md step 0).

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
# corrections, and the date. Later decisions are appended with their dates, so it reads as the
# part's decision record. The part script refuses to build while this is empty
# (common/verify.py require_layout).
CONFIRMED = ""

# What this part is waiting on, in one line, kept current until it is printed and fit-checked: the
# user's letter, a measurement, a test print ("" when nothing). build_all prints it, so a new session
# sees where the part stopped. Mirror it as "Waiting on:" in the part's parts/BACKLOG.md line.
OPEN = "the user's letter"

# How the part is used: the part axis that points DOWN when it is installed ("-X", "+Z"...), or "" when
# orientation means nothing (a box, a spacer). Every Sketch(down=DOWN) is then drawn with down at the
# bottom of the page, and scripts/render.py adds an "installed" view.
DOWN = "-Z"

# ---------------------------------------------------------------------------
# Dimensions (mm) -- same names as the part script where they overlap
# ---------------------------------------------------------------------------

# TODO: e.g. RAIL_W = 70.0, HOLE_PITCH = 30.0, ...

# ---------------------------------------------------------------------------
# Candidate A -- top view.   Roles: existing, feature, part, cutout, hardware, carried, guide
# ---------------------------------------------------------------------------

a = Sketch("<Part> -- layout A, top view (confirm before modelling)", size=200, down=DOWN)

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
# layout_b.svg / layout_side.svg (a side view: Sketch("...", axes=("X", "Z"), down=DOWN)).
