---
name: design-part
description: Use whenever the user asks to design, make, model, or change a physical part, mount, bracket, holder, clamp, enclosure, or assembly for 3D printing in this repo -- including follow-ups that add a mechanism ("make it fold", "make it telescopic") -- before writing any geometry.
---

# Design a part: sketch first, then model

Follow `CLAUDE.md` "Workflow". This is the order, with the steps people skip in bold.

1. **Read every photo first.** The installed-state photo settles orientation.
   Say what you can see and what you can't.
2. **Ask before drawing.** Name the facts you need (what it holds, where it
   mounts, measurements, how it's used, materials, hardware) in one short
   list. If the user says "assume the rest", assume -- and write every
   assumed number into the sketch notes and the part header as ASSUMED.
3. **Sketch lettered candidates.** `./venv/bin/python scripts/new.py part <name>`
   creates `parts/<name>/layout.py`. Draw what exists, then each candidate
   layout as its own lettered schematic (A, B, C) at true scale, dimensions
   with sources in `notes()`. Run it.
4. **Look at the sketch yourself** (macOS: `qlmanage -t -s 1200 -o <dir> layout.svg`,
   then read the PNG). Fix overlapping labels and anything wrong. Open it for
   the user (in Orca: `orca tab create --url file://<abs path>/layout.svg`).
5. **Recommend one, then wait.** The user answers with a letter plus
   corrections. "Yes" to an either/or is not an answer -- ask which.
6. **Record it:** set `CONFIRMED = "<letter> + <corrections> -- user, <date>"`
   in `layout.py`. Never before they answer.
7. **Model it** from `parts/templates/part_template.py` (already copied by
   `new.py`): every dimension a named parameter, hardware from
   `common/hardware.py`, fits from `common/tolerances.py`, fit checks for
   anything that moves.
8. **Show it:** finish with a plain run of the part script -- the model opens
   in the viewer by itself (an Orca tab, VS Code, or the browser). Screenshot
   it, compare with the photos, and render (`scripts/render.py <name>`) on a
   first build.
9. **Report**: what was built, what the checks cover, every ASSUMED value,
   hardware to buy, what to print first to test.

A new mechanism halfway through (a different joint, a lock, a way to fold)
goes back to step 3 with lettered options for it.

Worked example of the whole loop: `parts/shower_mount/` (`layout.py`, then
`shower_mount.py`).
