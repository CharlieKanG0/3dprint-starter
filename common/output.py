"""Export + live-view helpers shared by every part script.

Part scripts call `export_part` and `show_part` instead of `export_step` and
`ocp_vscode.show` directly, so one place controls where a model goes:

  (default)       show_part opens the model itself: in Orca, the part's own
                  standalone viewer in a built-in browser tab (started/opened as
                  needed); else the VS Code panel on 3939; else a one-line skip.
                  See common/viewer.py.
  OCP_PORT=3940   push to the viewer on that port instead (scripts/view.py sets it).
  PARAM_<NAME>=x  a sweep override (common/params.py): the viewer still gets
                  the model, but the STEP export is skipped.
  PART_CHECK=1    headless check mode: skip the STEP export and the viewer.
                  Set by scripts/build_all.py (and the pre-commit hook) so a
                  check run never rewrites committed .step files or needs a
                  viewer.
  PART_NO_EXPORT=1  view without exporting: the viewer still gets the model but no
                  .step is written, so a viewing run leaves the tree clean.
                  Set by scripts/view.py.
  PART_RENDER=dir headless render mode: write the STEP into `dir` (not next to
                  the script) and skip the viewer. Set by scripts/render.py;
                  works together with PARAM_* sweeps.
"""

import os
import sys
from pathlib import Path

from build123d import export_step


def check_mode() -> bool:
    return bool(os.environ.get("PART_CHECK"))


def export_part(part, path: str | Path) -> bool:
    """Write `part` to a STEP file. Returns False (and writes nothing) in check mode
    or when any PARAM_* override is set -- a sweep must not overwrite the real model.
    In render mode (PART_RENDER=dir) the file goes to `dir` instead, always."""
    render_dir = os.environ.get("PART_RENDER")
    if render_dir:
        out = Path(render_dir)
        out.mkdir(parents=True, exist_ok=True)
        export_step(part, str(out / Path(path).name))
        return True
    if check_mode() or os.environ.get("PART_NO_EXPORT") or any(k.startswith("PARAM_") for k in os.environ):
        return False
    export_step(part, str(path))
    return True


def show_part(*objects, name: str | None = None, **kwargs) -> None:
    """Show objects in an OCP viewer -- in Orca, its own built-in browser tab, opened
    automatically (common/viewer.py has the order). No-op in check and render mode;
    skipped with a note, never a blocking prompt, when no viewer can be reached.

    `name` picks the viewer/tab (default: the running script's name). The camera is
    reset on every push so a changed model is never shown through a stale zoom; pass
    reset_camera=Camera.KEEP to keep it."""
    if check_mode() or os.environ.get("PART_RENDER"):
        return
    from common import viewer

    name = name or Path(sys.argv[0]).stem
    try:
        port = viewer.open_for(name)
    except viewer.ViewerError as e:
        print(f"show_part: {e} -- model not shown")
        return
    if port is None or not viewer.port_open(port):
        print(f"show_part: no OCP viewer running -- model not shown ({viewer.HOWTO})")
        return
    from ocp_vscode import Camera, set_port, show

    set_port(port)
    kwargs.setdefault("reset_camera", Camera.RESET)
    show(*objects, **kwargs)
    print(f"show_part: {name} -> http://localhost:{port}/viewer")
