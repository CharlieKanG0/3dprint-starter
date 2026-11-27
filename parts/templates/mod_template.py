"""<Part name> -- <downloaded model>, modified: <the change>.

A modified copy of a downloaded model (a mesh, not a CAD solid). The downloaded shape stays
exactly as its designer made it; what this script adds or cuts is built here from named
parameters. Workflow: docs/modifying.md. Helpers: common/meshmod.py.

Source:    source/<source_file>  (title, designer and licence: see report.md)
Layout:    layout.py -> layout_*.svg (confirmed with the user before modelling -- AGENTS.md step 0)
Report:    report.md (size, condition, creator's print settings, filament estimate)
Material:  <PETG / ASA / PETG-CF / ASA-CF -- state which and why if non-obvious>
Printer:   see common/printer.py
Run:       ../../venv/bin/python <part_name>.py
Output:    <part_name>.3mf (geometry only; the slicer applies your print settings)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *  # new features are drawn in build123d, then converted to a mesh

from common.hardware import COUNTERBORE, HEATSET  # noqa: F401
from common.meshmod import (  # noqa: F401
    apply_changes,
    assert_mesh_bbox,
    assert_mesh_volume,
    assert_single_body,
    assert_solid_at,
    assert_void_at,
    assert_watertight,
    health,
    load_model,
    mesh_bed_fit,
    repair,
    test_piece,
    to_mesh,
)
from common.output import export_mesh, show_mesh
from common.params import param  # noqa: F401  -- param("NAME", default) for sweepable values
from common.tolerances import FIT  # noqa: F401
from common.verify import require_layout

# No geometry before the user has confirmed a layout (AGENTS.md step 0).
require_layout(__file__)

HERE = Path(__file__).parent
SOURCE = HERE / "source" / "<source_file>"

# ---------------------------------------------------------------------------
# Parameters (all dimensions in mm, in the model's own frame: centred in X/Y, bottom at Z=0)
# ---------------------------------------------------------------------------

# TODO: name every dimension of what you add or cut, each with its source (measured on the
# downloaded model in report.md / datasheet / ASSUMED). No magic numbers in the geometry below.

# ---------------------------------------------------------------------------
# The downloaded model
# ---------------------------------------------------------------------------

base = load_model(SOURCE)
if not health(base).usable:  # a gappy mesh cannot be edited; try the automatic repair, else fix it in Orca first
    base = repair(base)
assert_watertight(base)

# ---------------------------------------------------------------------------
# What changes. Build tools here, in the model's frame; `adds` are fused on, `cuts` removed
# (cuts also pass through anything added). Example:
#   adds = [Pos(0, 0, 10) * Cylinder(BOSS_R, BOSS_H)]
#   cuts = [Pos(0, 0, 10) * Cylinder(HOLE_R, BOSS_H * 3)]
# ---------------------------------------------------------------------------

adds: list = []
cuts: list = []

result = apply_changes(base, add=adds, cut=cuts)  # snap=0.01 when an addition continues a face of the original flush

# ---------------------------------------------------------------------------
# Verify before exporting (the mesh counterparts of common/verify.py)
# ---------------------------------------------------------------------------

assert_watertight(result)
assert_single_body(result)
# TODO: one probe per feature you added or cut, at its real position:
#   assert_void_at(result, (x, y, z))     # a hole is open air...
#   assert_solid_at(result, (x, y, z))    # ...a boss or an untouched wall is material
# and a POSITIVE CONTROL so the probe is known to see: the same point in `base` must read the
# opposite (assert_solid_at(base, (x, y, z)) where the new hole goes).
# assert_mesh_bbox(result, (X, Y, Z))
# assert_mesh_volume(result, lo, hi)
print(mesh_bed_fit(result).summary())

# ---------------------------------------------------------------------------
# Export + live view (grey = the original, for comparison)
# ---------------------------------------------------------------------------

export_mesh(result, HERE / "<part_name>.3mf")
# Where a fit is the question (a clamp, a snap, a peg), also export a short slice to print and try first:
# export_mesh(test_piece(result, "z", 10.0, at=<where the fitting feature is>), HERE / "<part_name>_test_piece.3mf")
print(f"<part_name>  |  volume={result.volume:.0f} mm^3 (was {base.volume:.0f})  |  {len(result.faces):,} triangles")
show_mesh(result, ghost=base)
