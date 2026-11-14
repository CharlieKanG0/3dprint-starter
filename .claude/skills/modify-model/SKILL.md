---
name: modify-model
description: Use whenever the user wants to change, optimise or add to a model they DOWNLOADED (a .3mf or .stl from MakerWorld, Printables, Thingiverse, a file in Downloads) -- lighter, faster, less filament, a new hole, a clamp, a bracket -- before touching any geometry or settings. For a part designed from scratch use design-part.
---

# Modify a downloaded model: inspect, choose the route, sketch, edit, check

Follow `CLAUDE.md` ("Modifying a downloaded model") and `docs/modifying.md`. A downloaded model is a
**mesh**: build123d solids can't edit it, so the downloaded shape stays as is and your change is built
beside it and combined (`common/meshmod.py`). The sketch-first rule still applies in full.

1. **Read the file yourself.** `./venv/bin/python scripts/inspect_model.py <file> --material <their material>`.
   Also read the product page and photos if they gave a link or the 3MF names one (CLAUDE.md: fetch
   links yourself). Report in plain words: size and bed fit, closed solid or not, the creator's print
   settings (and whether they were for a different printer), where the plastic goes, the licence.
   Never quote the weight/time table as fact: it is an estimate (about +-25%) until re-sliced.
2. **Pick the route with the user, lightest first.** Then ask only what the route needs (material,
   what it holds or attaches to, which dimensions matter; offer to save a new real object to `things/`):
   - *Lighter / faster only* -> no geometry. Give the slicer settings for THEIR printer and material
     (walls, infill, speeds -- the report's table shows what each saves; keep >=3 walls where it carries
     load or takes a screw). Offer to re-estimate with other options.
   - *Add or cut a feature* -> the mesh edit below.
   - *Change its proportions* -> rebuild in build123d (`design-part`), using the report, the slices
     and `Mesher` / `detect_primitives` (build123d's STL reconstruction tutorial) as a guide.
3. **Not a closed solid?** `meshmod.repair` first; if still open, the user repairs it in Orca/Bambu
   Studio. Do not edit a gappy mesh.
4. **Start it:** `./venv/bin/python scripts/new.py mod <name> <file>` -- copies the download to
   `parts/<name>/source/`, writes `report.md`, and creates `layout.py` + `<name>.py` from the mod
   templates. Name it for the result (`pole_clamp`), not the download.
5. **Sketch lettered candidates.** Run `layout.py`: it draws slices of the real mesh as the
   "existing" structure (`layout_existing_*.svg`). Draw each candidate change as its own lettered
   sketch on a slice (`layout_a.svg`, ...) at true position, dimensions sourced in `notes()`: measured
   from the mesh / datasheet / ASSUMED. Look at them yourself (`qlmanage -t -s 1200 -o <dir> x.svg`),
   open them for the user, recommend one, **wait for their letter**, then set `CONFIRMED`.
   A new mechanism (a different clamp or lock) goes back to this step.
   **Draw it the way it is installed.** The file is in its print orientation; settle which way is down
   in use (ask, or read the installed photo) before the first candidate, then set `TURN` in `layout.py`
   so down is down on the page (`Sketch(turn=..., down=True)`). Sideways sketches mislabel lips as
   "shelves" and hide which way the item falls out -- the user and you both misread them.
   **The outer size is a design input.** Each candidate states on its sketch whether, where and by how
   much it changes the original's outer size, so the user's letter covers it: a download is often sized
   to fit a real space, and an addition is often meant to grow it.
6. **Edit:** fill in `<name>.py`: named parameters (each sourced), new geometry in build123d in the
   model's frame, `apply_changes(base, add=[...], cut=[...])`. Cuts also pass through additions.
   Fused additions must overlap the mesh by ~1 mm, never touch on a shared face (the same rule as
   CLAUDE.md "Never fuse faces that coincide").
7. **Verify:** `assert_watertight`, `assert_single_body`, a probe per feature (`assert_void_at` /
   `assert_solid_at`) with a positive control on the base, bbox, volume, `mesh_bed_fit`. Then a
   plain run (the viewer shows blue = modified, grey ghost = original), a `scripts/render.py <name>`,
   and read the pictures before reporting.
8. **Report:** what changed (numbers), every ASSUMED value, the checks, what to print first to test
   the fit, hardware to buy, and the slicer settings for their printer and material. The `.3mf` is
   geometry only: they pick their own profile. Licence caveat if the file's licence is restrictive.

Fix friction you meet in the helpers themselves, generically (`common/meshmod.py`,
`scripts/inspect_model.py`, the mod templates) -- never inside one part. `scripts/check_meshmod.py` is
the self-test; extend it when you extend the helpers.
