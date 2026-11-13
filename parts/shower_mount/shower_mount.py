"""Shower mount -- folding, height-adjustable arm on the roof-platform side rail.

A base bolts into the side rail's top T-channel (2x M6). A spring-loaded toothed
hinge on the base carries a telescopic arm: push the arm up or down and it clicks
every 9 deg from horizontal to 45 deg down (hard stop), or all the way up and over
onto the deck to stow. A round bar slides and rolls in the arm's sleeve: one thumb
knob locks both, so it sets the reach AND rolls the head fore/aft (15 deg ticks on
the sleeve mouth, a pointer line along the bar). At the arm tip a smaller toothed joint carries our own
compact claw, which snaps onto the shower handle directly and can be aimed 0-30 deg
toward the user. Both springs are hidden: each sits in a pocket in the arm, and the
knob's spigot slides in the pocket mouth.

Layout:    layout.py -> layout_b*.svg. Confirmed with the user 2026-11-13: layout B,
           toothed click hinge (no pull-pin), enclosed spring, own claw (no stock
           holster), tip joint integrated into the claw (T2). Then: telescopic arm,
           round bar (roll = a feature), thumb-knob lock (A) -- layout_b_telescope*.svg.

Coordinates (use frame): +X out from the vehicle, +Y along the vehicle, +Z up;
origin = top outer corner of the side rail. Arm angle THETA: 0 = horizontal out,
+ = up (stowed = 180), - = down (hard stop at -45).

Pieces (one STEP each, exported in print orientation, no supports):
  base       ASA-CF  plate on the rail + hinge lug + 45 deg stop.  Plate on the bed;
                     lug teeth on a vertical face.
  arm_sleeve ASA-CF  hinge hub + round sleeve + lock boss.  Teeth up; teardrop bore.
  arm_bar    ASA-CF  round sliding bar + tip joint.  Teeth up; a 1 mm flat on the bed.
  claw       ASA     snap claw + tip-joint boss.  Ring axis vertical (unfilled: it flexes).
  knob       ASA     main hinge knob (spigot covers the spring, M8 nyloc inside).
  tip_cap    ASA     tip-joint thumb cap (spigot covers the spring, M5 nyloc inside).
  lock_knob  ASA     telescope thumb knob (M6 hex bolt head pressed in from below).
  lock_shoe  ASA     pad between the lock bolt and the bar (drop it into the bore first).

Hardware (sizes printed when the script runs):
  2x M6 SHCS + channel nuts (base -> rail), 1x M8 hex bolt + nyloc + washer (hinge),
  1x M5 hex bolt + nyloc (tip), 1x M6 hex bolt + M6 brass heat-set insert (lock),
  1x compression spring 14 OD (hinge), 1x compression spring 8 OD (tip), stainless.

Deviations from the layout drawings (decided here, tell the user):
  * Each telescope section is kept under the P2S bed (256); that sets the travel.
  * Main hinge spring cover: the knob's spigot slides INSIDE the hub pocket (as at
    the tip) instead of a skirt over a boss, so the arm's back face is flat on the bed.
  * Claw sits on the +Y face of the arm tip (layout had -Y) so arm_bar prints teeth-up.
  * Hinge axis 50 above the rail top (layout: 10) so the hub clears the 12 mm plate.

ASSUMED (nothing below was measured -- confirm before printing a keeper):
  rail: top width 50, height 40, T-channel centred 20 in from the outer face, M6
  (given); body side 25 inboard of the rail face; handle 30 dia (given) with no
  shoulder; handset + hose share 0.6 kg; springs: hinge 14 OD, 150 N at 18 mm
  working length; tip 8 OD, 60 N at 8 mm; friction 0.3. All are parameters below.

Printer:   Bambu Lab P2S
Requires:  build123d (see /3dprint/requirements.txt)
Run:       ../../venv/bin/python shower_mount.py
Output:    shower_mount_<piece>.step (next to this script)
"""

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `common`

from build123d import *

from common.face_teeth import face_teeth, mesh_overlap, tooth_height
from common.hardware import COUNTERBORE, HEATSET, HEX_HEAD, NYLOC_NUT
from common.output import export_part, show_part
from common.params import param
from common.tolerances import FIT
from common.verify import assert_bbox, assert_single_solid, assert_volume, bed_fit, require_layout

HERE = Path(__file__).parent
require_layout(__file__)  # layout.py CONFIRMED records the user's choice (CLAUDE.md step 0)

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------

# --- Rail (ASSUMED except the M6) ---
RAIL_W, RAIL_H = 50.0, 40.0
CHANNEL_X = -20.0  # T-channel centre, from the rail's outer face
CHANNEL_BOLT = "M6"  # given by the user

# --- Base ---
BASE_T = 12.0  # plate thickness: M6 counterbore 6 deep leaves 6 under the head
PLATE_X0 = -45.0  # plate's inboard edge (rail top runs to -RAIL_W)
LUG_T = 20.0  # hinge lug thickness along Y
LUG_WALL = 3.0  # lug disc radius beyond the rosette
BOLT_EDGE = 12.0  # channel-bolt centre -> plate end
BOLT_CLEAR = 15.0  # channel-bolt centre -> lug / hub face (hex-key access)
BED_CHAMFER = 2.0  # bed-facing perimeter chamfer (house rule says ~3; plate is only 12 thick)

