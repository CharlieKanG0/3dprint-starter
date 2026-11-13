# 3dprint — functional FDM parts, code-first CAD

Parametric functional parts (brackets, clamps, mounts, enclosures) designed
in `build123d` (Python) and FDM-printed. The printer (name, bed size, nozzle)
is described in **`common/printer.py`**; design against those numbers and
read it before checking bed fit. Default materials: PETG, ASA, or their CF
blends. Ask which one if a part's material isn't obvious.

When working in this repo, act as an expert mechanical engineer and Python
software architect: every dimension should be traceable to a reason (a
datasheet, a measured part, a standard), not eyeballed.

## Workflow

0. **Sketch before you model.** Draw the assembly as a labelled 2D schematic
   with `common/sketch.py`: `./venv/bin/python scripts/new.py part <name>`
   creates `parts/<name>/layout.py` (and the part script), draw what exists, the part and the hardware at
   true positions, add dimensions, state each number's source (measured /
   datasheet / assumed) in `notes()`, and run it to get `layout.svg`. Look at
   it yourself (convert it to PNG or open it in a browser) and check it before showing the user; add a side view when heights
   matter. Draw each candidate layout as its own lettered schematic. The
   user confirms by letter plus corrections; "yes" to an either/or is not a
   confirmation. Reference photos settle orientation, so read the
   installed-state photo before the first line of geometry.
1. Fill in `parts/<name>/<name>.py` (from `parts/templates/part_template.py`,
   created by `scripts/new.py` above).
2. Name every dimension as a parameter at the top of the script. No magic
   numbers in the geometry body — if a number appears twice, it belongs in
   the parameters section.
3. Build the part, add the assertions described below, then run it:
   ```
   ./venv/bin/python parts/<name>/<name>.py
   ```
   This exports `<name>.step` next to the script and pushes the model to
   the running OCP CAD Viewer (VS Code panel, or a browser tab via
   `scripts/view.py <name>`) — setup and commands in `docs/viewer.md`.
4. Render the first build (`./venv/bin/python scripts/render.py <name>` ->
   PNGs in `exports/`; read them) and compare it to the
   reference photos before refining. A wrong shape caught here costs one build; caught after the
   details are in, it costs all of them.
5. Once a part has been printed and test-fit, move its backlog line from
   "Backlog" to "Done" in `parts/BACKLOG.md`.

### Improving the workflow

Treat this workflow as a product. When a task hits friction (a wrong build, a
slow feedback loop, something explained twice), end by proposing one concrete
fix: a helper in `common/`, a check in `scripts/`, a template, or a doc. Keep
every fix generic, so it serves any future part and not just the one at hand.

### Environment

`./setup.sh` does everything (uv-managed Python 3.12 venv in `./venv`, the
standalone viewer in `./.viewer-venv`, F3D, the git hook) and is safe to
re-run. If an import fails, re-run it before debugging anything else.

**Do not add `cadquery` to this venv.** It and `build123d` pin incompatible
versions of the underlying `OCP` binding (`cadquery` wants `cadquery-ocp` in
`[7.9.3.1, 8.0)`, `build123d` wants `cadquery-ocp-novtk` in `[8.0, 8.1)`) —
installing both corrupts the shared `OCP` namespace and produces confusing,
unrelated-looking import errors. If a task genuinely needs cadquery, use a
separate venv.

### Viewing and checking

- Viewer (VS Code panel or a browser tab): `docs/viewer.md`.
- `./venv/bin/python scripts/build_all.py` rebuilds every part and assembly
  headless and fails on a broken assertion. `.githooks/pre-commit` runs it with `--staged`:
  only the parts a commit touches, or every part if `common/` or `scripts/`
  changed (`./setup.sh` enables it).
- Several parts together (a bracket on its rail, a box and its lid): write an assembly, `assemblies/<name>/<name>.py` from
  `assemblies/templates/assembly_template.py` (`common/assembly.py`). It
  places the parts with reference geometry and asserts overlaps, contact and
  clearances; `view.py`, `render.py` and `build_all.py` take its name like a
  part's. Add one as soon as a part has to fit something else -- see
  `docs/viewer.md`; worked example `assemblies/shovel_on_rail/`.
