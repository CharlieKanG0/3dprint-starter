"""Render a part or an assembly to PNG views with F3D -- no viewer server needed.

    ./venv/bin/python scripts/render.py <name> [--views iso,top,front,right] [--size 900]

<name> is a part (parts/<name>/<name>.py) or an assembly
(assemblies/<name>/<name>.py, common/assembly.py). The script runs headless in
render mode (PART_RENDER, see common/output.py), so its STEPs land in
exports/<name>/ and the committed .step files are untouched. Every STEP it
exports is rendered -- a multi-variant part gives one set of views per variant;
an assembly gives one coloured scene. PARAM_<NAME>=x overrides pass through, so
a sweep renders too. A part whose layout.py sets DOWN (the axis pointing down when installed) also
gets an "installed" view, drawn the way up it is used. Prints one PNG path per view (exports/<step>_<view>.png);
read them to check the shape against the reference photos. Needs `brew install f3d`.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
sys.path.insert(0, str(ROOT))

from common.project import find_script  # noqa: E402
from common.verify import layout_down  # noqa: E402

# build123d is Z-up. --camera-direction is where the camera looks; --camera-view-up
# keeps the horizon level. Views are labelled by the side of the part they show.
VIEWS = {
    "iso": ("-1,1,-1", "0,0,1"),    # camera at +X,-Y,+Z, looking down at the part
    "top": ("0,0,-1", "0,1,0"),
    "front": ("0,1,0", "0,0,1"),    # looking along +Y (sees the -Y face)
    "right": ("-1,0,0", "0,0,1"),   # looking along -X (sees the +X face)
}


def installed_view(down: str) -> tuple[str, str]:
    """The iso view turned so the part's installed "up" (opposite `down`, e.g. "-X") is up on screen:
    (camera direction, view-up), both in the part's Z-up frame."""
    axis = np.zeros(3)
    axis["XYZ".index(down.lstrip("+-").upper())] = -1.0 if down.startswith("-") else 1.0
    up, z = -axis, np.array([0.0, 0.0, 1.0])
    if up @ z > 0.5:
        rot = np.eye(3)
    elif up @ z < -0.5:
        rot = np.diag([1.0, -1.0, -1.0])           # upside down: half a turn about X
    else:                                          # a quarter turn taking +Z onto `up`
        k = np.cross(z, up)
        kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        rot = np.eye(3) + kx + kx @ kx
    fmt = lambda v: ",".join(f"{c + 0.0:g}" for c in v)  # noqa: E731  (+0.0: no "-0")
    return fmt(rot @ np.array([-1.0, 1.0, -1.0])), fmt(up)


def signed_axis(vec: str) -> str:
    """"0,0,1" -> "+Z": f3d's --up wants an axis name."""
    v = [float(c) for c in vec.split(",")]
    i = max(range(3), key=lambda j: abs(v[j]))
    return ("+" if v[i] > 0 else "-") + "XYZ"[i]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("part", help="part or assembly name")
    ap.add_argument("--views", default="iso,top,front,right")
    ap.add_argument("--size", type=int, default=900)
    args = ap.parse_args()

    if not shutil.which("f3d"):
        print("f3d not found -- brew install f3d", file=sys.stderr)
        return 2
    script = find_script(args.part)
    out_dir = EXPORTS / args.part
    # only this run's models get rendered: clear the old ones, but keep the rest of the folder
    # (a plain run's viewer page, view.html, lives there too)
    for old in [*out_dir.glob("*.step"), *out_dir.glob("*.glb"), *out_dir.glob("*.stl")] if out_dir.exists() else []:
        old.unlink()

    env = {**os.environ, "PART_RENDER": str(out_dir)}
    env.pop("PART_CHECK", None)
    run = subprocess.run([sys.executable, str(script)], env=env, cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout + run.stderr, file=sys.stderr)
        return run.returncode
    steps = sorted([*out_dir.glob("*.step"), *out_dir.glob("*.glb"), *out_dir.glob("*.stl")]) if out_dir.exists() else []
    if not steps:
        print(f"{script.name} exported nothing -- no export_part() / export_mesh() / Assembly.finish() call?", file=sys.stderr)
        return 1

    views = args.views.split(",")
    down = layout_down(script.parent)
    if down:
        VIEWS["installed"] = installed_view(down)
        if args.views == ap.get_default("views"):
            views.append("installed")
    for step in steps:
        rc = render(step, views, args.size)
        if rc:
            return rc
    return 0


def y_up(vec: str) -> str:
    """Z-up vector -> glTF's Y-up frame (build123d's export_gltf rotates the model the same way)."""
    x, y, z = vec.split(",")
    return ",".join((x, z, y[1:] if y.startswith("-") else f"-{y}"))


def render(step: Path, views: list[str], size: int) -> int:
    """`step` is a part's .step, an assembly's .glb (glTF: Y-up, colours + transparency), or a mesh part's .stl."""
    gltf = step.suffix == ".glb"
    for name in views:
        direction, up = VIEWS[name]
        world_up = up if name == "installed" else "0,0,1"
        if gltf:
            direction, up, world_up = y_up(direction), y_up(up), y_up(world_up)
        png = EXPORTS / f"{step.stem}_{name}.png"
        cmd = [
            "f3d", str(step), "--output", str(png), "--no-config",
            "--resolution", f"{size},{size}",
            "--up", signed_axis(world_up), "--camera-direction", direction, "--camera-view-up", up,
            "--axis", "--grid", "--verbose=quiet",  # "=": a separate "quiet" is read as a file
        ]
        # A STEP is drawn with its B-rep edges; a glTF is a triangle mesh, so --edges would
        # draw every triangle. --blending honours its alpha (see-through reference geometry).
        if gltf:
            cmd.append("--blending")
        elif step.suffix != ".stl":  # an STL is a triangle mesh too: --edges would outline every triangle
            cmd.append("--edges")
        if name != "iso":
            cmd.append("--camera-orthographic")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not png.exists():
            print(f"f3d failed for view {name}:\n{res.stdout}{res.stderr}", file=sys.stderr)
            return 1
        print(png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
