"""One OCP viewer + browser tab per part or assembly, so they can be viewed side by side.

    ./venv/bin/python scripts/view.py <name>          # part or assembly: start its viewer, open its tab, push
    ./venv/bin/python scripts/view.py --list          # part -> port, and whether the viewer is up
    ./venv/bin/python scripts/view.py --stop <part|all>

Each part gets a stable port (first free one from 3940, remembered in
exports/viewers.json). The viewer is started if it isn't running, the Orca
browser tab is opened (or switched to) BEFORE the model is pushed -- a push to a
viewer with no tab connected is lost -- then the part script runs with
OCP_PORT set and PART_NO_EXPORT=1, so no .step is rewritten.

A plain run of a part script does the same by itself (common/output.show_part ->
common/viewer.py); this CLI adds --list / --stop and a no-export push.

Needs the standalone viewer venv that ./setup.sh creates (override the interpreter
with OCP_VIEWER_PYTHON). Opens an Orca built-in tab when the `orca` CLI is there,
else your default browser.
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.project import find_script  # noqa: E402
from common.viewer import ViewerError, assign, ensure_tab, ensure_viewer, load, pids, port_open  # noqa: E402


def push(part: str, port: int) -> int:
    script = find_script(part)
    env = {**os.environ, "OCP_PORT": str(port), "PART_NO_EXPORT": "1"}
    return subprocess.run([sys.executable, str(script)], env=env, cwd=ROOT).returncode


def main() -> int:
    args = sys.argv[1:]
    reg = load()
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--list":
        for part, port in sorted(reg.items(), key=lambda kv: kv[1]):
            print(f"{part:24} :{port}  {'up' if port_open(port) else 'down'}")
        return 0
    if args[0] == "--stop":
        targets = list(reg) if args[1:] == ["all"] else args[1:]
        for part in targets:
            for pid in pids(reg.get(part, -1)):
                os.kill(pid, signal.SIGTERM)
                print(f"stopped {part} viewer (pid {pid})")
        return 0
    part = args[0]
    port = assign(part, reg)
    try:
        ensure_viewer(port)
    except ViewerError as e:
        sys.exit(str(e))
    ensure_tab(port)
    return push(part, port)


if __name__ == "__main__":
    sys.exit(main())
