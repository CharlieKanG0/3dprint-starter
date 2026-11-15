"""Rebuild every part and assembly headless and fail if any assertion breaks.

    ./venv/bin/python scripts/build_all.py            # all parts
    ./venv/bin/python scripts/build_all.py shower_mount
    ./venv/bin/python scripts/build_all.py --staged   # only what the commit touches

A part is any parts/<name>/<name>.py, an assembly any assemblies/<name>/<name>.py
(common/project.py). Parts run first, then assemblies. Each runs in its own process with
PART_CHECK=1, so nothing is exported or sent to a viewer (see common/output.py)
and committed .step files are never rewritten. Run by the pre-commit hook
(.githooks/pre-commit) with --staged, so a change to common/ can't silently break
a part while a half-finished part elsewhere can't block an unrelated commit. A part whose layout.py
is still waiting for the user's letter (CONFIRMED empty) is listed as "wait", not failed:
it refuses to build by design, and that must not block a fix to the shared code. A part whose
layout.py sets OPEN (what it is waiting on) has that printed beside its result.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.project import all_scripts, kind_of  # noqa: E402
from common.verify import layout_open, layout_pending  # noqa: E402


def discover(names: list[str]) -> list[Path]:
    scripts = all_scripts()
    if names:
        missing = set(names) - {s.stem for s in scripts}
        if missing:
            sys.exit(f"unknown part(s): {', '.join(sorted(missing))}")
        scripts = [s for s in scripts if s.stem in names]
    return scripts


# A staged change under any of these can affect every part, so it checks them all.
SHARED = ("common/", "things/", "scripts/", "requirements.txt", ".githooks/")


def staged_parts() -> list[str]:
    """Names to check for the current commit: everything if shared code changed;
    otherwise the parts and assemblies with staged files, plus every assembly
    whenever any part changed (assemblies are built from parts). Empty = nothing to check."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    if any(f.startswith(SHARED) for f in out):
        return [s.stem for s in discover([])]
    touched = {f.split("/")[1] for f in out if f.startswith(("parts/", "assemblies/")) and f.count("/") >= 2}
    part_changed = any(f.startswith("parts/") for f in out)
    return [
        s.stem for s in discover([])
        if s.stem in touched or (part_changed and kind_of(s) == "assemblies")
    ]


def main() -> int:
    env = {**os.environ, "PART_CHECK": "1"}
    failed = []
    args = sys.argv[1:]
    inv = subprocess.run([sys.executable, str(ROOT / "scripts/things.py"), "--check"], capture_output=True, text=True)
    if inv.returncode != 0:  # things/INVENTORY.md is generated; CLAUDE.md imports it, so it must be current
        print(inv.stdout.strip())
        return 1
    if args in ([], ["--staged"]):  # the downloaded-model helpers (common/meshmod.py): cheap, and every mod part depends on them
        chk = subprocess.run([sys.executable, str(ROOT / "scripts/check_meshmod.py")], capture_output=True, text=True)
        print(f"{'ok  ' if chk.returncode == 0 else 'FAIL'}  meshmod self-check")
        if chk.returncode != 0:
            print("\n".join(("      " + ln) for ln in (chk.stderr or chk.stdout).strip().splitlines()[-8:]))
            return 1
    if args == ["--staged"]:
        args = staged_parts()
        if not args:
            print("no staged part or shared-code changes; nothing to check")
            return 0
    for script in discover(args):
        open_ = layout_open(script.parent)
        if layout_pending(script.parent):
            why = open_ or "the user's letter (layout not confirmed)"
            print(f"wait  {script.stem}  (waiting on: {why})")
            continue
        result = subprocess.run(
            [sys.executable, str(script)], env=env, capture_output=True, text=True, timeout=600
        )
        ok = result.returncode == 0
        print(f"{'ok  ' if ok else 'FAIL'}  {script.stem}" + (f"  (waiting on: {open_})" if open_ else ""))
        if not ok:
            failed.append(script.stem)
            print("\n".join(("      " + line) for line in (result.stderr or result.stdout).strip().splitlines()[-12:]))
    if failed:
        print(f"\n{len(failed)} part(s) failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
