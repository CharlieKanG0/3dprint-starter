"""Face teeth (a Hirth-style rosette) for a spring-loaded click / detent joint.

Two identical rosettes, one flipped to face the other and turned half a tooth,
mesh along their whole width: every flank is a plane through the joint axis at
the mid-plane, so the tooth height grows with radius (h = r * sin(pi/n), i.e. a
90 deg included angle at every radius). Push the halves together with a spring
and the joint clicks round in 360/n steps, holding by friction on the 45 deg
flanks -- no pin. Slip torque ~ F * r_mean * tan(45 deg + atan(mu)).

    teeth, band = face_teeth(40, r_in=15, r_out=25)
    # teeth: z in [-band, +band]; the mid-plane (where two halves meet) is z = 0.
    # Sit the rosette on a body face at z = -band. Two meshed halves leave
    # 2 * band between their body faces.

Printing: fine on a face pointing up (best) or on a vertical face (the worst
flank is then a 45 deg overhang). Keep the tooth height >= ~1 mm on FDM.
"""

import math

from build123d import Axis, Cylinder, Part, Solid, Wire, Location, Pos


def tooth_height(n: int, r: float) -> float:
    """Root-to-tip height at radius r (90 deg included angle)."""
    return r * math.sin(math.pi / n)


def mesh_overlap(a, b) -> float:
    """Volume two placed rosettes (or parts carrying them) share -- ~0 when they mesh."""
    return (a & b).volume


def face_teeth(n: int, r_in: float, r_out: float, phase_deg: float = 0.0) -> tuple[Part, float]:
    """`n` teeth between radii r_in..r_out about +Z, tips toward +Z. Returns (solid, band).

    `phase_deg` turns the pattern; tooth roots sit at phase + k*360/n. A mating half,
    flipped to face this one, needs phase + 180/n after the flip (check it -- see
    `mesh_overlap` in a part's assertions).
    """
    band = tooth_height(n, r_out) / 2 + 0.4  # half-height of the tooth band, + a solid floor
    r_lo, r_hi = r_in * 0.8, r_out * 1.15  # build oversize, then trim to the annulus
    half = math.pi / n

    def pentagon(r: float, a0: float) -> Wire:
        a1, am = a0 + 2 * half, a0 + half
        h = tooth_height(n, r) / 2
        rm = r * math.cos(half)  # chord midpoint radius
        pts = [
            (r * math.cos(a0), r * math.sin(a0), -band),
            (r * math.cos(a0), r * math.sin(a0), -h),
            (rm * math.cos(am), rm * math.sin(am), h),
            (r * math.cos(a1), r * math.sin(a1), -h),
            (r * math.cos(a1), r * math.sin(a1), -band),
        ]
        return Wire.make_polygon(pts, close=True)

    a0 = math.radians(phase_deg)
    tooth = Solid.make_loft([pentagon(r_lo, a0), pentagon(r_hi, a0)], ruled=True)
    teeth = [tooth.rotate(Axis.Z, k * 360.0 / n) for k in range(n)]
    ring = Pos(0, 0, -band) * (Cylinder(r_out, 2 * band, align=None) - Cylinder(r_in, 2 * band, align=None))
    floor_top = -tooth_height(n, r_in) / 2  # inside r_in: flat, at the root level of the inner edge
    hub = Pos(0, 0, -band) * Cylinder(r_in, floor_top + band, align=None)
    rosette = Part() + teeth
    return (rosette & ring) + hub, band
