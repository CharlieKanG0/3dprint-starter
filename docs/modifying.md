# Changing a model you downloaded

You found a model on MakerWorld, Printables or Thingiverse. It's nearly right,
but you want it lighter, faster to print, or you want to add something: a
hole, a clamp, a bracket. This is how to do that with Claude. If you haven't
set up yet, start with **[Getting started](getting-started.md)**.

## Start with the file

Put the downloaded file (`.3mf` or `.stl`) somewhere Claude can see, like your
Downloads folder, and tell Claude the path and what you want. A link to the
model's page helps too: Claude reads the description and photos itself.

Two kinds of file:

- **`.3mf` from MakerWorld** also carries the creator's print settings (speeds,
  walls, infill) and the weight and time they got. Claude reads those.
- **`.stl`** is just the shape.

Check the licence on the model's page allows you to make a changed copy for
your own use. Claude shows the licence text it finds in the file.

## What Claude does first: a health check

Claude runs a command that reads the file and tells you, in plain words:

- **Size,** and whether it fits your printer's bed.
- **Whether it's a closed solid.** A downloaded model is a *mesh*: a skin of
  tiny triangles, not a CAD drawing. If the skin has gaps, adding or cutting
  things can't work until it's repaired. Most models are fine.
- **How the creator printed it,** and whether that was for a different printer
  than yours (the speeds and filament settings then don't carry over).
- **Where the plastic goes.** Many models are thin-walled, so almost all the
  plastic is wall, and changing the infill barely helps. The report says so,
  and shows estimated grams and time for fewer walls.

The numbers for weight and time are **estimates** (about 25% either way). Re-slice
in your slicer to get the real ones.

## Pick the lightest route that does the job

| You want | What happens |
| --- | --- |
| **Lighter or faster** | Usually no model change at all: re-slice with fewer walls and the right settings for your printer and plastic. Claude tells you what to set. |
| **Add or cut something:** a hole, a boss, a slot, a clamp | Claude **edits the model**. It keeps the creator's shape exactly and adds your change on top. |
| **Change its proportions:** make it wider, rework how it works | Claude **rebuilds it** as a proper CAD design, using the downloaded one as a guide. Slower, and gives you full control. |

The route is checked again once you pick a sketch. If the option you chose
replaces most of the original, Claude says so and offers the rebuild instead:
a rebuilt part is a CAD design you can keep changing, and it also gives you a
`.step` file. An edit of a download only ever gives a `.3mf` (see below).

## If the model gets edited

It works like designing a part, with one extra picture:

1. **Claude draws what exists.** Slices through the downloaded model, at true
   size, with its measurements. Nothing is guessed from the photos when the
   file itself has the answer.
2. **Claude sketches options,** A, B, C, for your change drawn onto those
   slices, turned the way the part sits when it is in use, with a "down" arrow (a
   download is saved the way it prints, which is often on its side). You answer
   with a letter plus any changes. Nothing is built until you do.
3. **Claude builds it,** checks it, and opens it in the viewer: **blue is the
   modified model, the transparent grey ghost is the original**, so you can see
   exactly what changed. (The mesh viewer loads its 3D engine from the internet, so
   it needs a connection.)
4. **You get a `.3mf`** with the geometry only. Claude opens it in your slicer
   (and shows you the file); pick your own printer, plastic and settings:
   nothing from the creator's profile comes along.

**Why a `.3mf` and not a `.step`?** A download is a mesh: a skin of
triangles, with no record of how it was drawn. An edit keeps that skin and
adds to it, so the result is a mesh too, and `.3mf` is the file format for
meshes. A `.step` is a CAD design with real surfaces and measurements you can
change later; writing a mesh into one doesn't turn it into a design. If you
want a `.step` (to keep changing the part in a CAD program), ask for a
**rebuild**: Claude redraws the part as a design, using the download as a
guide.

Claude's checks: the result is still one closed solid, the new hole really is open
and the new boss really is solid, the size is right, and it fits your bed.
A check is also run to prove it can fail, so a green tick means something.

## Tips

- **Say what it attaches to.** "Clamps a pole about 25 mm across" lets
  Claude pick sizes. Measure the real thing if you can.
- **Name the material.** It changes wall thickness, how much flex a clamp
  can have, and the weight estimate.
- **Keep the original download.** Claude copies it into your part's folder, so
  the change can be redone if you change your mind.

## For tinkerers

```sh
./venv/bin/python scripts/inspect_model.py ~/Downloads/model.3mf --material ASA   # the health check
./venv/bin/python scripts/new.py mod pole_clamp ~/Downloads/model.3mf         # start the edit
./venv/bin/python parts/pole_clamp/layout.py                                  # slices + your options
./venv/bin/python parts/pole_clamp/pole_clamp.py                          # build, check, view
./venv/bin/python scripts/check_meshmod.py                                        # self-test of the toolbox
```

The helpers are `common/meshmod.py` (load, measure, add, cut, check, export) and
`common/printplan.py` (the creator's settings and the estimate).
New geometry is drawn in build123d and fused to the mesh with `manifold3d`.
