"""<Part name> -- <one-line purpose>.

<Longer description: what it mounts to or mates with, and what it's for.>

Layout:    layout.py -> layout.svg (labelled schematic, confirmed with the
           user before modeling -- CLAUDE.md step 0; see common/sketch.py)

Material:  <PETG / ASA / PETG-CF / ASA-CF -- state which and why if non-obvious>
Printer:   see common/printer.py
Requires:  build123d (see requirements.txt; ./setup.sh installs it)
Run:       ../../venv/bin/python <part_name>.py
Output:    <part_name>.step (next to this script)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *

from common.hardware import COUNTERBORE, HEATSET
from common.output import export_part, show_part
from common.params import param  # noqa: F401  -- param("NAME", default) for sweepable values
from common.tolerances import FIT
from common.verify import (  # noqa: F401
    assert_bbox,
    assert_holes,
    assert_single_solid,
    assert_volume,
    bed_fit,
    require_layout,
)

# No geometry before the user has confirmed a layout (CLAUDE.md step 0). This fails
# until layout.py has been run and its CONFIRMED line records the user's choice.
require_layout(__file__)

# ---------------------------------------------------------------------------
# Parameters (all dimensions in mm)
# ---------------------------------------------------------------------------

# TODO: name every dimension here. No magic numbers in the geometry below --
# if a number shows up twice, it belongs in this section.


# ---------------------------------------------------------------------------
# Derived values + sanity assertions
# ---------------------------------------------------------------------------

# TODO: assert geometric relationships that must hold (e.g. a boss doesn't
# overlap a bolt hole, a groove fits within its housing) -- cheap insurance
# against a parameter edit silently breaking the part.


with BuildPart() as part:
    # TODO: build the part. See CLAUDE.md "House rules" before you do:
    #   - build cutting tools (Cylinder, Box, ...) OUTSIDE this `with` block
    #     if you need to `.locate()` them before subtracting -- constructing
    #     one as a bare statement inside an open BuildPart auto-adds it at
    #     its unlocated position first.
    pass


# ---------------------------------------------------------------------------
# Verify before exporting -- common/verify.py
# ---------------------------------------------------------------------------

assert part.part is not None, "the part is empty -- build it in the BuildPart block above"
assert_single_solid(part.part)
# TODO: once you know the expected numbers, add:
#   assert_bbox(part.part, (X, Y, Z))
#   assert_volume(part.part, lo, hi)
#   assert_holes(part.part, radius, [(x, y), ...])   # true OCC axes, not Face.center()
# and print bed_fit(part.part).summary() so the print orientation is on record.


# ---------------------------------------------------------------------------
# Export + live view -- common/output.py (see docs/viewer.md)
# ---------------------------------------------------------------------------

export_part(part.part, Path(__file__).parent / "<part_name>.step")
print(f"<part_name>  |  volume={part.part.volume:.1f} mm^3")
show_part(part.part)