# --- Hinge (main toothed joint) ---
HX, HZ = 10.0, 50.0  # hinge axis position in the end view
TEETH = 40  # 9 deg per click
ROSETTE_R_IN, ROSETTE_R_OUT = 15.0, 25.0
HINGE_BOLT = "M8"
HUB_R = ROSETTE_R_OUT + 2.0
HUB_T = 34.0  # hub thickness along Y (the sleeve sits inside this slab)
SPRING_OD, SPRING_WORK_L, SPRING_F, SPRING_RATE = 14.0, 18.0, 150.0, 15.0  # ASSUMED
POCKET_CLR = 1.5  # spring -> pocket wall, radial
POCKET_FLOOR = 5.0  # hub material between pocket floor and the tooth face
MAX_DROP = 45.0  # hard stop, deg below horizontal
STOP_T = 8.0  # stop block thickness (normal to the beam face)
STOP_T0, STOP_T1 = 42.0, 64.0  # stop block extent along the beam from the hinge axis (past the root fillet)
STOP_CLR = 0.3  # the teeth seat the arm at -45, the stop just catches an overshoot

# --- Knob (main) ---
KNOB_D, KNOB_T = 40.0, 12.0
KNOB_RIM_GAP = 6.0  # knob flange -> hub face at the nominal setting
KNOB_GRIP_N, KNOB_GRIP_R = 10, 3.0  # scallops round the flange

# --- Telescopic arm ---
BAR_D = 24.0  # round sliding bar (about as stiff in the swing plane as the old 30x18 beam)
BAR_FLAT = 1.0  # flat along the bar's bed side so it prints lying down
SLIDE_CLR = FIT["loose"].radial  # bar in the sleeve bore, per side
SLEEVE_WALL = 3.5
SLEEVE_FLAT = 1.5  # flat on the sleeve's bed side (flush with the hub face)
BORE_X0 = 32.0  # bore starts clear of the hub (sleeve is solid to here)
SLEEVE_END = 220.0  # hub + sleeve = 247 < 256 bed
INNER_L = 225.0  # tip-joint axis -> bar end: bar piece = 225 + 15 = 240 < 256 bed
OVERLAP_MIN = 75.0  # bar never less than this deep in the sleeve (~3x its diameter)
EXTEND = param("EXTEND", 0.5)  # 0 = retracted .. 1 = fully out (viewer/render pose only)
ROLL = param("ROLL", 0.0)  # bar roll, deg (viewer/render pose only)
ROLL_TICK = 15.0  # tick marks on the sleeve mouth
TICK_DEPTH, TICK_W = 0.6, 1.0
LOCK_FROM_END = 15.0  # lock bolt axis -> sleeve mouth
LOCK_BOLT = "M6"
LOCK_BOSS_R = 7.5
LOCK_BOSS_H = 10.0  # boss stands this far proud of the sleeve
SHOE_T = 3.5
LOCK_KNOB_D, LOCK_KNOB_T, LOCK_KNOB_GAP = 26.0, 12.0, 2.0

# --- Tip joint + claw ---
TIP_TEETH = 24  # 15 deg per click
TIP_R_IN, TIP_R_OUT = 5.0, 12.0
TIP_R = 15.0  # tip disc = claw boss radius
TIP_BOLT = "M5"
TIP_SPRING_OD, TIP_SPRING_WORK_L, TIP_SPRING_F = 8.0, 8.0, 60.0  # ASSUMED
TIP_POCKET_CLR = 1.0
TIP_POCKET_FLOOR = 4.0
TIP_CAP_D, TIP_CAP_T = 20.0, 7.0
TIP_RIM_GAP = 3.0
TIP_GAP = 2.0  # arm tip disc -> outside of the claw ring (claw turns about the joint)
AIM_MAX = 30.0

HANDLE_D = 30.0  # given by the user (ASSUMED round, no shoulder)
CLAW_H = 30.0
CLAW_WALL = 4.0
CLAW_WRAP = 220.0  # deg of the handle the claw wraps; the rest is the mouth (faces +X)
CLAW_SNAP = param("CLAW_SNAP", 0.0)  # extra grip: claw bore this much under the handle dia
CLAW_BOSS_T = 10.0
MOUTH_TIP_R = 1.5  # rounded lips at the mouth = lead-in

CARRIED_KG = 0.6  # handset + water-filled hose share (ASSUMED)
MU = 0.3

SPIGOT_FIT = FIT["loose"].radial  # knob spigot sliding in a spring pocket

# ---------------------------------------------------------------------------
# Derived values + sanity assertions
# ---------------------------------------------------------------------------

_, B = face_teeth(TEETH, ROSETTE_R_IN, ROSETTE_R_OUT)  # main tooth half-band
_, BT = face_teeth(TIP_TEETH, TIP_R_IN, TIP_R_OUT)  # tip tooth half-band
R_MEAN = (ROSETTE_R_IN + ROSETTE_R_OUT) / 2
TIP_R_MEAN = (TIP_R_IN + TIP_R_OUT) / 2

