"""Mechanical checks every part runs before it is called done.

These are the "Verify before calling a part done" checks from CLAUDE.md as
code, so a part script calls them instead of re-deriving each one inline.
Each `assert_*` raises AssertionError with the numbers that failed.
"""

import math
from dataclasses import dataclass

from build123d import GeomType
from OCP.BRepAdaptor import BRepAdaptor_Surface

from common import printer


@dataclass(frozen=True)
class CylinderAxis:
    """A cylindrical face's TRUE OCC axis (not Face.center(), which is wrong for
    partial/trimmed faces -- e.g. the end caps of a slot)."""

    radius: float
    x: float  # a point on the axis
    y: float
    z: float
    dx: float  # axis direction (unit)
    dy: float
    dz: float


def cylinder_axes(part) -> list[CylinderAxis]:
    out = []
    for face in part.faces().filter_by(GeomType.CYLINDER):
        cyl = BRepAdaptor_Surface(face.wrapped).Cylinder()
        ax = cyl.Axis()
        loc, d = ax.Location(), ax.Direction()
        out.append(CylinderAxis(cyl.Radius(), loc.X(), loc.Y(), loc.Z(), d.X(), d.Y(), d.Z()))
    return out


def assert_single_solid(part) -> None:
    """Catches stray blobs and most broken booleans."""
    n = len(part.solids())
    assert n == 1, f"part is {n} solids, expected 1"


def assert_bbox(part, size: tuple[float, float, float], tol: float = 0.01, on_bed: bool = True) -> None:
    """Bounding box matches the intended overall dimensions; `on_bed` also requires min Z == 0."""
    bb = part.bounding_box()
    got = (bb.size.X, bb.size.Y, bb.size.Z)
    assert all(abs(g - e) <= tol for g, e in zip(got, size)), (
        f"bounding box {got[0]:.2f} x {got[1]:.2f} x {got[2]:.2f}, expected {size}"
    )
    if on_bed:
        assert abs(bb.min.Z) <= tol, f"part's lowest point is Z={bb.min.Z:.3f}, expected 0 (print bed)"


def assert_volume(part, lo: float, hi: float) -> None:
    """A bad boolean often changes volume by an amount that's obvious at a glance."""
    assert lo < part.volume < hi, f"volume {part.volume:.0f} mm^3 outside the expected {lo:.0f}-{hi:.0f}"


def assert_holes(part, radius: float, positions: list[tuple[float, float]], tol: float = 0.01) -> None:
    """Every cylinder of `radius` whose axis is vertical must sit exactly at `positions` (x, y).

    Slots work too: pass the centre of each rounded end. A hole split into two
    faces by a seam is counted once.
    """
    found = set()
    for c in cylinder_axes(part):
        if abs(c.radius - radius) <= tol and abs(abs(c.dz) - 1.0) <= 1e-6:
            found.add((round(c.x, 2), round(c.y, 2)))
    assert len(found) == len(positions), (
        f"expected {len(positions)} vertical holes of radius {radius}, found {len(found)}: {sorted(found)}"
    )
    for ex, ey in positions:
        assert any(abs(fx - ex) <= tol and abs(fy - ey) <= tol for fx, fy in found), (
            f"no hole of radius {radius} at ({ex}, {ey}); found {sorted(found)}"
        )


@dataclass(frozen=True)
class BedFit:
    angle_deg: int  # rotate about Z by this much for the smallest footprint
    width: float
    height: float
    bed: tuple[float, float]
    margin: float

    @property
    def fits(self) -> bool:
        return self.width <= self.bed[0] - 2 * self.margin and self.height <= self.bed[1] - 2 * self.margin

    def summary(self) -> str:
        return (
            f"Bed fit: rotate {self.angle_deg} deg -> {self.width:.0f} x {self.height:.0f} mm on a "
            f"{self.bed[0]:.0f} x {self.bed[1]:.0f} mm bed ({self.margin:g} mm margin/side): "
            + ("FITS" if self.fits else "DOES NOT FIT")
        )


def bed_fit(part, bed: tuple[float, float] = printer.BED, margin: float = printer.BED_MARGIN) -> BedFit:
    """Smallest-footprint rotation of the part about Z (any 0-179 degrees) on the bed (common/printer.py)."""
    pts = [(p.X, p.Y) for e in part.edges() for p in (e.position_at(i / 16) for i in range(17))]
    best = None
    for deg in range(180):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        xs = [x * c - y * s for x, y in pts]
        ys = [x * s + y * c for x, y in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if best is None or max(w, h) < max(best[1], best[2]):
            best = (deg, w, h)
    return BedFit(best[0], best[1], best[2], bed, margin)
