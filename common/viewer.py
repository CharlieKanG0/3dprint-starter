"""Find or start an OCP viewer for a part and show it in a built-in browser tab.

Shared by `common/output.show_part` (every part/assembly run) and `scripts/view.py`.

Where a model goes when a script runs (first match wins):
  1. OCP_PORT set           -> that viewer (scripts/view.py sets it after preparing the tab).
  2. Inside Orca            -> the part's own standalone viewer (stable port from 3940,
                               remembered in exports/viewers.json), started if needed,
                               shown in an Orca built-in browser tab (opened, or switched to).
  3. VS Code panel on 3939  -> there.
  4. Viewer venv installed  -> the part's own standalone viewer in your default browser
                               (opened once per viewer process; VIEW_REOPEN=1 reopens).
  5. none of the above      -> skipped with a one-line note (never blocks on a prompt).
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import webbrowser
from pathlib import Path

from common.project import ROOT

EXPORTS = ROOT / "exports"
REGISTRY = EXPORTS / "viewers.json"
BASE_PORT = 3940
VSCODE_PORT = 3939
HOWTO = "run ./setup.sh for the browser viewer, see docs/viewer.md"


def viewer_python() -> str:
    """Interpreter with ocp_viewer: OCP_VIEWER_PYTHON, else ./.viewer-venv (setup.sh), else ~/.venvs/ocpviewer."""
    if os.environ.get("OCP_VIEWER_PYTHON"):
        return os.environ["OCP_VIEWER_PYTHON"]
    for cand in (ROOT / ".viewer-venv/bin/python", Path.home() / ".venvs/ocpviewer/bin/python"):
        if cand.exists():
            return str(cand)
    return str(ROOT / ".viewer-venv/bin/python")


class ViewerError(RuntimeError):
    pass


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def in_orca() -> bool:
    """Running inside the Orca IDE, with its CLI available to open browser tabs."""
    return bool(os.environ.get("ORCA_WORKTREE_ID")) and shutil.which("orca") is not None


def load() -> dict[str, int]:
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}


def assign(name: str, reg: dict[str, int] | None = None) -> int:
    """Stable port for `name` (first free one from BASE_PORT), remembered in exports/viewers.json."""
    reg = load() if reg is None else reg
    if name not in reg:
        port = BASE_PORT
        while port in reg.values() or port_open(port):  # skip ports taken by other parts or other viewers
            port += 1
        reg[name] = port
        EXPORTS.mkdir(exist_ok=True)
        REGISTRY.write_text(json.dumps(reg, indent=2))
    return reg[name]


def ensure_viewer(port: int) -> None:
    if port_open(port):
        return
    py = viewer_python()
    if not Path(py).exists():
        raise ViewerError(f"viewer interpreter not found: {py} -- run ./setup.sh")
    EXPORTS.mkdir(exist_ok=True)
    log = open(EXPORTS / f"viewer_{port}.log", "w")
    subprocess.Popen(
        [py, "-m", "ocp_viewer", "--port", str(port), "--axes0", "--grid_xy"],
        stdout=log, stderr=log, start_new_session=True,
    )
    for _ in range(60):
        if port_open(port):
            return
        time.sleep(0.25)
    raise ViewerError(f"viewer on port {port} did not start; see exports/viewer_{port}.log")


def _orca_json(*args: str) -> dict:
    out = subprocess.run(["orca", *args, "--json"], capture_output=True, text=True)
    return json.loads(out.stdout)["result"] if out.returncode == 0 and out.stdout else {}


def ensure_tab(port: int) -> str:
    """Show the viewer's tab: an Orca built-in tab (switched to, or created), else the default
    browser (once per viewer process; VIEW_REOPEN=1 reopens). Returns the URL.

    A push to a viewer with no tab connected is lost, so a new tab gets a moment to
    connect its websocket before the caller pushes."""
    url = f"http://localhost:{port}/viewer"
    if not shutil.which("orca"):
        if os.environ.get("VIEW_REOPEN") is None and _seen(port):
            print(f"viewer tab: {url}  (closed it? re-run with VIEW_REOPEN=1)")
            return url
        print(f"opening {url}")
        webbrowser.open(url)
        time.sleep(3.0)
        return url
    tab = next((t for t in _orca_json("tab", "list").get("tabs", []) if t["url"] == url), None)
    if tab:
        _orca_json("tab", "switch", "--page", tab["browserPageId"])
        return url
    _orca_json("tab", "create", "--url", url)
    time.sleep(2.0)
    return url


def _seen(port: int) -> bool:
    """True if this viewer process already had a browser tab opened by an earlier run."""
    marker = EXPORTS / f"viewer_{port}.opened"
    pid = ",".join(map(str, pids(port)))
    if marker.exists() and marker.read_text() == pid:
        return True
    EXPORTS.mkdir(exist_ok=True)
    marker.write_text(pid)
    return False


def open_for(name: str) -> int | None:
    """Port to push `name` to, with its viewer up and (in Orca) its tab showing; None if no viewer."""
    if os.environ.get("OCP_PORT"):
        return int(os.environ["OCP_PORT"])
    if in_orca():
        port = assign(name)
        ensure_viewer(port)
        ensure_tab(port)
        return port
    if port_open(VSCODE_PORT):
        return VSCODE_PORT
    if Path(viewer_python()).exists():
        port = assign(name)
        ensure_viewer(port)
        ensure_tab(port)
        return port
    return None


def pids(port: int) -> list[int]:
    out = subprocess.run(["lsof", "-tiTCP:%d" % port, "-sTCP:LISTEN"], capture_output=True, text=True).stdout
    return [int(p) for p in out.split()]