# Y layout (use frame). Tooth mid-plane of the main hinge at y = 0.
Y_LUG0, Y_LUG1 = -B - LUG_T, -B
Y_HUB0, Y_HUB1 = B, B + HUB_T
SLEEVE_R = BAR_D / 2 + SLIDE_CLR + SLEEVE_WALL
BORE_R = BAR_D / 2 + SLIDE_CLR
Y_AX = Y_HUB1 - (SLEEVE_R - SLEEVE_FLAT)  # telescope axis (along X, at z = 0)
# Tip disc: as thick as the bar, bed flat flush with the bar's flat.
Y_TIP0, Y_TIP1 = Y_AX - BAR_D / 2 + BAR_FLAT, Y_AX + BAR_D / 2
# Tip: teeth on the tip's +Y face; claw boss beyond; tip cap on the -Y face.
Y_TIPMID = Y_TIP1 + BT
Y_BOSS0, Y_BOSS1 = Y_TIPMID + BT, Y_TIPMID + BT + CLAW_BOSS_T

POCKET_R = SPRING_OD / 2 + POCKET_CLR
POCKET_DEPTH = HUB_T - POCKET_FLOOR
SPIGOT_IN = POCKET_DEPTH - SPRING_WORK_L  # knob spigot inside the pocket at nominal
TIP_POCKET_R = TIP_SPRING_OD / 2 + TIP_POCKET_CLR
TIP_POCKET_DEPTH = (Y_TIP1 - Y_TIP0) - TIP_POCKET_FLOOR
TIP_SPIGOT_IN = TIP_POCKET_DEPTH - TIP_SPRING_WORK_L

HANDLE_OFFSET = HANDLE_D / 2 + CLAW_WALL + TIP_R + TIP_GAP  # tip joint axis -> handle axis
CLAW_RI = HANDLE_D / 2 - CLAW_SNAP / 2
CLAW_RO = HANDLE_D / 2 + CLAW_WALL

L_MIN = BORE_X0 + INNER_L  # hinge -> tip joint, bar fully in
L_MAX = SLEEVE_END - OVERLAP_MIN + INNER_L  # hinge -> tip joint, fully out
L_POSE = L_MIN + EXTEND * (L_MAX - L_MIN)
LOCK_X = SLEEVE_END - LOCK_FROM_END
Y_LOCK_TOP = Y_AX - SLEEVE_R - LOCK_BOSS_H  # boss top (lock is on the -Y side = up when printing)

T_GRAV = CARRIED_KG * 9.81 * (L_MAX + HANDLE_OFFSET) / 1000
T_SLIP = SPRING_F * R_MEAN / 1000 * math.tan(math.radians(45) + math.atan(MU))
TIP_T_GRAV = CARRIED_KG * 9.81 * HANDLE_OFFSET / 1000
TIP_T_SLIP = TIP_SPRING_F * TIP_R_MEAN / 1000 * math.tan(math.radians(45) + math.atan(MU))

assert HZ - HUB_R >= BASE_T + 2.0, "hub drags on the base plate"
assert POCKET_R < ROSETTE_R_IN, "spring pocket cuts into the tooth band"
assert SPIGOT_IN >= 5.0, f"knob spigot only {SPIGOT_IN:.1f} into the pocket -- spring shows when loosened"
assert KNOB_RIM_GAP > tooth_height(TEETH, ROSETTE_R_OUT), "knob rim would stop the hub lifting a tooth"
assert TIP_SPIGOT_IN >= 4.0, f"tip cap spigot only {TIP_SPIGOT_IN:.1f} into its pocket"
assert TIP_POCKET_R < TIP_R_IN + 1.0 or TIP_POCKET_R < TIP_R, "tip pocket larger than the tip"
assert HANDLE_OFFSET - CLAW_RO - TIP_R >= TIP_GAP - 1e-9, "arm tip rubs the claw ring"
assert T_SLIP / T_GRAV >= 1.5, f"hinge holds only {T_SLIP / T_GRAV:.1f}x the handset weight"
assert TIP_T_SLIP / TIP_T_GRAV >= 2.0, f"tip joint holds only {TIP_T_SLIP / TIP_T_GRAV:.1f}x"
assert HUB_R + SLEEVE_END <= 252 and INNER_L + TIP_R <= 252, "a telescope section is longer than the bed"
assert Y_AX - SLEEVE_R > Y_HUB0 + 2.0, "sleeve pokes past the hub's tooth face"
assert LOCK_X - LOCK_BOSS_R > SLEEVE_END - OVERLAP_MIN, "lock is not over the bar at full extension"
assert LOCK_BOSS_H + SLEEVE_WALL >= HEATSET[LOCK_BOLT].hole_depth + SHOE_T + 0.5, "lock boss too short for insert + shoe"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def on_y(shape, y_face: float, toward: int):
    """Turn a +Z-built feature so +Z points along `toward`*Y, then put its z=0 at y = y_face."""
    rot = Rot(-90, 0, 0) if toward > 0 else Rot(90, 0, 0)  # Rot(X=-90): +Z -> +Y
    return Pos(0, y_face, 0) * (rot * shape)


