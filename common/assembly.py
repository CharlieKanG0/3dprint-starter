"""Put several parts together with reference geometry, check the fit, view or render it.

An assembly script lives at assemblies/<name>/<name>.py (copy
assemblies/templates/assembly_template.py). It works for any combination of
parts -- a bracket on a slat, a box and its lid, a whole roof system:

    asm = Assembly("shovel_on_rail")
    mount = asm.part("shovel_mount")                              # fresh geometry, see part()
    asm.ref("rail", Box(400, 40, 20), at=(0, 0, -10))             # not printed: context only
    asm.add("mount left", mount, at=(-100, 0, 0), group="mounts")
    asm.add("mount right", mount, at=(100, 0, 0), group="mounts")
    asm.check_overlaps()                                          # every pair, true volumes
    asm.assert_gap("mount left", "mount right", 50, None)         # names, groups, or fnmatch globs
    asm.finish()                                                  # viewer, or STEP in render mode

Run modes are the ones in common/output.py: PART_CHECK=1 (build_all) runs the
assertions only, PART_RENDER=dir (scripts/render.py) also writes one coloured,
partly transparent <name>.glb into dir, otherwise the scene goes to the OCP viewer (OCP_PORT,
scripts/view.py). Nothing is written next to the script: an assembly is derived
from its parts, so there is no committed .step to go stale.

Overlap volumes come from a real solid boolean (Solid & Solid), with a
self-test that a known overlap is detected -- a probe that silently returns
"no overlap" is worse than none.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from build123d import Axis, Box, Color, Compound, Location, Plane, Shape, import_step

from common.output import check_mode, show_part
from common.project import ROOT, find_script

CACHE = ROOT / "exports" / ".assembly_cache"

# Colours handed out to groups that don't name one (light first: dark scenes in the viewer).
PALETTE = ["#e8e8e8", "#3a7bd5", "#d08a2e", "#4caf50", "#c0392b", "#8e44ad", "#16a085", "#f1c40f"]
REF_COLOR = "#666666"
# Render tessellation (mm, rad): fine enough for a picture, coarse enough to stay fast on a big scene.
GLTF_LINEAR_DEFLECTION = 0.05
GLTF_ANGULAR_DEFLECTION = 0.2


# ---------------------------------------------------------------------------
# Loading parts
# ---------------------------------------------------------------------------


def _cache_key(script: Path) -> str:
    h = hashlib.sha1(script.read_bytes())
    for f in sorted((ROOT / "common").glob("*.py")):
        h.update(f.read_bytes())
    for k in sorted(k for k in os.environ if k.startswith("PARAM_")):
        h.update(f"{k}={os.environ[k]}".encode())
    return h.hexdigest()[:12]


def load_part(part: str, step: str | None = None) -> Shape:
    """Geometry of one exported STEP of a part, built fresh from its current script.

    The part script runs in render mode into a cache directory keyed on its
    source, common/, and any PARAM_* overrides -- so the assembly never shows a
    stale committed .step, and the committed one is never rewritten. `step` is
    the exported file's stem for multi-variant parts (default: the part name).
    """
    script = find_script(part)
    out = CACHE / part / _cache_key(script)
    done = out / ".done"
    if not done.exists():
        out.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k not in ("PART_CHECK", "PART_NO_EXPORT", "OCP_PORT")}
        env["PART_RENDER"] = str(out)
        run = subprocess.run([sys.executable, str(script)], env=env, cwd=ROOT, capture_output=True, text=True)
        if run.returncode != 0:
            tail = "\n".join((run.stderr or run.stdout).strip().splitlines()[-12:])
            raise RuntimeError(f"part {part} failed to build:\n{tail}")
        done.touch()
    path = out / f"{step or part}.step"
    if not path.exists():
        have = sorted(p.stem for p in out.glob("*.step"))
        raise FileNotFoundError(f"part {part} exported no {path.name}; it exports: {have}")
    return import_step(str(path))


def place(shape: Shape, at=(0.0, 0.0, 0.0), rotate=(0.0, 0.0, 0.0), mirror: Plane | None = None) -> Shape:
    """Copy of `shape`: mirrored first, then rotated about X, Y, Z (degrees, origin), then moved to `at`."""
    s = shape.mirror(mirror) if mirror is not None else shape
    for axis, deg in zip((Axis.X, Axis.Y, Axis.Z), rotate):
        if deg:
            s = s.rotate(axis, deg)
    return s.moved(Location(tuple(at)))


# ---------------------------------------------------------------------------
# Geometry probes
# ---------------------------------------------------------------------------


def _rgba(hex_color: str, alpha: float) -> Color:
    h = hex_color.lstrip("#")
    return Color(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)), alpha)


def _matte_gltf(path: Path, roughness: float = 0.8) -> None:
    """Make every material in a .glb matte plastic. build123d leaves metallicFactor at the
    glTF default of 1.0, which renders printed parts as dark metal."""
    import json
    import struct

    data = path.read_bytes()
    json_len = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + json_len])
    rest = data[20 + json_len:]  # BIN chunk, untouched
    for m in doc.get("materials", []):
        pbr = m.setdefault("pbrMetallicRoughness", {})
        pbr["metallicFactor"], pbr["roughnessFactor"] = 0.0, roughness
    blob = json.dumps(doc, separators=(",", ":")).encode()
    blob += b" " * (-len(blob) % 4)  # chunks are 4-byte aligned
    chunk = struct.pack("<I4s", len(blob), b"JSON") + blob
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk) + len(rest)) + chunk + rest)


def _bbox_overlap(a: Shape, b: Shape, pad: float = 0.0) -> bool:
    ba, bb = a.bounding_box(), b.bounding_box()
    return all(
        getattr(ba.min, c) - pad <= getattr(bb.max, c) and getattr(bb.min, c) - pad <= getattr(ba.max, c)
        for c in "XYZ"
    )


def overlap_volume(a: Shape, b: Shape) -> float:
    """Volume shared by two shapes (solid by solid). 0.0 when they only touch or are apart."""
    vol = 0.0
    for sa in a.solids():
        for sb in b.solids():
            if not _bbox_overlap(sa, sb):
                continue
            r = sa & sb
            if r is not None:
                vol += sum(s.volume for s in r.solids())
    return vol


def _self_test() -> None:
    v = overlap_volume(Box(2, 2, 2), Box(2, 2, 2).moved(Location((1, 0, 0))))
    assert abs(v - 4.0) < 1e-6, f"overlap probe is broken: expected 4.0 mm^3 for a known overlap, got {v}"


# ---------------------------------------------------------------------------
# The assembly
# ---------------------------------------------------------------------------


@dataclass
class Instance:
    name: str
    shape: Shape
    group: str
    reference: bool  # context geometry (rack, purchased item, placeholder), not printed


@dataclass
class Assembly:
    name: str
    instances: list[Instance] = field(default_factory=list)
    colors: dict[str, str] = field(default_factory=dict)  # group -> colour
    alphas: dict[str, float] = field(default_factory=dict)  # group -> opacity

    # --- building ---

    def part(self, part: str, step: str | None = None) -> Shape:
        """Fresh geometry of a part's exported STEP (see load_part). Place it with add()."""
        return load_part(part, step)

    def add(self, name: str, shape: Shape, *, group: str | None = None, color: str | None = None,
            alpha: float = 1.0, reference: bool = False, **placement) -> Shape:
        """Place a copy of `shape` (placement kwargs: at, rotate, mirror -- see place()).

        Instances in the same group share a colour and one entry in the viewer tree.
        Returns the placed shape.
        """
        assert name not in {i.name for i in self.instances}, f"duplicate instance name {name!r}"
        group = group or name
        placed = place(shape, **placement)  # always a copy: the label below must not touch `shape`
        placed.label = name  # the instance's name in the viewer tree
        self.instances.append(Instance(name, placed, group, reference))
        if group not in self.colors:
            printed = sum(1 for g in self.colors if not self._is_ref_group(g))
            self.colors[group] = color or (REF_COLOR if reference else PALETTE[printed % len(PALETTE)])
            self.alphas[group] = alpha
        return placed

    def _is_ref_group(self, group: str) -> bool:
        return all(i.reference for i in self.instances if i.group == group)

    def ref(self, name: str, shape: Shape, **kw) -> Shape:
        """Reference geometry: the rack, a bought item, a placeholder for a part not designed yet."""
        return self.add(name, shape, reference=True, **kw)

    # --- selecting ---

    def select(self, sel: str) -> list[Instance]:
        """Instances matching `sel`: an exact group name, else an fnmatch glob on instance names."""
        hits = [i for i in self.instances if i.group == sel] or [
            i for i in self.instances if fnmatch.fnmatchcase(i.name, sel)
        ]
        assert hits, f"{self.name}: nothing matches {sel!r}"
        return hits

    def _matches(self, inst: Instance, sel: str) -> bool:
        return inst.group == sel or fnmatch.fnmatchcase(inst.name, sel)

    # --- checks ---

    def check_overlaps(self, allow: list[tuple[str, str]] = (), tol: float = 1e-3) -> None:
        """Assert no two instances share volume (> tol mm^3), except the `allow`ed pairs.

        Touching faces are fine (zero volume). `allow` takes (selector, selector)
        pairs, either order -- e.g. a bolt that is meant to pass through a hole
        modelled without one.
        """
        _self_test()
        bad = []
        for a, b in combinations(self.instances, 2):
            if any((self._matches(a, x) and self._matches(b, y)) or (self._matches(a, y) and self._matches(b, x))
                   for x, y in allow):
                continue
            if not _bbox_overlap(a.shape, b.shape):
                continue
            v = overlap_volume(a.shape, b.shape)
            if v > tol:
                bad.append(f"  {a.name} <-> {b.name}: {v:.2f} mm^3")
        assert not bad, f"{self.name}: overlapping instances\n" + "\n".join(bad)
        n = len(self.instances)
        print(f"{self.name}: no overlaps among {n} instances ({n * (n - 1) // 2} pairs, {len(allow)} allowed)")

    def gap(self, a: str, b: str) -> float:
        """Smallest distance between anything matching `a` and anything matching `b` (0 = touching or overlapping)."""
        best = None
        for ia in self.select(a):
            for ib in self.select(b):
                if ia is ib:
                    continue
                d = ia.shape.distance_to(ib.shape)
                best = d if best is None else min(best, d)
        assert best is not None, f"{self.name}: {a!r} and {b!r} select the same single instance"
        return best

    def assert_gap(self, a: str, b: str, lo: float | None, hi: float | None) -> float:
        """Assert lo <= gap(a, b) <= hi (either bound may be None). Prints the measured value."""
        d = self.gap(a, b)
        ok = (lo is None or d >= lo - 1e-6) and (hi is None or d <= hi + 1e-6)
        want = f"{'-inf' if lo is None else lo} .. {'inf' if hi is None else hi}"
        print(f"{self.name}: gap {a} <-> {b} = {d:.3f} mm (want {want}) {'ok' if ok else 'FAIL'}")
        assert ok, f"{self.name}: gap {a!r} <-> {b!r} is {d:.3f} mm, want {want}"
        return d

    def assert_each_touches(self, a: str, b: str, tol: float = 0.01) -> None:
        """Every instance matching `a` touches something matching `b` (e.g. each clamp sits on the panel)."""
        for ia in self.select(a):
            d = min(ia.shape.distance_to(ib.shape) for ib in self.select(b) if ib is not ia)
            assert d <= tol, f"{self.name}: {ia.name} is {d:.3f} mm from {b!r}, expected to touch"
        print(f"{self.name}: every {a} touches {b} ok")

    # --- output ---

    def groups(self) -> dict[str, list[Instance]]:
        out: dict[str, list[Instance]] = {}
        for i in self.instances:
            out.setdefault(i.group, []).append(i)
        return out

    def compound(self) -> Compound:
        """Everything as one labelled compound, every solid coloured by its group (with alpha)."""
        children = []
        for g, insts in self.groups().items():
            kids = []
            for i in insts:
                for n, solid in enumerate(i.shape.solids()):
                    s = solid.moved(Location())  # copy, so labels/colours don't leak between instances
                    s.label = i.name if n == 0 else f"{i.name} #{n}"
                    s.color = _rgba(self.colors[g], self.alphas[g])
                    kids.append(s)
            children.append(Compound(children=kids, label=g))
        return Compound(children=children, label=self.name)

    def finish(self) -> None:
        """Render mode: write <name>.glb (colours + transparency, which F3D honours; STEP
        colours it ignores) into PART_RENDER. Otherwise push to the viewer (no-op in check mode)."""
        render_dir = os.environ.get("PART_RENDER")
        if render_dir:
            from build123d import export_gltf

            Path(render_dir).mkdir(parents=True, exist_ok=True)
            out = Path(render_dir) / f"{self.name}.glb"
            export_gltf(self.compound(), str(out), binary=True,
                        linear_deflection=GLTF_LINEAR_DEFLECTION, angular_deflection=GLTF_ANGULAR_DEFLECTION)
            _matte_gltf(out)
            return
        if check_mode():
            return
        groups = self.groups()
        show_part(
            *[Compound(children=[i.shape for i in insts]) for insts in groups.values()],
            names=list(groups),
            colors=[self.colors[g] for g in groups],
            alphas=[self.alphas[g] for g in groups],
        )
