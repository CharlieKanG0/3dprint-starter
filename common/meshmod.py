"""Modify a downloaded model (3MF or STL): load it, add and cut features, check it, export it.

A model downloaded from MakerWorld, Printables or Thingiverse is a *mesh* (a skin of tiny
triangles), not a CAD solid, so it cannot be edited with build123d's solid operations. This
module is the mesh side of the repo's workflow (docs/modifying.md): the downloaded shape stays
exactly as its designer made it, and what you add or cut is built as named parameters.

    from common.meshmod import load_model, apply_changes, to_mesh, assert_watertight, ...

    base = load_model(SOURCE)                      # millimetres, centred in X/Y, bottom at Z=0
    boss = to_mesh(Cylinder(6, 8).locate(...))     # new geometry is drawn in build123d
    hole = to_mesh(Cylinder(2.6, 30).locate(...))
    result = apply_changes(base, add=[boss], cut=[hole])   # (base + add) - cut

Coordinates: `load_model` puts the model on the bed the way a slicer would (build transforms
applied, XY centred on the bounding box, lowest point at Z=0) so the sketch, the part script
and `inspect_model.py` all talk about the same numbers.

Nothing here is specific to one model. Mesh checks mirror common/verify.py: a mesh has no
"holes" or "faces" to query, so features are checked by probing a small box of space
(`material_in`) and by volume.
"""

from __future__ import annotations

import io
import math
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh

from common import printer

NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS_PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
UNIT_MM = {"micron": 0.001, "millimeter": 1.0, "centimeter": 10.0, "inch": 25.4, "foot": 304.8, "meter": 1000.0}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

@dataclass
class SourceInfo:
    """What the file says about itself (3MF only; an STL has none of this)."""
    path: Path
    kind: str  # "3mf" or "stl"
    unit: str = "millimeter"
    title: str = ""
    designer: str = ""
    license: str = ""
    application: str = ""
    extra: dict[str, str] = field(default_factory=dict)


def _tag(local: str, ns: str = NS_CORE) -> str:
    return f"{{{ns}}}{local}"


def _matrix(text: str | None) -> np.ndarray:
    """A 3MF `transform` (12 numbers, row-vector convention) as a 4x4 column-vector matrix."""
    m = np.eye(4)
    if not text:
        return m
    v = [float(x) for x in text.split()]
    if len(v) != 12:
        raise ValueError(f"3MF transform needs 12 numbers, got {len(v)}")
    m[:3, :3] = np.array(v[:9]).reshape(3, 3).T
    m[:3, 3] = v[9:]
    return m


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(zf.read(name.lstrip("/")))


def _object_triangles(zf, root, file_name, obj_id, cache, depth=0):
    """(vertices Nx3, faces Mx3) of object `obj_id` in model part `file_name`, components resolved."""
    if depth > 16:
        raise ValueError("3MF components nest too deeply (a loop?)")
    key = (file_name, obj_id)
    if key in cache:
        return cache[key]
    obj = next((o for o in root.iter(_tag("object")) if o.get("id") == obj_id), None)
    if obj is None:
        raise ValueError(f"3MF object {obj_id} not found in {file_name}")
    verts, faces = [], []
    mesh = obj.find(_tag("mesh"))
    if mesh is not None:
        v = np.array([[float(x.get("x")), float(x.get("y")), float(x.get("z"))]
                      for x in mesh.find(_tag("vertices"))])
        f = np.array([[int(t.get("v1")), int(t.get("v2")), int(t.get("v3"))] for t in mesh.find(_tag("triangles"))])
        verts.append(v)
        faces.append(f)
    comps = obj.find(_tag("components"))
    if comps is not None:
        for c in comps:
            path = c.get(_tag("path", NS_PROD)) or c.get("path")
            sub_file, sub_root = (path.lstrip("/"), _read_xml(zf, path)) if path else (file_name, root)
            v, f = _object_triangles(zf, sub_root, sub_file, c.get("objectid"), cache, depth + 1)
            m = _matrix(c.get("transform"))
            verts.append(v @ m[:3, :3].T + m[:3, 3])
            faces.append(f if np.linalg.det(m[:3, :3]) >= 0 else f[:, ::-1])
    offset, vs, fs = 0, [], []
    for v, f in zip(verts, faces):
        vs.append(v)
        fs.append(f + offset)
        offset += len(v)
    out = (np.vstack(vs), np.vstack(fs)) if vs else (np.zeros((0, 3)), np.zeros((0, 3), int))
    cache[key] = out
    return out