def y_cyl(r: float, y0: float, y1: float, x: float = 0.0, z: float = 0.0):
    """Cylinder about an axis parallel to Y, from y0 to y1, at (x, z)."""
    return Pos(x, 0, z) * on_y(Cylinder(r, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN)), y0, +1)


def y_hex(af: float, y0: float, y1: float, x: float = 0.0, z: float = 0.0):
    """Hex prism (across-flats `af`, slip fit added) about an axis parallel to Y."""
    hexagon = extrude(RegularPolygon(af / 2 + FIT["slip"].radial, 6, major_radius=False), y1 - y0)
    return Pos(x, 0, z) * on_y(hexagon, y0, +1)


def xz_prism(face: Face, y0: float, y1: float):
    """Extrude a face drawn in the XZ plane (Plane.XZ: local x -> X, local y -> Z) from y0 to y1."""
    solid = extrude(face, y1 - y0)  # Plane.XZ normal is -Y, so extrude goes toward -Y
    bb = solid.bounding_box()
    return Pos(0, y1 - bb.max.Y, 0) * solid


def xz_poly(pts) -> Face:
    return Face(Wire.make_polygon([Vector(x, 0, z) for x, z in pts], close=True))


def xz_disc(cx: float, cz: float, r: float) -> Face:
    return Pos(cx, 0, cz) * Face(Wire.make_circle(r, Plane.XZ))


def xz_rect(x0, x1, z0, z1) -> Face:
    return xz_poly([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])


def swing(shape, theta: float):
    """Rotate a shape built with the hinge on the origin up by `theta` deg about Y, then put it on the hinge."""
    return Pos(HX, 0, HZ) * (Rot(0, -theta, 0) * shape)


# ---------------------------------------------------------------------------
# Base: plate on the rail + hinge lug (teeth on its +Y face) + 45 deg stop
# ---------------------------------------------------------------------------

lug_r = ROSETTE_R_OUT + LUG_WALL
y_bolt0 = Y_LUG0 - BOLT_CLEAR  # channel bolt before the lug
y_bolt1 = Y_HUB1 + BOLT_CLEAR  # channel bolt past the hub
plate_y0, plate_y1 = y_bolt0 - BOLT_EDGE, y_bolt1 + BOLT_EDGE

plate = Pos((PLATE_X0 + 0) / 2, (plate_y0 + plate_y1) / 2, BASE_T / 2) * Box(-PLATE_X0, plate_y1 - plate_y0, BASE_T)
lug_profile = xz_rect(HX - lug_r, HX + lug_r, 0, HZ) + xz_disc(HX, HZ, lug_r)
lug = xz_prism(lug_profile, Y_LUG0, Y_LUG1)

# Stop block: its contact face is the plane of the beam's lower face at THETA = -45.
d = Vector(math.cos(math.radians(-MAX_DROP)), 0, math.sin(math.radians(-MAX_DROP)))
n = Vector(d.Z, 0, -d.X)  # in-plane normal pointing to the "more down" side
h = Vector(HX, 0, HZ)
_o0 = SLEEVE_R + STOP_CLR
corners = [h + d * t + n * o for t, o in ((STOP_T0, _o0), (STOP_T1, _o0),
                                          (STOP_T1, _o0 + STOP_T), (STOP_T0, _o0 + STOP_T))]
stop_face = xz_poly([(p.X, p.Z) for p in corners]) & xz_rect(-100, 200, 0, 200)  # keep it above the bed
stop = xz_prism(stop_face, Y_LUG0, Y_HUB1)

# face_teeth spans z in [-B, B] with the mid-plane at 0: put the mid-plane at y = 0 and point it +Y.
teeth_lug, _ = face_teeth(TEETH, ROSETTE_R_IN, ROSETTE_R_OUT)
teeth_lug = Pos(HX, 0, HZ) * on_y(teeth_lug, 0.0, +1)

ch = COUNTERBORE[CHANNEL_BOLT]
hb = COUNTERBORE[HINGE_BOLT]
head = HEX_HEAD[HINGE_BOLT]
HEAD_POCKET = head.thickness + 0.5
cutters = [
    y_cyl(hb.clearance_dia / 2, Y_LUG0 - 1, B + 1, HX, HZ),  # hinge bolt
    y_hex(head.across_flats, Y_LUG0 - 1, Y_LUG0 + HEAD_POCKET, HX, HZ),  # bolt head can't spin
]

for yb in (y_bolt0, y_bolt1):  # channel bolts: counterbored from the top of the plate
    cutters += [
        Pos(CHANNEL_X, yb, -1) * Cylinder(ch.clearance_dia / 2, BASE_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(CHANNEL_X, yb, BASE_T - ch.counterbore_depth)
        * Cylinder(ch.counterbore_dia / 2, ch.counterbore_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)),
    ]
# bed chamfer on the plate's bottom perimeter (the lug/stop footprints beyond it are short)
plate = chamfer(plate.edges().group_by(Axis.Z)[0], BED_CHAMFER)
base = Part() + [plate, lug, stop, teeth_lug] - cutters