- `PARAM_<NAME>=x ./venv/bin/python parts/<name>/<name>.py` sweeps a
  parameter declared with `param()` (`common/params.py`); sweeps never
  overwrite the `.step`.

## House rules

- **Build cutting tools outside an open `BuildPart` block if you'll
  `.locate()` them before subtracting.** Constructing a primitive (e.g.
  `Cylinder(...)`) as a bare statement *inside* an open `with BuildPart()`
  context auto-adds it to the part at its *unlocated* position first,
  because the add happens at construction time, before any chained
  `.locate()` call. This silently fuses a stray blob into the part — it
  will not raise an error, and may not even be visible until you check
  volume or bounding box. Build the tool standalone above the `BuildPart`
  block, locate it there, then subtract it inside the block instead.
- **Verify hole/feature placement with the true OCC axis, never
  `Face.center()`.** `Face.center()` on a cylindrical face is only the axis
  for a full 360° revolution; for a partial or trimmed face (a slot's end
  cap) it can be off by exactly the radius, which looks plausible in review.
  `common/verify.py`'s `assert_holes` / `cylinder_axes` query the real axis.
- **Reuse `common/hardware.py` and `common/tolerances.py`** for bolt
  counterbores, heat-set insert holes, and clearance fits rather than
  retyping dimensions per part. If a part needs a size that isn't in those
  tables yet, add it there, not inline.
- **Chamfer bed-facing perimeter edges** (3mm, 45° is a reasonable default)
  on any part with a flat base against the print bed — it breaks the sharp
  corner that catches and lifts during printing, especially relevant for
  ASA/ASA-CF given their higher warp tendency vs. PETG.
- **Insert and counterbore dimensions are starting points, not
  guarantees.** Heat-set insert hole sizing varies meaningfully by brand and
  length; confirm against the actual insert's datasheet before cutting a
  part you intend to actually use, and update `common/hardware.py` with
  what you measure works.

## Print/material notes (PETG / ASA / CF blends)

These are ballpark starting points to design against, not measured
tolerances for your specific printer/filament combo — validate empirically
and fold corrections back into `common/tolerances.py` rather than into one
part's script.

- Minimum wall thickness: ≥1.2mm for a cosmetic/light-duty single wall,
  ≥2mm where the wall is actually load-bearing.
- Avoid unsupported overhangs steeper than ~45° from vertical; ASA/ASA-CF
  tolerate bridging and steep overhangs worse than PETG, so prefer
  reorienting or adding a chamfer/fillet lead-in over relying on supports
  for a part meant to be reprintable without manual cleanup.
- Holes print slightly undersized on FDM; if a dowel/pin/shaft needs a
  verified slip fit, test-print the hole and adjust via
  `common/tolerances.py`'s `FIT` table rather than hardcoding a one-off
  compensation in the part.
- ASA-CF and PETG-CF are both more brittle and more dimensionally stable
  than their unfilled counterparts — prefer them for parts that need flat,
  accurate mating faces (brackets, clamp bases); prefer unfilled ASA/PETG
  where some flex or impact resistance matters more than stiffness.

## Verify before calling a part done

Every part script ends with the checks in `common/verify.py`:
`assert_single_solid` (catches the stray-blob bug above), `assert_bbox`,
`assert_volume`, `assert_holes` (true axes), and `bed_fit(...)` printed so
the print orientation is on record. Prefer extending that module over
writing a check inline in one part.

## Parts backlog

Flat list at `parts/BACKLOG.md`, not a ticket tracker: most work here is a
single bounded part (parametrize, build, verify, print). Add an idea as a
line, move it to "Done" once printed and fit-checked.

## Worked example

`parts/shovel_mount/` + `assemblies/shovel_on_rail/` show the house style
end to end. Copy their patterns; don't build on them. The owner may delete
them.
