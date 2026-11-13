"""Export + live-view helpers shared by every part script.

Part scripts call `export_part` and `show_part` instead of `export_step` and
`ocp_vscode.show` directly, so one place controls where a model goes:

  OCP_PORT=3940   push to the viewer on that port instead of the default
                  (3939). Needed when the VS Code viewer already holds 3939
                  and you run the standalone viewer beside it -- docs/viewer.md.
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


def show_part(*objects, **kwargs) -> None:
    """Push objects to the running OCP CAD Viewer. No-op in check and render mode."""
    if check_mode() or os.environ.get("PART_RENDER"):
        return
    from ocp_vscode import set_port, show

    port = os.environ.get("OCP_PORT")
    if port:
        set_port(int(port))
    show(*objects, **kwargs)