# ---------------------------------------------------------------------------
# Telescopic arm. Sleeve: built with the hinge on the origin, axis along +X at
# (Y_AX, z=0), THETA = 0. Bar: built with the tip joint on the origin (it slides
# to x = L and rolls about the telescope axis).
# ---------------------------------------------------------------------------


def x_cyl(r: float, x0: float, x1: float, y: float = Y_AX, z: float = 0.0):
    """Cylinder about an axis parallel to X, from x0 to x1, at (y, z)."""
    return Pos(x0, y, z) * (Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN)))


def roll_about_axis(shape, deg: float):
    return Pos(0, Y_AX, 0) * (Rot(deg, 0, 0) * (Pos(0, -Y_AX, 0) * shape))


BIG = 600.0
hub = y_cyl(HUB_R, Y_HUB0, Y_HUB1)
sleeve = x_cyl(SLEEVE_R, 0, SLEEVE_END) & Pos(0, Y_HUB1 - BIG / 2, 0) * Box(BIG, BIG, BIG)  # bed flat
lock_boss = y_cyl(LOCK_BOSS_R, Y_LOCK_TOP, Y_AX, LOCK_X, 0)
teeth_hub, _ = face_teeth(TEETH, ROSETTE_R_IN, ROSETTE_R_OUT, phase_deg=180.0 / TEETH)
teeth_hub = on_y(teeth_hub, 0.0, -1)
# teardrop bore: round + a 45 deg peak toward -Y (= up when printing), so the ceiling needs no support
peak = BORE_R * math.sqrt(2)
drop = Face(Wire.make_polygon([Vector(0, -BORE_R * math.sqrt(0.5), BORE_R * math.sqrt(0.5)), Vector(0, -peak, 0),
                               Vector(0, -BORE_R * math.sqrt(0.5), -BORE_R * math.sqrt(0.5))], close=True))
bore = x_cyl(BORE_R, BORE_X0, SLEEVE_END + 1) + Pos(BORE_X0, Y_AX, 0) * extrude(drop, SLEEVE_END + 1 - BORE_X0, dir=(1, 0, 0))
ticks = []
for k in range(int(360 / ROLL_TICK)):
    a_deg = k * ROLL_TICK
    tick_len = 3.0 if a_deg % 45 else 4.5 if a_deg else 6.0  # longer every 45, longest at 0 (= +Z, up)
    tick = Pos(SLEEVE_END, Y_AX, 0) * (Rot(-a_deg, 0, 0) * Pos(0, 0, SLEEVE_R - tick_len / 2 + 0.01)
                                         * Box(2 * TICK_DEPTH, TICK_W, tick_len))
    ticks.append(tick)
hs_lock = HEATSET[LOCK_BOLT]
arm_sleeve = (Part() + [hub, sleeve, lock_boss, teeth_hub]) - [
    y_cyl(hb.clearance_dia / 2, Y_HUB0 - B - 1, Y_HUB1 + 1),  # hinge bolt
    y_cyl(POCKET_R, Y_HUB1 - POCKET_DEPTH, Y_HUB1 + 1),  # hinge spring pocket, from the +Y face
    bore,
    y_cyl(hs_lock.hole_dia / 2, Y_LOCK_TOP - 1, Y_AX, LOCK_X, 0),  # insert on top, shoe below it
] - ticks

tb = COUNTERBORE[TIP_BOLT]
bar_x0 = -INNER_L
bar = x_cyl(BAR_D / 2, bar_x0, -TIP_R + 2.0) & Pos(0, Y_TIP0 + BIG / 2, 0) * Box(BIG, BIG, BIG)  # bed flat
tip = y_cyl(TIP_R, Y_TIP0, Y_TIP1)
teeth_tip, _ = face_teeth(TIP_TEETH, TIP_R_IN, TIP_R_OUT)
teeth_tip = on_y(teeth_tip, Y_TIPMID, +1)
pointer = Pos((bar_x0 - TIP_R) / 2, Y_AX, BAR_D / 2) * Box(-bar_x0 - TIP_R - 4, TICK_W, 2 * TICK_DEPTH)  # roll pointer, +Z
arm_bar = (Part() + [bar, tip, teeth_tip]) - [
    pointer,
    y_cyl(tb.clearance_dia / 2, Y_TIP0 - 1, Y_TIPMID + BT + 1),  # tip bolt
    y_cyl(TIP_POCKET_R, Y_TIP0 - 1, Y_TIP0 + TIP_POCKET_DEPTH),  # tip spring pocket, -Y face
]