def _read_3mf(path: Path) -> tuple[trimesh.Trimesh, SourceInfo]:
    with zipfile.ZipFile(path) as zf:
        root = _read_xml(zf, "3D/3dmodel.model")
        unit = root.get("unit", "millimeter")
        scale = UNIT_MM.get(unit)
        if scale is None:
            raise ValueError(f"unknown 3MF unit {unit!r}")
        meta = {m.get("name"): (m.text or "").strip() for m in root.findall(_tag("metadata"))}
        info = SourceInfo(path=path, kind="3mf", unit=unit, title=meta.get("Title", ""),
                          designer=meta.get("Designer", ""), license=meta.get("License", ""),
                          application=meta.get("Application", ""), extra=meta)
        build = root.find(_tag("build"))
        items = list(build) if build is not None else []
        cache: dict = {}
        verts, faces, offset = [], [], 0
        for item in items:
            if item.get("printable", "1") == "0":
                continue
            v, f = _object_triangles(zf, root, "3D/3dmodel.model", item.get("objectid"), cache)
            m = _matrix(item.get("transform"))
            v = v @ m[:3, :3].T + m[:3, 3]
            f = f if np.linalg.det(m[:3, :3]) >= 0 else f[:, ::-1]
            verts.append(v)
            faces.append(f + offset)
            offset += len(v)
    if not verts:
        raise ValueError(f"{path.name}: no printable object in the 3MF")
    mesh = trimesh.Trimesh(np.vstack(verts) * scale, np.vstack(faces), process=False)
    return mesh, info


def load_model(path: str | Path, place: bool = True) -> trimesh.Trimesh:
    """Load a 3MF or STL as a mesh in millimetres.

    `place=True` (default) centres it in X/Y on its bounding box and sits it on Z=0, so every
    script that loads the same file agrees on coordinates. The shift is kept in
    `mesh.metadata["shift"]` (add it to a coordinate to get back to the file's frame)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".3mf":
        mesh, _ = _read_3mf(path)
    elif suffix == ".stl":
        mesh = trimesh.load(path, file_type="stl", force="mesh", process=False)
    else:
        raise ValueError(f"{path.name}: only .3mf and .stl are supported")
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    shift = np.zeros(3)
    if place:
        lo, hi = mesh.bounds
        shift = -np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
        mesh.apply_translation(shift)
    mesh.metadata["shift"] = shift
    mesh.metadata["source"] = str(path)
    return mesh


def source_info(path: str | Path) -> SourceInfo:
    """Title, designer, licence and unit of a file (empty strings for an STL)."""
    path = Path(path)
    if path.suffix.lower() == ".3mf":
        return _read_3mf(path)[1]
    return SourceInfo(path=path, kind="stl")


# ---------------------------------------------------------------------------
# Condition of a mesh
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MeshHealth:
    triangles: int
    bodies: int  # separate pieces
    watertight: bool  # every edge shared by exactly two triangles (a closed skin)
    winding_ok: bool  # all triangles face outward consistently
    volume: float  # mm^3 (positive when the skin faces outward)
    area: float  # mm^2
    size: tuple[float, float, float]

    @property
    def usable(self) -> bool:
        """Closed, consistently oriented and with positive volume: safe for add/cut."""
        return self.watertight and self.winding_ok and self.volume > 0

    def problems(self) -> list[str]:
        out = []
        if not self.watertight:
            out.append("not watertight: the skin has gaps or edges shared by three or more triangles")
        if not self.winding_ok:
            out.append("triangles are not consistently oriented (some face inward)")
        if self.volume <= 0:
            out.append("zero or negative volume (the whole mesh may be inside out)")
        return out


def health(mesh: trimesh.Trimesh) -> MeshHealth:
    bodies = len(mesh.split(only_watertight=False)) if len(mesh.faces) else 0
    return MeshHealth(
        triangles=len(mesh.faces), bodies=bodies, watertight=bool(mesh.is_watertight),
        winding_ok=bool(mesh.is_winding_consistent), volume=float(mesh.volume), area=float(mesh.area),
        size=tuple(float(x) for x in mesh.extents),
    )


def repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Best-effort cleanup of a broken mesh: weld, drop degenerate triangles, fix orientation, fill small holes.
    Returns a copy. Check `health(...)` afterwards -- a mesh with big gaps stays unusable and needs
    fixing in a mesh tool (Orca's "Repair" / Bambu Studio) first."""
    m = mesh.copy()
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(m)
    trimesh.repair.fix_inversion(m)
    trimesh.repair.fill_holes(m)
    return m


