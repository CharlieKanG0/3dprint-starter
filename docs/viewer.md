# Viewing a part

_Technical reference for the 3D viewer and renders. New here? You don't need
this page: the viewer opens by itself. See [Getting started](getting-started.md)._

Every part script ends with `show_part(...)` from `common/output.py`, which
puts the model on screen by itself (`common/viewer.py`), first match wins:

1. `OCP_PORT` set → that viewer (`scripts/view.py` sets it).
2. Inside Orca (`ORCA_WORKTREE_ID` + the `orca` CLI) → the part's own
   standalone viewer, started if needed, in a built-in browser tab (opened,
   or switched to).
3. The VS Code panel on 3939, if it's listening.
4. `./.viewer-venv` installed (`./setup.sh`) → the part's own standalone
   viewer in your default browser, opened once per viewer process
   (`VIEW_REOPEN=1` reopens it).
5. Otherwise a one-line note; it never waits on a prompt.

The camera is reset on every push, so a changed model is never shown through
an old zoom (`show_part(..., reset_camera=Camera.KEEP)` keeps it).

| Viewer | Use when |
| --- | --- |
| VS Code panel | You're working in VS Code. Default port 3939. |
| Standalone, in a browser tab | Any editor, several parts side by side. `scripts/view.py` runs it on its own port. |

`OCP_PORT=<port>` sends `show_part` to a viewer on that port instead of 3939.

## VS Code panel

The extension has **no interpreter setting of its own** — it uses VS Code's
general Python interpreter. Point it at `./venv/bin/python` (Cmd+Shift+P →
"Python: Select Interpreter"), then Cmd+Shift+P → "OCP CAD Viewer: Refresh
libraries list". `cat ~/.ocpvscode` shows a non-empty `services` entry once a
viewer is listening. `show_part` then updates the panel on every run.

That panel is not reachable from a browser: it doesn't answer plain HTTP.

## Standalone viewer (any browser)

In `ocp_vscode` 4.x the standalone server is a separate package, `ocp_viewer`.
`./setup.sh` installs it into its own venv, `./.viewer-venv` -- keep it out of
the project venv (see the `cadquery` warning in CLAUDE.md). Point
`OCP_VIEWER_PYTHON` at another interpreter to use a different install.

Each session, one viewer and tab per part (several parts side by side):

```
./venv/bin/python scripts/view.py <part>        # starts its viewer, opens its tab, pushes the model
./venv/bin/python scripts/view.py --list        # part -> port, up/down
./venv/bin/python scripts/view.py --stop <part|all>
```

`view.py` gives each part a stable port (first free from 3940, remembered in
`exports/viewers.json`), opens the tab in your default browser (or, if the
`orca` CLI is installed, an Orca tab) *before* pushing (a push to a viewer with no
tab connected is lost), and runs the script with `PART_NO_EXPORT=1` so no `.step`
is rewritten. Re-running it updates that part's tab in place (closed the tab? re-run with
`VIEW_REOPEN=1`). One viewer shows
one scene at a time; to see several parts together in one frame, write an
assembly (below) and `view.py` it like a part.

Manual equivalent, for a single viewer:

```
./.viewer-venv/bin/python -m ocp_viewer --port 3940 --axes0 --grid_xy   # leave running
open http://localhost:3940/viewer                                       # open the tab first
OCP_PORT=3940 ./venv/bin/python parts/<name>/<name>.py                      # then push a part
```

Use a port other than 3939 if the VS Code viewer is also running; whoever
started first owns 3939, and `lsof -iTCP:3939 -sTCP:LISTEN` shows who.

### Viewer keys

The viewer keeps its previous camera. In the tab: `5` iso, `8` top, `1` front,
`r` fit the model to the window. `t` toggles transparent faces.

## Rendering for the agent (F3D)

`./venv/bin/python scripts/render.py <name>` runs a part or assembly headless
(`PART_RENDER=exports/<name>/`, see `common/output.py`) and writes iso/top/front/right
PNGs to `exports/<step>_<view>.png` with F3D (`./setup.sh` installs it). No viewer server
needed; read the PNGs to check the shape against reference photos. A part with
several variants gets one set of views per exported STEP; an assembly renders as
one coloured scene with its reference geometry see-through (it exports glTF,
which carries colour and alpha -- F3D ignores STEP colours; its axis widget then
labels the up axis Y). `PARAM_<NAME>=x` overrides pass through. The committed
`.step` is never touched. Use the OCP viewer above for interactive orbit and sections.

## Assemblies: several parts in one scene

An assembly is `assemblies/<name>/<name>.py` (copy
`assemblies/templates/assembly_template.py`, or `scripts/new.py assembly <name>`;
the docstring of `common/assembly.py` has a complete example). It places printed parts and reference geometry (the
rack, bought items, placeholders) and asserts how they fit, with
`common/assembly.py`:

```python
asm = Assembly("<name>")
asm.ref("rail", Box(600, 40, 20), at=(0, 0, -10), group="rail")      # not printed
mount = asm.part("bracket")                                          # built fresh
asm.add("mount left", mount, at=(-150, 0, 0), group="mounts")
asm.add("mount right", mount, mirror=Plane.YZ, at=(150, 0, 0), group="mounts")
asm.check_overlaps()                          # every pair, true solid-boolean volumes
asm.assert_each_touches("mounts", "rail")
asm.assert_gap("handle", "mounts", 0.1, 1.0)
asm.finish()                                  # viewer / glTF in render mode / no-op in check mode
```

- `asm.part()` runs the part script into `exports/.assembly_cache/`, keyed on its
  source, `common/` and `PARAM_*` -- the scene always shows the current code,
  never a stale committed `.step`, and a sweep moves every part that reads the
  swept parameter.
- Selectors in checks are a group name or an `fnmatch` glob on instance names.
- Same tools as parts: `view.py <name>`, `render.py <name>`,
  `build_all.py <name>`. `build_all.py --staged` re-checks every assembly
  whenever any part changes. Nothing is written next to the script.

## Headless

`PART_CHECK=1` skips both the viewer and the STEP export. `scripts/build_all.py`
sets it.
