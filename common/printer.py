"""Your printer -- the one place to describe it. Edit these to match yours.

Every part reads the bed size from here (common/verify.py's `bed_fit`), and
CLAUDE.md tells the agent to design against these numbers. Defaults are a
Bambu Lab P1S/P2S/X1C-class machine (256 x 256 x 256 mm, 0.4 mm nozzle).

Common beds, for reference:  Bambu A1 256x256x256, A1 mini 180x180x180,
Prusa MK4 250x210x220, Prusa Core One 250x220x270, Ender-3 V3 220x220x250.
"""

NAME = "Bambu Lab P2S"
BED = (256.0, 256.0)  # usable X, Y in mm
MAX_Z = 256.0  # build height, mm
NOZZLE = 0.4  # mm
BED_MARGIN = 2.0  # keep-out around the bed edge, mm per side