# lock: thumb knob with an M6 hex bolt head pressed in from below; the shoe sits in the
# hole under the insert and pads the bolt end against the bar
lock_head = HEX_HEAD[LOCK_BOLT]
y_lk1 = Y_LOCK_TOP - LOCK_KNOB_GAP
lock_knob = y_cyl(LOCK_KNOB_D / 2, y_lk1 - LOCK_KNOB_T, y_lk1, LOCK_X, 0) - [
    Pos(LOCK_X + LOCK_KNOB_D / 2 * math.cos(2 * math.pi * k / 8), 0, LOCK_KNOB_D / 2 * math.sin(2 * math.pi * k / 8))
    * y_cyl(2.5, y_lk1 - LOCK_KNOB_T - 1, y_lk1 + 1) for k in range(8)
] - [
    y_hex(lock_head.across_flats, y_lk1 - lock_head.thickness - 0.3, y_lk1 + 1, LOCK_X, 0),
    y_cyl(COUNTERBORE[LOCK_BOLT].clearance_dia / 2, y_lk1 - LOCK_KNOB_T + 2.0, y_lk1 + 1, LOCK_X, 0),
]
y_shoe1 = Y_AX - BORE_R  # shoe rests on the bar's top (bore surface)
lock_shoe = y_cyl(hs_lock.hole_dia / 2 - FIT["loose"].radial, y_shoe1 - SHOE_T, y_shoe1, LOCK_X, 0)
lock_bolt_len = (Y_AX - BORE_R - SHOE_T) - (y_lk1 - lock_head.thickness - 0.3)  # head seat -> shoe, locked

# ---------------------------------------------------------------------------
# Claw (built with the tip joint on the origin, axis along Y, aim 0)
# ---------------------------------------------------------------------------

y_ring = (Y_BOSS0 + Y_BOSS1) / 2  # ring centred on the boss slab
ring = Pos(HANDLE_OFFSET, y_ring, 0) * (Cylinder(CLAW_RO, CLAW_H) - Cylinder(CLAW_RI, CLAW_H))
mouth_half = math.radians((360.0 - CLAW_WRAP) / 2)
mouth = Pos(HANDLE_OFFSET, y_ring, 0) * extrude(
    Polygon((0, 0), (3 * CLAW_RO * math.cos(mouth_half), 3 * CLAW_RO * math.sin(mouth_half)),
            (3 * CLAW_RO * math.cos(mouth_half), -3 * CLAW_RO * math.sin(mouth_half)), align=None),
    CLAW_H, both=True)
ring = ring - mouth
lip_r_mid = (CLAW_RI + CLAW_RO) / 2
lips = [Pos(HANDLE_OFFSET + lip_r_mid * math.cos(mouth_half), y_ring + s * lip_r_mid * math.sin(mouth_half), 0)
        * Cylinder(CLAW_WALL / 2, CLAW_H) for s in (1, -1)]
boss_profile = (xz_disc(0, 0, TIP_R) + xz_rect(-TIP_R, TIP_R, -CLAW_H / 2, 0)
                + xz_rect(0, HANDLE_OFFSET - CLAW_RI, -CLAW_H / 2, CLAW_H / 2))
boss = xz_prism(boss_profile, Y_BOSS0, Y_BOSS1)
teeth_claw, _ = face_teeth(TIP_TEETH, TIP_R_IN, TIP_R_OUT, phase_deg=180.0 / TIP_TEETH)
teeth_claw = on_y(teeth_claw, Y_TIPMID, -1)
tip_head = HEX_HEAD[TIP_BOLT]
claw = (Part() + [ring, boss, teeth_claw] + lips) - [
    Pos(HANDLE_OFFSET, y_ring, 0) * Cylinder(CLAW_RI, CLAW_H * 2),  # keep the bore clean of the web
    y_cyl(tb.clearance_dia / 2, Y_TIPMID - BT - 1, Y_BOSS1 + 1),
    y_hex(tip_head.across_flats, Y_BOSS1 - tip_head.thickness - 0.5, Y_BOSS1 + 1),
]

# ---------------------------------------------------------------------------
# Knob + tip cap (built on their joint axes, in place at the nominal setting)
# ---------------------------------------------------------------------------

nut8 = NYLOC_NUT[HINGE_BOLT]
y_knob_in = Y_HUB1 + KNOB_RIM_GAP
knob_flange = y_cyl(KNOB_D / 2, y_knob_in, y_knob_in + KNOB_T)
scallops = [Pos(KNOB_D / 2 * math.cos(2 * math.pi * k / KNOB_GRIP_N), 0, KNOB_D / 2 * math.sin(2 * math.pi * k / KNOB_GRIP_N))
            * y_cyl(KNOB_GRIP_R, y_knob_in - 1, y_knob_in + KNOB_T + 1) for k in range(KNOB_GRIP_N)]
knob_spigot = y_cyl(POCKET_R - SPIGOT_FIT, Y_HUB1 - SPIGOT_IN, y_knob_in)
knob = (knob_flange + knob_spigot) - scallops - [
    y_cyl(hb.clearance_dia / 2, Y_HUB1 - SPIGOT_IN - 1, y_knob_in + KNOB_T + 1),
    y_hex(nut8.across_flats, y_knob_in + KNOB_T - nut8.thickness, y_knob_in + KNOB_T + 1),
]

