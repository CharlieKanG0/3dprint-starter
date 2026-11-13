"""Shower mount -- layout schematics: the "sketch before you model" record (CLAUDE.md step 0).

End view looking along the vehicle: +X = outward from the vehicle side, +Z = up.
Origin = top outer corner of the platform side rail. A printed snap claw at the
arm tip grips the shower handle directly (replaces the stock holster).

Run:     ../../venv/bin/python layout.py
Output:  layout_b.svg, layout_b_hinge.svg, layout_b_claw.svg, layout_b_tip.svg

Layout B chosen by the user 2026-11-13 (A = swing arm + drop bar, rejected),
with the corrections: toothed click hinge instead of a pull-pin; spring enclosed
in the hub + knob cap; own compact claw instead of the stock holster.
Modelled 2026-11-13 in shower_mount.py, which records where the model departs
from these drawings (arm split in two for the bed, spigot-style spring cover on the
main hinge, claw on the arm tip's +Y face, hinge axis 50 above the rail).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.sketch import Sketch

CONFIRMED = ("B (flip arm on a toothed click hinge) + spring enclosed + own claw, tip joint T2 "
             "integrated; then telescopic round arm, roll free, thumb-knob lock A -- user, 2026-11-13")

HERE = Path(__file__).parent

# --- Existing (ALL ASSUMED until measured) ---------------------------------
RAIL_W = 50.0  # side rail top width
RAIL_H = 40.0  # side rail height
CHANNEL_X = -20.0  # top T-channel centre, from the rail's outer face
CHANNEL_W = 8.0  # slot opening
BODY_INSET = 25.0  # body side panel sits this far inboard of the rail face

# --- Carried: shower handset (ASSUMED from photos, hand for scale) ----------
HANDLE_D = 34.0  # handle diameter where the claw grips -- MEASURE
HEAD_ABOVE_CLAW = 45.0  # handset length above the claw (threaded top end)
HEAD_BELOW_CLAW = 150.0  # handset length below the claw (grip + hose fitting)

# --- Claw (printed, replaces the stock holster) -------------------------------
CLAW_H = 30.0  # grip height along the handle (stock holster was ~110)
CLAW_WALL = 4.0
CLAW_WRAP_DEG = 220.0  # how far the claw wraps the handle; the rest is the mouth

# --- Tip joint (T2, integrated): the claw's back boss IS one half of the joint ----
TIP_BOSS_D = 30.0  # = ARM_W: the joint is no bigger than the arm it sits on
TIP_TEETH = 24  # 15 deg per click
TIP_ROSETTE_OD, TIP_ROSETTE_ID = 24.0, 10.0
TIP_R_MEAN = (TIP_ROSETTE_OD + TIP_ROSETTE_ID) / 4
TIP_TOOTH_H = (2 * math.pi * TIP_R_MEAN / TIP_TEETH) / 2  # 90 deg included teeth
TIP_BOLT = "M5"
CLAW_BOSS_T = 10.0  # claw's joint boss thickness along the joint axis (Y)
ARM_T = 18.0  # arm thickness along Y (also the tip's thickness)
TIP_SPRING_OD, TIP_SPRING_L, TIP_SPRING_F = 8.0, 12.0, 60.0  # ASSUMED small stainless spring over M5
TIP_POCKET_D = TIP_SPRING_OD + 2 * 1.0
TIP_CAP_PROUD = 6.0  # thumb cap stands this far out of the arm face
AIM_MAX = 30.0  # spray aim range toward the user
TIP_GAP = 2.0  # arm-tip disc -> outside of the claw ring (the claw turns about the joint)
HANDLE_OFFSET = HANDLE_D / 2 + CLAW_WALL + TIP_BOSS_D / 2 + TIP_GAP  # tip joint axis -> handle axis
# the claw ring turns about the joint, so its nearest point stays this far from the axis:
assert HANDLE_OFFSET - (HANDLE_D / 2 + CLAW_WALL) - TIP_BOSS_D / 2 >= TIP_GAP - 1e-9, "arm tip rubs the claw ring"

# --- Design targets (ASSUMED, parameters) ------------------------------------
REACH = 300.0  # rail face -> hanging point: water must clear the body side
ADJUST = 250.0  # height adjustment range = arm length * sin(max drop angle)
ARM_W = 30.0
TOOTH_COUNT = 40  # B: face teeth on the hinge -> 360/40 = 9 deg per click
MAX_DROP_DEG = 45.0  # B: hard stop, arm cannot go lower (keeps head off the body side)
TILT_STEPS = tuple(range(0, int(MAX_DROP_DEG) + 1, 360 // TOOTH_COUNT))  # 0, 9, ... 45


def draw_existing(sk: Sketch) -> None:
    sk.rect(-RAIL_W / 2, -RAIL_H / 2, RAIL_W, RAIL_H, "existing")
    sk.rect(CHANNEL_X, -4, CHANNEL_W, 8, "feature")
    sk.text(-RAIL_W - 8, -RAIL_H / 2 + 8, "side rail (profile unknown)", anchor="end")
    sk.rect(-BODY_INSET - 10, -RAIL_H - 260, 20, 500, "existing")
    sk.text(-BODY_INSET - 25, -RAIL_H - 200, "body side", anchor="end")
    sk.rect(-260, -RAIL_H - 12, 440, 16, "existing")  # roof skin
    sk.text(-200, -RAIL_H - 32, "roof")


def draw_claw_head(sk: Sketch, x: float, z_pivot: float, tilt: float = 0.0, label: bool = True,
                   dashed: bool = False) -> None:
    """Claw + handset on the integrated tip joint at (x, z_pivot), side view.

    The joint boss is a round lobe on the back (-X) of the claw at mid-height; the arm tip sits
    beside it (offset along Y, so it never meets the handset). `tilt` (deg) rotates the claw
    about the joint, positive = spray end (top) leans toward the user (+X).
    """
    t = math.radians(tilt)

    def w(lx, lz):  # local (relative to the joint, untilted) -> world, clockwise by tilt
        return (x + lx * math.cos(t) + lz * math.sin(t), z_pivot - lx * math.sin(t) + lz * math.cos(t))

    head_len = HEAD_ABOVE_CLAW + CLAW_H + HEAD_BELOW_CLAW
    head_mid = CLAW_H / 2 + HEAD_ABOVE_CLAW - head_len / 2
    sk.rect(*w(HANDLE_OFFSET, head_mid), HANDLE_D, head_len, "carried", angle=-tilt, dashed=dashed)
    sk.rect(*w(HANDLE_OFFSET, 0), HANDLE_D + 2 * CLAW_WALL, CLAW_H, "part", angle=-tilt, dashed=dashed)
    if not dashed:
        sk.circle(x, z_pivot, TIP_BOSS_D / 2, "part")  # claw boss (and the arm tip behind it)
    sk.circle(x, z_pivot, 2.5, "hardware")
    if label:
        sk.text(x + HANDLE_OFFSET + 30, z_pivot - 40, "claw + handset", anchor="start")


# =============================================================================
# B -- flip arm on a spring-loaded toothed (face-gear) hinge
# =============================================================================
# Hinge numbers (ASSUMED starting points; the holding-torque check below uses them)
ROSETTE_OD, ROSETTE_ID = 50.0, 30.0
R_MEAN = (ROSETTE_OD + ROSETTE_ID) / 4
TOOTH_PITCH = 2 * math.pi * R_MEAN / TOOTH_COUNT
TOOTH_H = TOOTH_PITCH / 2  # 90 deg included tooth -> height = half the pitch
FLANK_DEG = 45.0  # tooth flank angle from the rotation plane
MU = 0.3  # ASA on ASA, dry/wet, ASSUMED
SPRING_F = 150.0  # N, spring force at the knob's working setting (ASSUMED)
SPRING_RATE = 20.0  # N/mm (ASSUMED stainless spring over the M8 bolt)
BOLT = "M8"
HUB_T = 22.0  # arm hub thickness along the hinge axis
LUG_T = 20.0  # base lug thickness
SPRING_L = 25.0  # working length at the nominal knob setting
SPRING_OD = 14.0  # ASSUMED, sits over the M8 bolt
# Spring enclosure: the spring sits in a pocket bored into the hub; a boss on the hub
# extends that pocket, and the knob is a closed cap whose skirt slides over the boss.
POCKET_CLR = 1.5  # radial clearance spring -> pocket wall
POCKET_DEPTH = 8.0  # how far the spring sinks into the hub (shallow = room for a long boss)
BOSS_WALL = 3.0
BOSS_L = 15.0  # boss stands this far proud of the hub face
SKIRT_CLR = 0.5  # radial clearance boss -> knob skirt (FDM sliding fit)
SKIRT_WALL = 2.5
WASHER_T = 3.0
CAP_T = 4.0  # knob end wall over the nut (bolt end hidden too)
RIM_GAP = 6.0  # knob skirt rim -> hub face at the nominal setting
CARRIED_KG = 0.6  # head + holster + water-filled hose share (ASSUMED)

L_B = ADJUST / math.sin(math.radians(MAX_DROP_DEG))
T_GRAV = CARRIED_KG * 9.81 * L_B / 1000  # Nm, worst case = arm horizontal
T_SLIP = SPRING_F * (R_MEAN / 1000) * math.tan(math.radians(FLANK_DEG) + math.atan(MU))
PUSH_DOWN = (T_SLIP - T_GRAV) / (L_B / 1000)
PUSH_UP = (T_SLIP + T_GRAV) / (L_B / 1000)

b = Sketch("B -- flip arm on a toothed click hinge, end view", size=520, axes=("X out", "Z"))
draw_existing(b)
hinge = (8.0, 10.0)
b.rect(CHANNEL_X + 5, 10, 60, 30, "part")
b.circle(CHANNEL_X, -2, 3, "hardware")
b.text(CHANNEL_X - 40, 4, "base: T-bolts in top channel", anchor="end")
b.circle(*hinge, ROSETTE_OD / 2, "part")
b.circle(*hinge, 4, "hardware")
b.text(hinge[0] + 5, 48, f"toothed hinge: {TOOTH_COUNT} teeth, clicks every {360 / TOOTH_COUNT:.0f} deg", anchor="start")
for deg in TILT_STEPS:
    t = math.radians(deg)
    tip = (hinge[0] + L_B * math.cos(t), hinge[1] - L_B * math.sin(t))
    if deg in (0, max(TILT_STEPS)):
        b.bar(hinge, tip, ARM_W, "part")
        draw_claw_head(b, tip[0], tip[1], label=deg == 0)
        b.text(tip[0] - 30, tip[1] + 28, f"{deg} deg")
    else:
        b.line(hinge, tip, "guide")
        b.text(tip[0] + 10, tip[1], f"{deg}", anchor="start")
b.text(hinge[0] + 80, hinge[1] - 150, f"hard stop at {MAX_DROP_DEG:.0f} deg", anchor="start")
b.rect(hinge[0] - L_B / 2, hinge[1] + 40, L_B, ARM_W, "part", dashed=True)
b.text(hinge[0] - L_B / 2, hinge[1] + 68, "stowed: clicked up and over, flat on the deck")
tip0 = (hinge[0] + L_B, hinge[1])
tip45 = (hinge[0] + L_B * math.cos(math.radians(MAX_DROP_DEG)), hinge[1] - L_B * math.sin(math.radians(MAX_DROP_DEG)))
b.dim((hinge[0], hinge[1]), tip0, f"{L_B:.0f} arm", offset=85)
b.dim((tip0[0] + 90, tip45[1]), (tip0[0] + 90, tip0[1]), f"{ADJUST:.0f} drop", offset=0)
b.notes(
    "Height: push the arm up/down; the spring-loaded teeth ride over each other and click into the next",
    f"  position ({', '.join(str(d) for d in TILT_STEPS)} deg). No pin. Claw on a tip joint keeps the head upright (see layout_b_tip).",
    f"Fold: push the arm up past vertical and over onto the deck; needs a clear ~{L_B:.0f} mm strip inboard.",
    f"Reach shrinks with angle: {L_B * math.cos(math.radians(MAX_DROP_DEG)):.0f} at {MAX_DROP_DEG:.0f} deg. "
    "ASSUMED: rail 50x40, channel position, body inset.",
)
b.save(HERE / "layout_b.svg")

# --- B hinge section: cut through the hinge axis (axis runs along the vehicle) --
h = Sketch("B -- toothed hinge, section through the hinge axis", size=150, axes=("Y along vehicle", "Z"))
ro, ri = ROSETTE_OD / 2, ROSETTE_ID / 2
# fixed base lug (part of the base), bolt head captured in a hex pocket on its far side
h.rect(-LUG_T / 2, -5, LUG_T, ROSETTE_OD + 30, "part")
h.text(-LUG_T / 2, ro + 22, "base lug (fixed)")
h.rect(-LUG_T + 3, 0, 6, 13, "hardware")
h.text(-LUG_T - 4, -ro + 2, f"{BOLT} hex head, captured", anchor="end")
# arm hub (rotates, slides axially by one tooth height)
# hub drawn around its spring pocket (pocket left empty so the spring shows)
_pf = TOOTH_H + HUB_T - POCKET_DEPTH
_pr = SPRING_OD / 2 + POCKET_CLR
h.rect((TOOTH_H + _pf) / 2, 0, _pf - TOOTH_H, ROSETTE_OD, "part")
for _s in (1, -1):
    h.rect(_pf + POCKET_DEPTH / 2, _s * (_pr + ro) / 2, POCKET_DEPTH, ro - _pr, "part")
h.text(HUB_T / 2 + TOOTH_H, ro + 12, "arm hub (rotates)")
h.text(HUB_T / 2 + TOOTH_H, -ro - 6, "arm leaves toward viewer (+X)")
# face teeth: zigzag across the interface on both sides of the bore
for sgn in (1, -1):
    z, k = ri, 0
    while z < ro - 1e-6:
        z2 = min(z + TOOTH_PITCH / 2, ro)
        y1, y2 = (0, TOOTH_H) if k % 2 == 0 else (TOOTH_H, 0)
        h.line((y1, sgn * z), (y2, sgn * z2), "cutout", dashed=False)
        z, k = z2, k + 1
# spring enclosure: pocket in the hub + boss, closed knob cap sliding over the boss
hub_face = TOOTH_H + HUB_T
pocket_r = SPRING_OD / 2 + POCKET_CLR
boss_r = pocket_r + BOSS_WALL
skirt_ri = boss_r + SKIRT_CLR
skirt_ro = skirt_ri + SKIRT_WALL
y_floor = hub_face - POCKET_DEPTH  # spring seats on the pocket floor
y_washer = y_floor + SPRING_L
y_knob_in = y_washer + WASHER_T  # inside face of the knob end wall
y_knob_out = y_knob_in + CAP_T + 8  # end wall holds a captured nyloc nut
y_rim = hub_face + RIM_GAP
OVERLAP = hub_face + BOSS_L - y_rim
ADJ_IN = RIM_GAP - TOOTH_H  # knob travel before the rim meets the hub (spring still lifts a tooth)
ADJ_OUT = OVERLAP  # knob travel outward before the skirt leaves the boss
BOSS_TO_CAP = y_knob_in - (hub_face + BOSS_L)  # boss end -> inside of the knob end wall
assert BOSS_TO_CAP >= ADJ_IN + 0.5, f"boss hits the knob before the rim meets the hub ({BOSS_TO_CAP:.1f} < {ADJ_IN:.1f}+0.5)"
assert OVERLAP >= 6, f"skirt overlaps the boss by only {OVERLAP:.1f} mm"
# boss (part of the hub), drawn as its two walls either side of the pocket
for sgn in (1, -1):
    h.rect(hub_face + BOSS_L / 2, sgn * (pocket_r + BOSS_WALL / 2), BOSS_L, BOSS_WALL, "part")
# knob cap: end wall + skirt (both sides)
h.rect((y_knob_in + y_knob_out) / 2, 0, y_knob_out - y_knob_in, 2 * skirt_ro, "part")
for sgn in (1, -1):
    h.rect((y_rim + y_knob_in) / 2, sgn * (skirt_ri + SKIRT_WALL / 2), y_knob_in - y_rim, SKIRT_WALL, "part")
h.text(y_knob_out + 4, 6, "knob = closed cap", anchor="start")
h.text(y_knob_out + 4, -2, "(sets spring force,", anchor="start")
h.text(y_knob_out + 4, -10, " nyloc nut inside)", anchor="start")
# bolt, spring, washer
bolt_end = y_knob_out - CAP_T - 1
h.rect((-LUG_T + 3 + bolt_end) / 2, 0, bolt_end + LUG_T - 3, 8, "hardware")
h.rect(bolt_end - 3.5, 0, 7, 13, "hardware")  # nyloc nut in the cap
for i in range(8):
    y0 = y_floor + i * SPRING_L / 8
    h.line((y0, SPRING_OD / 2 * (1 if i % 2 else -1)), (y0 + SPRING_L / 8, SPRING_OD / 2 * (-1 if i % 2 else 1)),
           "hardware", dashed=False)
h.rect(y_washer + WASHER_T / 2, 0, WASHER_T, 2 * pocket_r - 1, "hardware")
h.dim((0, ri), (0, ro), f"teeth {ri:.0f}-{ro:.0f} radius", offset=30)
h.dim((y_floor, -ro - 24), (y_floor + SPRING_L, -ro - 24), f"{SPRING_L:.0f} spring", offset=0)
h.dim((hub_face, -skirt_ro), (y_rim, -skirt_ro), f"{RIM_GAP:.0f} gap", offset=-5)
h.dim((y_rim, skirt_ro), (hub_face + BOSS_L, skirt_ro), f"{OVERLAP:.0f} overlap", offset=6)
h.text(y_floor + POCKET_DEPTH / 2, ro + 4, "spring pocket", anchor="middle")
h.notes(
    f"{TOOTH_COUNT} teeth, 90 deg included, height {TOOTH_H:.2f} at mean radius {R_MEAN:.0f} (printed facing up, no supports).",
    f"Holds: slip torque = F r tan(flank + atan mu) = {SPRING_F:.0f} N x {R_MEAN / 1000:.3f} m x "
    f"tan({FLANK_DEG:.0f}+{math.degrees(math.atan(MU)):.0f}) = {T_SLIP:.1f} Nm",
    f"  vs gravity {T_GRAV:.1f} Nm ({CARRIED_KG} kg at {L_B:.0f} mm) -> safety factor {T_SLIP / T_GRAV:.1f}.",
    f"Adjust by hand: ~{PUSH_DOWN:.0f} N to push down, ~{PUSH_UP:.0f} N to lift, at the tip.",
    f"ASSUMED: spring {SPRING_F:.0f} N at {SPRING_RATE:.0f} N/mm, mu {MU}, carried mass {CARRIED_KG} kg. "
    "Knob tightens hard for driving.",
    f"Spring enclosed: {POCKET_DEPTH:.0f} mm deep pocket in the hub + {BOSS_L:.0f} mm boss, covered by the knob's skirt"
    f" ({OVERLAP:.0f} mm overlap).",
    f"Knob range: {ADJ_IN:.1f} mm in (+{ADJ_IN * SPRING_RATE:.0f} N) before the rim meets the hub, {ADJ_OUT:.0f} mm out"
    f" (-{ADJ_OUT * SPRING_RATE:.0f} N) before the boss shows.",
    "Shower water gets in past the skirt: the annulus is open at the bottom so it drains; stainless spring + washer.",
)
h.save(HERE / "layout_b_hinge.svg")

# =============================================================================
# Claw -- top section through the grip (handle axis vertical)
# =============================================================================
mouth_deg = 360.0 - CLAW_WRAP_DEG
MOUTH_CHORD = HANDLE_D * math.sin(math.radians(mouth_deg / 2))
SNAP = HANDLE_D - MOUTH_CHORD  # how far the arms spread to let the handle in
c = Sketch("Claw -- top section through the grip", size=120, axes=("X out", "Y along vehicle"))
c.circle(0, 0, HANDLE_D / 2, "carried")
c.text(0, 0, f"handle {HANDLE_D:.0f}")
r_mid = HANDLE_D / 2 + CLAW_WALL / 2
n = 22
a0 = math.radians(mouth_deg / 2)  # mouth centred on +X: push the head in from outside
pts = [(r_mid * math.cos(a0 + k * (2 * math.pi - 2 * a0) / n), r_mid * math.sin(a0 + k * (2 * math.pi - 2 * a0) / n))
       for k in range(n + 1)]
for p0, p1 in zip(pts, pts[1:]):
    c.bar(p0, p1, CLAW_WALL, "part")
_jx = -HANDLE_OFFSET  # tip joint axis (runs along Y)
c.rect((_jx - TIP_BOSS_D / 2 - HANDLE_D / 2) / 2, 0, HANDLE_D / 2 - TIP_BOSS_D / 2 - _jx, CLAW_BOSS_T, "part")
c.rect(_jx, CLAW_BOSS_T / 2 + TIP_TOOTH_H + ARM_T / 2, TIP_BOSS_D, ARM_T, "part", dashed=True)
c.bar((_jx, -CLAW_BOSS_T / 2 - 3), (_jx, CLAW_BOSS_T / 2 + ARM_T + TIP_CAP_PROUD), 5, "hardware")
c.text(_jx - TIP_BOSS_D / 2 - 4, 0, "claw boss", anchor="end")
c.text(_jx - TIP_BOSS_D / 2 - 4, CLAW_BOSS_T / 2 + ARM_T / 2, "arm tip (dashed)", anchor="end")
mx = HANDLE_D / 2 * math.cos(a0)
c.dim((mx, -MOUTH_CHORD / 2), (mx, MOUTH_CHORD / 2), f"{MOUTH_CHORD:.1f} mouth", offset=-18)
c.dim((-HANDLE_D / 2, -HANDLE_D / 2 - 10), (HANDLE_D / 2, -HANDLE_D / 2 - 10), f"{HANDLE_D:.0f} handle", offset=0)
c.text(HANDLE_D / 2 + 24, -2, "push in", anchor="start")
c.notes(
    f"C-clip wraps {CLAW_WRAP_DEG:.0f} deg; mouth {MOUTH_CHORD:.1f} vs handle {HANDLE_D:.0f} -> arms spread {SNAP:.1f} mm, snap in/out.",
    f"Grip {CLAW_H:.0f} tall x {CLAW_WALL:.0f} wall (stock holster ~110 tall). Mouth faces outward, away from the vehicle.",
    "UNKNOWN: handle diameter, and whether it tapers or has a shoulder the claw can sit under",
    "  (a shoulder carries the weight; without one the snap grip alone has to stop it sliding down).",
)
c.save(HERE / "layout_b_claw.svg")

# =============================================================================
# Tip joint (T2, integrated) -- side view and section through the joint axis
# =============================================================================
TIP_T_GRAV = 0.5 * 9.81 * HANDLE_OFFSET / 1000  # Nm, ~0.5 kg handset + hose share (ASSUMED)
TIP_T_SLIP = TIP_SPRING_F * TIP_R_MEAN / 1000 * math.tan(math.radians(FLANK_DEG) + math.atan(MU))
tp = Sketch("Tip joint (T2) -- side view, integrated into the claw", size=300, axes=("X out", "Z"))
arm_deg = 27
t = math.radians(arm_deg)
tp.bar((-170 * math.cos(t), 170 * math.sin(t)), (0, 0), ARM_W, "part")
tp.text(-120, 90, f"arm, clicked {arm_deg} deg down", anchor="middle")
draw_claw_head(tp, 0, 0, label=False)
draw_claw_head(tp, 0, 0, tilt=AIM_MAX, label=False, dashed=True)
tp.text(HANDLE_OFFSET + 40, -150, "solid: upright", anchor="start")
tp.text(HANDLE_OFFSET + 40, -162, f"dashed: aimed {AIM_MAX:.0f} deg toward you", anchor="start")
tp.text(-TIP_BOSS_D / 2 - 6, -30, f"joint = round boss on the claw back, dia {TIP_BOSS_D:.0f}", anchor="end")
tp.text(-TIP_BOSS_D / 2 - 6, -42, "(same width as the arm)", anchor="end")
tp.dim((0, -CLAW_H / 2 - 8), (HANDLE_OFFSET, -CLAW_H / 2 - 8), f"{HANDLE_OFFSET:.0f}", offset=0)
tp.notes(
    "No hanger: the claw and its half of the joint are one printed piece. The arm tip sits beside the",
    "  boss (offset along the vehicle), so it clears the handset at every arm angle and aim.",
)
tp.save(HERE / "layout_b_tip.svg")

ts = Sketch("Tip joint (T2) -- section through the joint axis", size=90, axes=("Y along vehicle", "Z"))
y0 = -CLAW_BOSS_T  # claw boss from y0 to 0, teeth on its +Y face
tro, tri = TIP_ROSETTE_OD / 2, TIP_ROSETTE_ID / 2
ts.rect(y0 / 2, 0, CLAW_BOSS_T, TIP_BOSS_D, "part")
ts.text(y0 / 2, TIP_BOSS_D / 2 + 5, "claw boss")
ts.rect(y0 + 2, 0, 4, 8, "hardware")  # bolt head, recessed + captured in the boss
ts.text(y0 - 3, -9, f"{TIP_BOLT} head, recessed", anchor="end")
ya = TIP_TOOTH_H  # arm tip from ya to ya + ARM_T, spring pocket bored from its outer face
yo = ya + ARM_T
pocket_floor = yo - (TIP_SPRING_L + 1.5)
ts.rect((ya + pocket_floor) / 2, 0, pocket_floor - ya, TIP_BOSS_D, "part")
for sg in (1, -1):
    ts.rect((pocket_floor + yo) / 2, sg * (TIP_POCKET_D / 2 + TIP_BOSS_D / 2) / 2, yo - pocket_floor,
            TIP_BOSS_D / 2 - TIP_POCKET_D / 2, "part")
ts.text(ya + ARM_T / 2, TIP_BOSS_D / 2 + 5, "arm tip")
for sg in (1, -1):
    z, k = tri, 0
    while z < tro - 1e-6:
        z2 = min(z + TIP_TOOTH_H, tro)
        ts.line(((0, TIP_TOOTH_H)[k % 2], sg * z), ((TIP_TOOTH_H, 0)[k % 2], sg * z2), "cutout", dashed=False)
        z, k = z2, k + 1
for i in range(6):
    yy = pocket_floor + i * TIP_SPRING_L / 6
    ts.line((yy, TIP_SPRING_OD / 2 * (1 if i % 2 else -1)), (yy + TIP_SPRING_L / 6, TIP_SPRING_OD / 2 * (-1 if i % 2 else 1)),
            "hardware", dashed=False)
cap_in = pocket_floor + TIP_SPRING_L
ts.rect((cap_in + yo) / 2, 0, yo - cap_in, TIP_POCKET_D - 0.6, "part")  # cap spigot inside the pocket
ts.rect(yo + TIP_CAP_PROUD / 2, 0, TIP_CAP_PROUD, 20, "part")  # thumb cap
ts.rect((y0 + 4 + yo + TIP_CAP_PROUD - 2) / 2, 0, yo + TIP_CAP_PROUD - y0 - 6, 5, "hardware")
ts.text(yo + TIP_CAP_PROUD + 3, 4, "thumb cap, nyloc inside", anchor="start")
ts.text(yo + TIP_CAP_PROUD + 3, -4, "(spring hidden in the arm)", anchor="start")
ts.dim((y0, -TIP_BOSS_D / 2 - 6), (yo + TIP_CAP_PROUD, -TIP_BOSS_D / 2 - 6),
       f"{yo + TIP_CAP_PROUD - y0:.0f} whole joint", offset=0)
ts.dim((0, tri), (0, tro), f"teeth r{tri:.0f}-{tro:.0f}", offset=22)
ts.notes(
    f"{TIP_TEETH} teeth (every {360 / TIP_TEETH:.0f} deg), height {TIP_TOOTH_H:.1f}. Fine for FDM; "
    "if they print mushy, drop to 18 teeth (20 deg).",
    f"Holds: {TIP_SPRING_F:.0f} N spring -> slip {TIP_T_SLIP:.2f} Nm vs handset {TIP_T_GRAV:.2f} Nm "
    f"({HANDLE_OFFSET:.0f} mm offset): factor {TIP_T_SLIP / TIP_T_GRAV:.0f}.",
    f"  A hose tug of ~{TIP_T_SLIP / 0.1:.0f} N at the hose fitting (~100 mm below) re-aims it, by design.",
    f"Spring sits in a pocket in the arm tip; the thumb cap's spigot slides in the pocket, so it is always covered.",
    f"ASSUMED: spring {TIP_SPRING_OD:.0f} OD x {TIP_SPRING_L:.0f} long, {TIP_SPRING_F:.0f} N; handset 0.5 kg.",
)
ts.save(HERE / "layout_b_tip_section.svg")
print("wrote layout_b.svg, layout_b_hinge.svg, layout_b_claw.svg, layout_b_tip.svg, layout_b_tip_section.svg")

# =============================================================================
# Telescopic arm (user 2026-11-13: replaces the two-piece lap-jointed arm)
# Side view of the arm at THETA = 0, hinge on the origin, +X along the arm.
# =============================================================================
BED = 256.0  # P2S bed: each printed section must fit (incl. hub / tip disc)
HUB_R_T = 27.0  # hinge hub radius (shower_mount.py HUB_R)
TIP_R_T = 15.0  # tip disc radius
SLEEVE_H, SLEEVE_T = 34.0, 24.0  # outer sleeve: in the swing plane x along Y
WALL = 4.0
CLR = 0.3  # radial sliding clearance (FIT loose)
INNER_H, INNER_T = SLEEVE_H - 2 * WALL - 2 * CLR, SLEEVE_T - 2 * WALL - 2 * CLR
BORE_X0 = HUB_R_T + 5.0  # bore starts clear of the hub's spring pocket
SLEEVE_END = 220.0  # outer piece = hub + sleeve: 27 + 220 = 247 < 256
INNER_L = 225.0  # tip centre -> inner bar's end: piece 225 + 15 = 240 < 256
OVERLAP_MIN = 75.0  # bar always this deep in the sleeve (~2.2x its height)
L_MIN = BORE_X0 + INNER_L  # hinge -> tip, fully in
L_MAX = SLEEVE_END - OVERLAP_MIN + INNER_L  # hinge -> tip, fully out
assert HUB_R_T + SLEEVE_END <= BED - 4 and INNER_L + TIP_R_T <= BED - 4, "a section is longer than the bed"

ts2 = Sketch("Telescopic arm -- side view at 0 deg (retracted solid, extended dashed)", size=420, axes=("X along arm", "Z"))
ts2.circle(0, 0, HUB_R_T, "part")
ts2.text(0, HUB_R_T + 10, "hinge hub")
ts2.rect((0 + SLEEVE_END) / 2, 0, SLEEVE_END, SLEEVE_H, "part")
ts2.rect((BORE_X0 + SLEEVE_END) / 2, 0, SLEEVE_END - BORE_X0, SLEEVE_H - 2 * WALL, "cutout")
for L, dashed in ((L_MIN, False), (L_MAX, True)):
    bar0 = L - INNER_L
    ts2.rect((bar0 + L) / 2, 0, INNER_L, INNER_H, "carried" if dashed else "part", dashed=dashed)
    ts2.circle(L, 0, TIP_R_T, "part") if not dashed else ts2.rect(L, 0, 2 * TIP_R_T, 2 * TIP_R_T, "part", dashed=True)
ts2.text((BORE_X0 + SLEEVE_END) / 2, -SLEEVE_H / 2 - 10, "outer sleeve (prints with the hub)")
ts2.text(L_MAX - INNER_L / 2 + 40, -SLEEVE_H / 2 - 10, "inner bar (prints with the tip joint)")
ts2.circle(SLEEVE_END - 15, SLEEVE_H / 2 + 6, 6, "hardware")
ts2.text(SLEEVE_END - 15, SLEEVE_H / 2 + 22, "lock")
ts2.dim((0, -60), (L_MIN, -60), f"{L_MIN:.0f} retracted", offset=0)
ts2.dim((0, -85), (L_MAX, -85), f"{L_MAX:.0f} extended", offset=0)
ts2.dim((SLEEVE_END - OVERLAP_MIN, 40), (SLEEVE_END, 40), f"{OVERLAP_MIN:.0f} min overlap", offset=0)
ts2.notes(
    f"Hinge -> tip {L_MIN:.0f}-{L_MAX:.0f} ({L_MAX - L_MIN:.0f} travel). Reach out from the rail face "
    f"{10 + L_MIN + 38:.0f}-{10 + L_MAX + 38:.0f} at 0 deg;",
    f"  drop at the 45 deg stop {L_MIN * 0.707:.0f}-{L_MAX * 0.707:.0f}. Was one fixed length, 354.",
    f"Sections: sleeve {SLEEVE_H:.0f}x{SLEEVE_T:.0f} outside, {WALL:.0f} wall; bar {INNER_H:.1f}x{INNER_T:.1f}, "
    f"{CLR} sliding clearance per side.",
    f"Both pieces under {BED:.0f} so they print flat, teeth up -- no split joint, no lap bolts.",
    "Rectangular bar: can't twist in the sleeve, so the tip joint stays aligned with the hinge.",
)
ts2.save(HERE / "layout_b_telescope.svg")

# lock options: section across the sleeve mouth (looking down the arm), lettered
lk = Sketch("Telescope lock -- options A / B / C, section across the sleeve mouth", size=220, axes=("Y", "Z"))
for ox, name in ((0.0, "A"), (90.0, "B"), (180.0, "C")):
    lk.rect(ox, 0, SLEEVE_T, SLEEVE_H, "part")
    lk.rect(ox, 0, SLEEVE_T - 2 * WALL, SLEEVE_H - 2 * WALL, "cutout")
    lk.rect(ox, 0, INNER_T, INNER_H, "carried")
    lk.text(ox - 30, SLEEVE_H / 2 + 26, name, bold=True, size=8)
    if name == "A":
        lk.rect(ox, SLEEVE_H / 2 + 8, 22, 10, "part")
        lk.rect(ox, SLEEVE_H / 2 - WALL / 2, 4, WALL + 4, "hardware")
        lk.rect(ox, INNER_H / 2 - 1, INNER_T - 4, 2, "part")
        lk.text(ox, -SLEEVE_H / 2 - 9, "thumb knob")
        lk.text(ox, -SLEEVE_H / 2 - 18, "+ shoe")
    elif name == "B":
        lk.rect(ox, SLEEVE_H / 2 - WALL / 2, 6, WALL, "part", dashed=True)
        lk.rect(ox, INNER_H / 2 - 1.5, 6, 3, "cutout")
        lk.text(ox, -SLEEVE_H / 2 - 9, "flex tab clicks")
        lk.text(ox, -SLEEVE_H / 2 - 18, "into notches")
    else:
        lk.rect(ox, 0, SLEEVE_T + 10, SLEEVE_H + 10, "part", dashed=True)
        lk.text(ox, -SLEEVE_H / 2 - 9, "twist collar on")
        lk.text(ox, -SLEEVE_H / 2 - 18, "a split mouth")
lk.notes(
    "A thumb knob (stepless): M6 brass insert in the sleeve top, a printed thumb screw pushes a shoe onto the bar.",
    "  Any length, holds hard, one hand. Loosen, slide, tighten. Simplest and strongest.",
    "B click detent (stepped, every ~15 mm): a flexing tab in the sleeve wall drops into notches along the bar.",
    "  Pull/push to click, no knob -- same feel as the hinge. Holds less; a hard tug can click it in.",
    "C twist collar (tripod-leg style): threaded collar squeezes a slotted sleeve mouth. Stepless, but a",
    "  bulky printed thread at the arm tip, and the slotted mouth is the weakest place in ASA.",
)
lk.save(HERE / "layout_b_telescope_lock.svg")
print("wrote layout_b_telescope.svg, layout_b_telescope_lock.svg")
