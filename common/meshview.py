"""Show a mesh (a downloaded or modified 3MF/STL) in a browser tab -- the mesh counterpart of the OCP viewer.

The OCP viewer (common/viewer.py) draws CAD solids; a mesh model is 10^4-10^5 triangles, so this
writes one self-contained page (exports/<name>/view.html, the model embedded as numbers, drawn with
three.js loaded from a CDN, so it needs internet) and opens it where the OCP viewer would open: an Orca
built-in browser tab, else the default browser. Drag to spin, scroll to zoom, right-drag to pan.

`ghost` (optional) is drawn see-through in the same frame, to compare a modified model with the
original: what you added or cut stands out against it.
"""

from __future__ import annotations

import base64
import json
import os
import webbrowser
from pathlib import Path

from common.project import ROOT
from common.viewer import _orca_json, in_orca

THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
ORBIT = "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"


def _b64(mesh) -> str:
    tri = mesh.vertices[mesh.faces].astype("<f4")  # (n, 3, 3), no index buffer: simple and fine at this size
    return base64.b64encode(tri.tobytes()).decode()


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{{margin:0;height:100%;background:#f4f5f7;font:13px/1.4 -apple-system,Helvetica,Arial,sans-serif;color:#222}}
#c{{display:block;width:100vw;height:100vh}}#i{{position:fixed;left:12px;top:10px;background:#fffc;padding:6px 10px;border-radius:6px}}</style>
</head><body><canvas id="c"></canvas><div id="i">{title}<br>{info}</div>
<script src="{three}"></script><script src="{orbit}"></script>
<script>
const DATA={data};
const dec=s=>new Float32Array(Uint8Array.from(atob(s),c=>c.charCodeAt(0)).buffer);
const R=new THREE.WebGLRenderer({{canvas:document.getElementById('c'),antialias:true}});R.setPixelRatio(devicePixelRatio);
const S=new THREE.Scene();S.background=new THREE.Color(0xf4f5f7);
THREE.Object3D.DefaultUp.set(0,0,1);
const cam=new THREE.PerspectiveCamera(35,1,1,20000);
S.add(new THREE.HemisphereLight(0xffffff,0x888899,0.9));
const L=new THREE.DirectionalLight(0xffffff,0.7);L.position.set(1,-1.5,2);S.add(L);
function add(b64,opts){{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(dec(b64),3));g.computeVertexNormals();
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial(Object.assign({{side:THREE.DoubleSide,roughness:.6,metalness:0}},opts)));S.add(m);return m}}
if(DATA.ghost)add(DATA.ghost,{{color:0x888888,transparent:true,opacity:.22,depthWrite:false,polygonOffset:true,polygonOffsetFactor:4,polygonOffsetUnits:4}});
const main=add(DATA.mesh,{{color:0x2563eb}});
const [x0,y0,z0,x1,y1,z1]=DATA.bounds,cx=(x0+x1)/2,cy=(y0+y1)/2,cz=(z0+z1)/2,r=Math.max(x1-x0,y1-y0,z1-z0);
const grid=new THREE.GridHelper(Math.max(DATA.bed[0],r*2),Math.max(DATA.bed[0],r*2)/10,0xbbbbbb,0xdddddd);grid.rotation.x=Math.PI/2;grid.position.set(cx,cy,0);S.add(grid);
const ctl=new THREE.OrbitControls(cam,R.domElement);ctl.target.set(cx,cy,cz);
cam.position.set(cx+r*1.3,cy-r*1.8,cz+r*1.1);ctl.update();
function fit(){{R.setSize(innerWidth,innerHeight,false);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()}}
addEventListener('resize',fit);fit();(function loop(){{requestAnimationFrame(loop);R.render(S,cam)}})();
</script></body></html>"""


def write_view(mesh, name: str, ghost=None, bed=(256.0, 256.0), out_dir: Path | None = None) -> Path:
    """Write exports/<name>/view.html for `mesh` (and optionally `ghost`). Returns the path."""
    out = (out_dir or ROOT / "exports" / name)
    out.mkdir(parents=True, exist_ok=True)
    lo, hi = mesh.bounds
    ex = mesh.extents
    data = {"mesh": _b64(mesh), "ghost": _b64(ghost) if ghost is not None else None,
            "bounds": [*map(float, lo), *map(float, hi)], "bed": list(bed)}
    info = f"{ex[0]:.1f} x {ex[1]:.1f} x {ex[2]:.1f} mm, {len(mesh.faces):,} triangles" + (" (grey = original)" if ghost is not None else "")
    path = out / "view.html"
    path.write_text(PAGE.format(title=name, info=info, three=THREE, orbit=ORBIT, data=json.dumps(data)))
    return path


def open_view(path: Path) -> str:
    """Open `path` in an Orca built-in tab (switch to it if already open), else the default browser."""
    url = path.resolve().as_uri()
    if in_orca():
        tab = next((t for t in _orca_json("tab", "list").get("tabs", []) if t["url"] == url), None)
        if tab:
            _orca_json("tab", "switch", "--page", tab["browserPageId"])
            _orca_json("reload")  # the tab just switched to is the active one
        else:
            _orca_json("tab", "create", "--url", url)
    elif not os.environ.get("CI"):
        webbrowser.open(url)
    return url