nut5 = NYLOC_NUT[TIP_BOLT]
y_cap_out = Y_TIP0 - TIP_RIM_GAP
cap = (y_cyl(TIP_CAP_D / 2, y_cap_out - TIP_CAP_T, y_cap_out)
       + y_cyl(TIP_POCKET_R - SPIGOT_FIT, y_cap_out, Y_TIP0 + TIP_SPIGOT_IN)) - [
    y_cyl(tb.clearance_dia / 2, y_cap_out - TIP_CAP_T - 1, Y_TIP0 + TIP_SPIGOT_IN + 1),
    y_hex(nut5.across_flats, y_cap_out - TIP_CAP_T - 1, y_cap_out - TIP_CAP_T + nut5.thickness),
]
tip_cap = cap  # tip-local, like the bar

# ---------------------------------------------------------------------------
# Fit checks in the use frame
# ---------------------------------------------------------------------------

rail = Pos(-RAIL_W / 2, 0, -RAIL_H / 2) * Box(RAIL_W, 400, RAIL_H)
handset = Pos(HANDLE_OFFSET, y_ring, 0) * Pos(0, 0, (CLAW_H / 2 + 45 - (CLAW_H / 2 + 150)) / 2) * Cylinder(HANDLE_D / 2, 45 + CLAW_H + 150)


def claw_group(aim: float):
    """Claw + handset about the tip joint, aimed `aim` deg (spray end toward +X)."""
    return [Rot(0, aim, 0) * claw, Rot(0, aim, 0) * handset]


def bar_group(L: float, roll: float, aim: float):
    """Everything carried by the bar, slid out to hinge->tip = L and rolled: bar, tip cap, claw, handset."""
    c, hs = claw_group(aim)
    return [Pos(L, 0, 0) * roll_about_axis(x, roll) for x in (arm_bar, tip_cap, c, hs)]


def whole_arm(L: float, roll: float = 0.0):
    bar_p, cap_p, _, _ = bar_group(L, roll, 0.0)
    return Part() + [arm_sleeve, bar_p, cap_p, lock_shoe]


# telescope: bar slides and rolls freely in the bore, lands on the bore floor when retracted
for L in (L_MIN, L_MAX):
    for roll in (0.0, 37.0):
        bar_p = bar_group(L, roll, 0.0)[0]
        assert mesh_overlap(arm_sleeve, bar_p) < 1e-3, f"bar binds in the sleeve at L={L:.0f}, roll {roll}"
        assert mesh_overlap(bar_p, lock_shoe) < 1e-3, "bar hits the lock shoe"
assert mesh_overlap(arm_sleeve, lock_shoe) < 1e-3 and mesh_overlap(arm_sleeve, lock_knob) < 1e-3, "lock parts collide"
# hinge: teeth mesh at the clicks, miss at half a click, stop catches past -45, stowed and rail clear
arm_max = whole_arm(L_MAX)
for theta in (0.0, -9.0 * 2, -MAX_DROP):
    ov = mesh_overlap(swing(arm_max, theta), base)
    assert ov < 15.0, f"arm and base overlap {ov:.1f} mm^3 at {theta} deg -- teeth out of phase or a collision"
ov = mesh_overlap(swing(arm_max, 4.5), base)
assert ov > 100.0, f"half-click overlap only {ov:.1f} -- the tooth check isn't seeing the teeth"
assert mesh_overlap(swing(arm_max, -MAX_DROP - 3), base) > 100.0, "no hard stop below -45 deg"
assert mesh_overlap(swing(arm_max + lock_knob, 180.0), base) < 15.0, "stowed arm hits the base"
for theta in (0.0, -MAX_DROP, 180.0):
    assert mesh_overlap(swing(arm_max + lock_knob, theta), rail) < 1e-3, f"arm hits the rail at {theta} deg"
assert mesh_overlap(base, rail) < 1e-3, "base sits inside the rail"
# claw + handset clear the arm at both ends of the travel, every aim, rolled +-45
for L in (L_MIN, L_MAX):
    arm_l = Part() + [arm_sleeve, lock_knob]
    for roll in (-45.0, 0.0, 45.0):
        for aim in (0.0, AIM_MAX):
            bar_p, cap_p, c, hs = bar_group(L, roll, aim)
            ov = mesh_overlap(bar_p + cap_p, c)
            assert ov < 5.0, f"claw/tip overlap {ov:.1f} mm^3 at L={L:.0f}, roll {roll}, aim {aim}"
            assert mesh_overlap(arm_l, c) < 1e-3, f"claw hits the sleeve at L={L:.0f}, roll {roll}, aim {aim}"
            assert mesh_overlap(arm_l + bar_p, hs) < 1e-3, f"handset hits the arm at L={L:.0f}, roll {roll}, aim {aim}"
assert mesh_overlap(arm_sleeve, knob) < 1e-3 and mesh_overlap(arm_bar, tip_cap) < 1e-3, "knob/cap collide"

# bolt lengths (head seat -> outer face of the nut pocket)
hinge_bolt_len = (y_knob_in + KNOB_T) - (Y_LUG0 + HEAD_POCKET)
tip_bolt_len = (Y_BOSS1 - tip_head.thickness - 0.5) - (y_cap_out - TIP_CAP_T)

# ---------------------------------------------------------------------------
# Print orientation + verify
# ---------------------------------------------------------------------------


