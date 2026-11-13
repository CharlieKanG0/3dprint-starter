"""One OCP viewer + browser tab per part or assembly, so they can be viewed side by side.

    ./venv/bin/python scripts/view.py <name>          # part or assembly: start its viewer, open its tab, push
    ./venv/bin/python scripts/view.py --list          # part -> port, and whether the viewer is up
    ./venv/bin/python scripts/view.py --stop <part|all>

Each part gets a stable port (first free one from 3940, remembered in
exports/viewers.json). The viewer is started if it isn't running, a browser
tab is opened (or, in Orca, switched to) BEFORE the model is pushed -- a push to a
viewer with no tab connected is lost -- then the part script runs with
OCP_PORT set and PART_NO_EXPORT=1, so no .step is rewritten.

Needs the standalone viewer venv that ./setup.sh creates (override the
interpreter with OCP_VIEWER_PYTHON). Opens tabs in your default browser, or via
the `orca` CLI when it is installed (Orca reuses an existing tab).
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.project import find_script  # noqa: E402

EXPORTS = ROOT / "exports"
REGISTRY = EXPORTS / "viewers.json"
BASE_PORT = 3940
VIEWER_PY = os.environ.get("OCP_VIEWER_PYTHON", str(ROOT / ".viewer-venv/bin/python"))


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def load() -> dict[str, int]:
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}


def assign(part: str, reg: dict[str, int]) -> int:
    if part not in reg:
        port = BASE_PORT
        while port in reg.values() or port_open(port):  # skip ports taken by other parts or other viewers
            port += 1
        reg[part] = port
        EXPORTS.mkdir(exist_ok=True)
        REGISTRY.write_text(json.dumps(reg, indent=2))
    return reg[part]


def ensure_viewer(port: int) -> None:
    if port_open(port):
        return
    if not Path(VIEWER_PY).exists():
        sys.exit(f"viewer interpreter not found: {VIEWER_PY} -- run ./setup.sh")
    EXPORTS.mkdir(exist_ok=True)
    log = open(EXPORTS / f"viewer_{port}.log", "w")
    subprocess.Popen(
        [VIEWER_PY, "-m", "ocp_viewer", "--port", str(port), "--axes0", "--grid_xy"],
        stdout=log, stderr=log, start_new_session=True,
    )
    for _ in range(60):
        if port_open(port):
            return
        time.sleep(0.25)
    sys.exit(f"viewer on port {port} did not start; see exports/viewer_{port}.log")


def orca_json(*args: str) -> dict:
    out = subprocess.run(["orca", *args, "--json"], capture_output=True, text=True)
    return json.loads(out.stdout)["result"] if out.returncode == 0 and out.stdout else {}


def ensure_tab(port: int) -> None:
    url = f"http://localhost:{port}/viewer"
    if not shutil.which("orca"):
        if port_open(port) and REGISTRY.exists() and os.environ.get("VIEW_REOPEN") is None and _seen(port):
            print(f"viewer tab: {url}  (re-run with VIEW_REOPEN=1 if you closed it)")
            return
        print(f"opening {url}")
        webbrowser.open(url)
        time.sleep(3.0)  # let the tab connect its websocket before the model is pushed
        return
    tab = next((t for t in orca_json("tab", "list").get("tabs", []) if t["url"] == url), None)
    if tab:
        orca_json("tab", "switch", "--page", tab["browserPageId"])
        return
    orca_json("tab", "create", "--url", url)
    time.sleep(2.0)  # let the tab connect its websocket before the model is pushed


def _seen(port: int) -> bool:
    """True if this viewer process already had a tab opened by an earlier view.py run."""
    marker = EXPORTS / f"viewer_{port}.opened"
    pid = ",".join(map(str, pids(port)))
    if marker.exists() and marker.read_text() == pid:
        return True
    marker.write_text(pid)
    return False


def push(part: str, port: int) -> int:
    script = find_script(part)
    env = {**os.environ, "OCP_PORT": str(port), "PART_NO_EXPORT": "1"}
    return subprocess.run([sys.executable, str(script)], env=env, cwd=ROOT).returncode


def pids(port: int) -> list[int]:
    out = subprocess.run(["lsof", "-tiTCP:%d" % port, "-sTCP:LISTEN"], capture_output=True, text=True).stdout
    return [int(p) for p in out.split()]


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
    ensure_viewer(port)
    ensure_tab(port)
    return push(part, port)


if __name__ == "__main__":
    sys.exit(main())
