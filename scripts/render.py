"""Render a part or an assembly to PNG views with F3D -- no viewer server needed.

    ./venv/bin/python scripts/render.py <name> [--views iso,top,front,right] [--size 900]

<name> is a part (parts/<name>/<name>.py) or an assembly
(assemblies/<name>/<name>.py, common/assembly.py). The script runs headless in
render mode (PART_RENDER, see common/output.py), so its STEPs land in
exports/<name>/ and the committed .step files are untouched. Every STEP it
exports is rendered -- a multi-variant part gives one set of views per variant;
an assembly gives one coloured scene. PARAM_<NAME>=x overrides pass through, so
a sweep renders too. Prints one PNG path per view (exports/<step>_<view>.png);
read them to check the shape against the reference photos. Needs `brew install f3d`.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
sys.path.insert(0, str(ROOT))

from common.project import find_script  # noqa: E402

# build123d is Z-up. --camera-direction is where the camera looks; --camera-view-up
# keeps the horizon level. Views are labelled by the side of the part they show.
VIEWS = {
    "iso": ("-1,1,-1", "0,0,1"),    # camera at +X,-Y,+Z, looking down at the part
    "top": ("0,0,-1", "0,1,0"),
    "front": ("0,1,0", "0,0,1"),    # looking along +Y (sees the -Y face)
    "right": ("-1,0,0", "0,0,1"),   # looking along -X (sees the +X face)
}


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
    if out_dir.exists():
        shutil.rmtree(out_dir)  # only this run's STEPs get rendered

    env = {**os.environ, "PART_RENDER": str(out_dir)}
    env.pop("PART_CHECK", None)
    run = subprocess.run([sys.executable, str(script)], env=env, cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout + run.stderr, file=sys.stderr)
        return run.returncode
    steps = sorted([*out_dir.glob("*.step"), *out_dir.glob("*.glb")]) if out_dir.exists() else []
    if not steps:
        print(f"{script.name} exported nothing -- no export_part() / Assembly.finish() call?", file=sys.stderr)
        return 1

    for step in steps:
        rc = render(step, args.views.split(","), args.size)
        if rc:
            return rc
    return 0


def y_up(vec: str) -> str:
    """Z-up vector -> glTF's Y-up frame (build123d's export_gltf rotates the model the same way)."""
    x, y, z = vec.split(",")
    return ",".join((x, z, y[1:] if y.startswith("-") else f"-{y}"))


def render(step: Path, views: list[str], size: int) -> int:
    """`step` is a part's .step, or an assembly's .glb (glTF: Y-up, colours + transparency)."""
    gltf = step.suffix == ".glb"
    for name in views:
        direction, up = VIEWS[name]
        if gltf:
            direction, up = y_up(direction), y_up(up)
        png = EXPORTS / f"{step.stem}_{name}.png"
        cmd = [
            "f3d", str(step), "--output", str(png), "--no-config",
            "--resolution", f"{size},{size}",
            "--up", "+Y" if gltf else "+Z", "--camera-direction", direction, "--camera-view-up", up,
            "--axis", "--grid", "--verbose", "quiet",
        ]
        # A STEP is drawn with its B-rep edges; a glTF is a triangle mesh, so --edges would
        # draw every triangle. --blending honours its alpha (see-through reference geometry).
        cmd.append("--blending" if gltf else "--edges")
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