# ---------------------------------------------------------------------------
# Making and combining geometry
# ---------------------------------------------------------------------------

def to_mesh(shape, tolerance: float = 0.02, angular: float = 0.1) -> trimesh.Trimesh:
    """A build123d shape (Part, Solid, Compound) as a closed mesh. `tolerance` is the largest gap
    between the curved surface and its flat triangles in mm (0.02 is invisible when printed)."""
    verts, tris = shape.tessellate(tolerance, angular)
    m = trimesh.Trimesh([(v.X, v.Y, v.Z) for v in verts], tris, process=False)
    m.merge_vertices()
    assert m.is_watertight, "to_mesh: the build123d shape tessellated to an open mesh -- is the solid valid?"
    return m


def _as_mesh(x) -> trimesh.Trimesh:
    return x if isinstance(x, trimesh.Trimesh) else to_mesh(x)


def apply_changes(base: trimesh.Trimesh, add=(), cut=()) -> trimesh.Trimesh:
    """`(base + every item in add) - every item in cut`, as a closed mesh.

    Items may be meshes or build123d shapes (converted with `to_mesh`). Cuts also remove material
    from what was added, so a hole can pass through a new boss. The base must be usable
    (`health(base).usable`; try `repair` first)."""
    h = health(base)
    assert h.usable, "apply_changes: the base mesh is not usable -- " + "; ".join(h.problems())
    result = base
    adds = [_as_mesh(x) for x in add]
    cuts = [_as_mesh(x) for x in cut]
    if adds:
        result = trimesh.boolean.union([result, *adds], engine="manifold")
    if cuts:
        result = trimesh.boolean.difference([result, *cuts], engine="manifold")
    result.merge_vertices()
    result.metadata.update(base.metadata)
    return result


# ---------------------------------------------------------------------------
# Checks (the mesh counterparts of common/verify.py)
# ---------------------------------------------------------------------------

def assert_watertight(mesh: trimesh.Trimesh) -> None:
    h = health(mesh)
    assert h.usable, "mesh is not a valid closed solid -- " + "; ".join(h.problems())


def assert_single_body(mesh: trimesh.Trimesh) -> None:
    """One connected piece (a cut that severs the part, or a feature floating free, shows up here)."""
    n = len(mesh.split(only_watertight=False))
    assert n == 1, f"expected one body, found {n}"


def assert_mesh_bbox(mesh: trimesh.Trimesh, size: tuple[float, float, float], tol: float = 0.2, on_bed: bool = True) -> None:
    got = tuple(float(x) for x in mesh.extents)
    assert all(abs(g - e) <= tol for g, e in zip(got, size)), f"bbox {got} != expected {size} (tol {tol})"
    if on_bed:
        assert abs(mesh.bounds[0][2]) <= tol, f"lowest point is at Z={mesh.bounds[0][2]:.3f}, expected 0 (on the bed)"


def assert_mesh_volume(mesh: trimesh.Trimesh, lo: float, hi: float) -> None:
    assert lo <= mesh.volume <= hi, f"volume {mesh.volume:.0f} mm^3 outside [{lo:.0f}, {hi:.0f}]"


