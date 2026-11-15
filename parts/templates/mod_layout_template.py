"""<Part name> -- layout schematics for a modified downloaded model: the "sketch before you model" record.

`scripts/new.py mod` copied this next to the part script. Running it draws slices through the
downloaded mesh (what exists, true size) into layout_existing_*.svg; then draw each candidate
change as its own lettered Sketch on top of a slice, run it, look at the SVGs yourself, show
them, and wait for the user's letter + corrections. See parts/templates/layout_template.py for
the rules of a good schematic, and CLAUDE.md step 0.

Run:     ../../venv/bin/python layout.py
Output:  layout_existing_top/front/side.svg, layout_a.svg, ... (next to this script)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from common.meshmod import draw_section, health, load_model, section_axes
from common.sketch import Sketch

# The user's decision, filled in ONLY after they answer: the letter they picked, their
# corrections, and the date. Later decisions are appended with their dates, so it reads as the
# part's decision record. The part script refuses to build while this is empty.
CONFIRMED = ""

# What this part is waiting on, in one line, kept current until it is printed and fit-checked: the
# user's letter, a measurement, a test print ("" when nothing). build_all prints it, so a new session
# sees where the part stopped. Mirror it as "Waiting on:" in the part's parts/BACKLOG.md line.
OPEN = "the user's letter"

HERE = Path(__file__).parent
base = load_model(HERE / "source" / "<source_file>")  # mm, centred in X/Y, bottom at Z=0
X, Y, Z = (float(v) for v in health(base).size)
BIG = max(X, Y, Z)
# A download is in the frame it PRINTS in, rarely the one it is USED in. Settle which way is down
# when installed, then turn the views so it is down on the page: quarter turns counter-clockwise per
# slice axis (e.g. {"z": 1} if the model's -X points down when installed). Coordinates stay the model's.
TURN: dict[str, int] = {}


def existing(axis: str, title: str, at: float | None = None) -> Sketch:
    """A slice through the downloaded model, drawn as 'existing', with its overall size dimensioned.
    axis "z" = top view (slice at height `at`), "y" = front view, "x" = side view; default `at` = the middle."""
    sk = Sketch(title, size=BIG * 1.4, axes=section_axes(axis), turn=TURN.get(axis, 0), down=axis in TURN)
    draw_section(sk, base, axis, at)
    lo, hi = base.bounds
    h, v = {"z": (0, 1), "y": (0, 2), "x": (1, 2)}[axis]
    sk.dim((lo[h], lo[v]), (hi[h], lo[v]), f"{hi[h] - lo[h]:.1f}", offset=-BIG * 0.12)
    sk.dim((lo[h], lo[v]), (lo[h], hi[v]), f"{hi[v] - lo[v]:.1f}", offset=BIG * 0.12)
    return sk


# ---------------------------------------------------------------------------
# What exists: slices through the downloaded mesh (measured from the file, not guessed)
# Measure a wall, a gap or a hole with meshmod.line_spans(base, point, direction): where a line through
# the model is inside material, e.g. [(-22.5, -18.5), (18.5, 22.5)] = a 37 mm bore with 4 mm walls.
# ---------------------------------------------------------------------------

for axis, view in (("z", "top"), ("y", "front"), ("x", "side")):
    sk = existing(axis, f"<Part> -- downloaded model, {view} slice through the middle")
    sk.notes("Outline = a slice through the downloaded mesh; sizes measured from the file (mm).",
             "The model is centred in X/Y with its lowest point at Z=0.")
    sk.save(HERE / f"layout_existing_{view}.svg")

# ---------------------------------------------------------------------------
# Candidate A -- draw the change on a slice.   Roles: existing, feature, part, cutout, hardware, carried, guide
# ---------------------------------------------------------------------------

a = existing("z", "<Part> -- layout A, top slice (confirm before modelling)")

# TODO: draw candidate A's addition on the slice at true position and size, with its dimensions:
#   a.circle(cx, cy, r, "part", label="clamp screw boss")    a.rect(cx, cy, w, h, "cutout")
#   a.dim(p0, p1, "12  wall to screw", offset=-20)
# Add a second slice (existing("y", ...)) when heights matter. Say where each number comes from.
a.notes(
    "Sources: <dimension> = measured on the mesh / datasheet / ASSUMED.",
    "Unknown: <anything still to measure>.",
)
a.save(HERE / "layout_a.svg")

# Candidate B, C, ...: copy the block above, change the title, save as layout_b.svg, layout_c.svg.