def to_bed(shape):
    bb = shape.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * shape


def print_pose(shape, up: str):
    """`up` = the use-frame direction that faces up on the bed: '+Y', '-Y' or '+Z'."""
    rot = {"+Y": Rot(90, 0, 0), "-Y": Rot(-90, 0, 0), "+Z": Rot(0, 0, 0)}[up]  # Rot(X=90): +Y -> +Z
    return to_bed(rot * shape)


pieces = {
    "base": print_pose(base, "+Z"),
    "arm_sleeve": print_pose(arm_sleeve, "-Y"),  # hub teeth + lock boss face -Y -> up
    "arm_bar": print_pose(arm_bar, "+Y"),  # tip teeth face +Y -> up
    "claw": print_pose(claw, "+Z"),
    "knob": print_pose(knob, "-Y"),  # spigot points -Y -> up, flange on the bed
    "tip_cap": print_pose(tip_cap, "+Y"),  # spigot points +Y -> up
    "lock_knob": print_pose(lock_knob, "-Y"),  # top face on the bed, bolt-head pocket up
    "lock_shoe": print_pose(lock_shoe, "-Y"),  # flat disc
}

EXPECT_VOL = {  # mm^3 as built 2026-11-13 (telescopic arm), +-15 %: a broken boolean moves these a lot
    "base": 137_000, "arm_sleeve": 129_200, "arm_bar": 109_100, "claw": 17_500, "knob": 14_500,
    "tip_cap": 2_490, "lock_knob": 4_880, "lock_shoe": 155,
}
for name, p in pieces.items():
    assert_single_solid(p)
    bb = p.bounding_box()
    assert_bbox(p, (bb.size.X, bb.size.Y, bb.size.Z))  # on the bed (min Z = 0)
    if os.environ.get("SHOWER_PRINT_VOLUMES"):
        print(f"  {name}: {p.volume:.0f}")
    else:
        v = EXPECT_VOL[name]
        assert_volume(p, v * 0.85, v * 1.15)
    fit = bed_fit(p)
    assert fit.fits, f"{name}: {fit.summary()}"
    print(f"{name:10s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f}  vol {p.volume / 1000:6.1f} cm^3  | "
          f"{fit.summary()}")

print(f"Hinge: {TEETH} teeth ({360 / TEETH:.0f} deg/click), slip {T_SLIP:.1f} Nm vs handset {T_GRAV:.1f} Nm "
      f"({T_SLIP / T_GRAV:.1f}x). Tip: {TIP_TEETH} teeth, slip {TIP_T_SLIP:.2f} vs {TIP_T_GRAV:.2f} Nm "
      f"({TIP_T_SLIP / TIP_T_GRAV:.0f}x).")
print(f"Hardware: hinge {HINGE_BOLT} hex bolt >= {hinge_bolt_len:.0f} long (+ nyloc), tip {TIP_BOLT} hex bolt "
      f">= {tip_bolt_len:.0f} long (+ nyloc), lock {LOCK_BOLT} hex bolt ~{lock_bolt_len:.0f} long + {LOCK_BOLT} heat-set insert, "
      f"2x {CHANNEL_BOLT} SHCS x {BASE_T - ch.counterbore_depth + 8:.0f} + channel nuts.")
c45 = math.cos(math.radians(MAX_DROP))
print(f"Telescope: hinge->tip {L_MIN:.0f}-{L_MAX:.0f}. Reach from the rail face at 0 deg "
      f"{HX + L_MIN + HANDLE_OFFSET:.0f}-{HX + L_MAX + HANDLE_OFFSET:.0f}, at {MAX_DROP:.0f} deg "
      f"{HX + L_MIN * c45 + HANDLE_OFFSET:.0f}-{HX + L_MAX * c45 + HANDLE_OFFSET:.0f}; "
      f"drop at the stop {L_MIN * c45:.0f}-{L_MAX * c45:.0f}.")

# ---------------------------------------------------------------------------
# Export + live view
# ---------------------------------------------------------------------------

for name, p in pieces.items():
    export_part(p, HERE / f"shower_mount_{name}.step")
th, aim = -18.0, 15.0  # viewer/render pose; EXTEND and ROLL set the telescope
bar_p, cap_p, c, hs = bar_group(L_POSE, ROLL, aim)
scene = [base, swing(arm_sleeve, th), swing(lock_knob, th), swing(lock_shoe, th), swing(knob, th),
         swing(bar_p, th), swing(cap_p, th), swing(c, th), swing(hs, th), rail]
scene_names = ["base", "arm_sleeve", "lock_knob", "lock_shoe", "knob", "arm_bar", "tip_cap", "claw",
               "handset (ref)", "rail (ref)"]
if os.environ.get("PART_RENDER"):  # also a mounted preview
    export_part(Compound(scene), HERE / "shower_mount_zz_mounted.step")
show_part(*scene, names=scene_names,
          colors=["#e8e8e8", "#3a7bd5", "#d08a2e", "#d08a2e", "#d08a2e", "#16a085", "#d08a2e", "#8e44ad",
                  "#4caf50", "#666666"])