def material_in(mesh: trimesh.Trimesh, centre: tuple[float, float, float], size: float = 1.0) -> float:
    """Fraction (0..1) of a small cube of space that is solid. 1.0 = inside material, 0.0 = open air.
    This is how a mesh feature is checked: probe where the hole or boss should be."""
    probe = trimesh.creation.box((size, size, size))
    probe.apply_translation(centre)
    hit = trimesh.boolean.intersection([mesh, probe], engine="manifold")
    return float(hit.volume / probe.volume) if len(hit.faces) else 0.0


def assert_void_at(mesh, centre, size: float = 1.0) -> None:
    f = material_in(mesh, centre, size)
    assert f < 0.01, f"expected open space at {tuple(centre)}, found {f:.0%} material"


def assert_solid_at(mesh, centre, size: float = 1.0) -> None:
    f = material_in(mesh, centre, size)
    assert f > 0.99, f"expected material at {tuple(centre)}, found {f:.0%}"


def mesh_bed_fit(mesh: trimesh.Trimesh, bed=printer.BED, margin: float = printer.BED_MARGIN):
    """Same answer as common.verify.bed_fit, for a mesh (footprint = convex hull of the XY outline)."""
    from common.verify import fit_points

    hull = trimesh.convex.hull_points(mesh.vertices[:, :2])
    return fit_points([(float(x), float(y)) for x, y in hull], bed, margin)


# ---------------------------------------------------------------------------
# Sections, for the layout sketch
# ---------------------------------------------------------------------------

_SECTION = {  # cut-plane axis -> (plane normal, indices of the two drawn coordinates, sketch axes)
    "z": ((0, 0, 1), (0, 1), ("X", "Y")),  # top view: a slice at height `at`
    "y": ((0, 1, 0), (0, 2), ("X", "Z")),  # front view: a slice at depth `at`
    "x": ((1, 0, 0), (1, 2), ("Y", "Z")),  # side view: a slice at `at` along X
}


def section_loops(mesh: trimesh.Trimesh, axis: str = "z", at: float | None = None) -> list[np.ndarray]:
    """Outlines of the slice through the mesh perpendicular to `axis` at coordinate `at` (default:
    the middle of its extent), as a list of closed (N, 2) point loops in the drawn axes
    (see `section_axes`). Nested loops are holes: fill them with the even-odd rule."""
    normal, idx, _ = _SECTION[axis]
    k = "xyz".index(axis)
    if at is None:
        at = float(mesh.bounds[:, k].mean())
    origin = np.zeros(3)
    origin[k] = at
    path = mesh.section(plane_origin=origin, plane_normal=normal)
    if path is None:
        return []
    return [np.asarray(loop)[:, list(idx)] for loop in path.discrete]


def section_axes(axis: str) -> tuple[str, str]:
    """Sketch axis names for a section: pass as `Sketch(..., axes=section_axes("y"))`."""
    return _SECTION[axis][2]


def draw_section(sketch, mesh: trimesh.Trimesh, axis: str = "z", at: float | None = None, role: str = "existing") -> None:
    """Draw a slice of the mesh into a common.sketch.Sketch as the 'existing' structure."""
    assert tuple(sketch.axes) == section_axes(axis), (
        f"sketch axes are {sketch.axes}; a {axis}-section needs Sketch(..., axes={section_axes(axis)})")
    sketch.polygon(section_loops(mesh, axis, at), role)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def write_3mf(mesh: trimesh.Trimesh, path: str | Path, name: str = "model") -> Path:
    """A plain geometry-only 3MF in millimetres (no print settings: the slicer applies yours).
    Orca, Bambu Studio and PrusaSlicer all open it."""
    path = Path(path)
    v = mesh.vertices
    f = mesh.faces
    verts = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in v)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{NS_CORE}">'
        f'<metadata name="Title">{safe}</metadata><metadata name="Application">3dprint (common/meshmod.py)</metadata>'
        f'<resources><object id="1" type="model"><mesh><vertices>{verts}</vertices><triangles>{tris}</triangles></mesh>'
        '</object></resources><build><item objectid="1"/></build></model>'
    )
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    types = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model)
    path.write_bytes(buf.getvalue())
    return path


def write_stl(mesh: trimesh.Trimesh, path: str | Path) -> Path:
    path = Path(path)
    path.write_bytes(trimesh.exchange.stl.export_stl(mesh))
    return path
