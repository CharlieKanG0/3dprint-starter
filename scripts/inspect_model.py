"""Read a downloaded model (3MF or STL) and report, in plain words, what it is and what can be improved.

    ./venv/bin/python scripts/inspect_model.py ~/Downloads/some_model.3mf
    ./venv/bin/python scripts/inspect_model.py model.3mf --material ASA --write report.md

Reports: who made it and its licence; size and bed fit on YOUR printer (common/printer.py); whether
the shape is a closed solid that can be safely edited; the creator's print settings and result if
the file carries them; how much of the plastic is walls (which infill can't reduce) and an estimate
of grams and time for lighter settings. Run it before deciding how to change a model. See
docs/modifying.md. Needs no print profile and works for any file.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import meshmod, printplan, printer  # noqa: E402


def build_report(path: Path, material: str | None = None) -> str:
    mesh = meshmod.load_model(path)
    info = meshmod.source_info(path)
    h = meshmod.health(mesh)
    fit = meshmod.mesh_bed_fit(mesh)
    profile = printplan.read_profile(path)
    out: list[str] = [f"# {path.name}", ""]

    # -- who made it --------------------------------------------------------
    if info.title or info.designer or info.license:
        out.append(f"**{info.title or path.stem}**" + (f" by {info.designer}" if info.designer else "")
                   + (f". Licence: {info.license}. Check that it allows modified copies for your use." if info.license else ""))
        out.append("")

    # -- the shape ----------------------------------------------------------
    x, y, z = h.size
    out += ["## The shape", "",
            f"- Size **{x:.1f} x {y:.1f} x {z:.1f} mm** (units in the file: {info.unit}), {h.triangles:,} triangles, "
            f"{h.bodies} separate piece{'s' if h.bodies != 1 else ''}, {h.volume / 1000:.1f} cm3 of material.",
            f"- {fit.summary()}"]
    if h.usable:
        out.append("- **Closed solid: safe to add features to and cut from.**")
    else:
        out.append("- **Not a clean closed solid, so adding and cutting would fail or give wrong results:** "
                   + "; ".join(h.problems()) + ". Try `meshmod.repair()`; if it is still open, repair it in Orca or Bambu Studio first.")
    thickness = 2 * h.volume / h.area if h.area else 0.0
    out.append(f"- Typical wall thickness is about **{thickness:.1f} mm** (twice the volume over the surface area; "
               "exact only for a thin-walled shape).")
    out.append("")

    # -- the creator's print settings --------------------------------------
    if profile:
        out += ["## How the creator printed it", ""] + [f"- {ln}" for ln in profile.summary()]
        if profile.printer and printer.NAME.split()[-1] not in profile.printer:
            out.append(f"- **That is not your printer ({printer.NAME}).** Speeds, temperatures and the filament profile "
                       "must be re-chosen for yours; only the geometry carries over.")
        out.append("")
    else:
        out += ["## Print settings", "", "- The file carries none (geometry only), so the slicer's defaults apply.", ""]

    # -- where the plastic goes ---------------------------------------------
    base = profile or printplan.Profile(printer=printer.NAME, nozzle=printer.NOZZLE)
    flow = 9.0
    note = "assumed 9 mm3/s average flow"
    if profile and profile.weight_g and profile.time_s:
        flow, err = printplan.calibrate_flow(mesh, profile)
        note = f"time scaled to the creator's own slice ({flow:.1f} mm3/s average); weight estimate was {err:+.0%} off theirs before scaling"
    est = printplan.estimate(mesh, base, material, flow)
    out += ["## Where the plastic goes", ""]
    if est.solid_share > 0.9:
        out.append(f"- **About {est.solid_share:.0%} of the plastic is walls and top/bottom skin**, so the infill setting "
                   "barely changes the weight here. Savings come from fewer walls or a thinner model, not from infill.")
    else:
        out.append(f"- About {est.solid_share:.0%} of the plastic is walls and skin, {1 - est.solid_share:.0%} is infill. "
                   "Both settings matter.")
    out += [f"- Estimates below are ballpark (about +-25%, {note}); re-slice to confirm.", "",
            "| Settings | Plastic | Weight | Time vs as-downloaded |", "| --- | --- | --- | --- |"]
    options: list[tuple[str, printplan.Profile]] = []
    for walls in sorted({max(1, base.walls - 1), 2, 3}):
        if walls < base.walls:
            options.append((f"{walls} walls", replace(base, walls=walls)))
    for infill in (0.10, 0.05):
        if infill < base.infill:
            options.append((f"{base.walls} walls, {infill:.0%} infill", replace(base, infill=infill)))
    if base.walls > 2:
        options.append(("2 walls, 10% infill", replace(base, walls=2, infill=min(base.infill, 0.10))))
    rows = printplan.compare(mesh, base, options, material, flow)
    t0 = rows[0][1].seconds
    for label, e in rows:
        out.append(f"| {label} | {e.plastic_mm3 / 1000:.0f} cm3 | {e.grams:.0f} g | {e.seconds / 3600:.1f} h ({e.seconds / t0 - 1:+.0%}) |")
    mat = material or base.filament or "PLA"
    out += ["", f"Weights use {mat} at {printplan.DENSITY.get(mat, 1.24)} g/cm3 (typical; check your spool). Time assumes the same "
            "average flow as above: ASA and the CF blends usually print slower than PLA, so expect more. Fewer walls "
            "means a weaker part; keep 3+ walls anywhere that carries load or takes a screw.", ""]

    # -- next ---------------------------------------------------------------
    out += ["## What to do next", "",
            "| The change | Route |", "| --- | --- |",
            "| Lighter / faster only | Re-slice with fewer walls and your printer's profile. No model edit. |",
            "| Add or cut a feature (hole, boss, clamp, slot) | `scripts/new.py mod <name> <this file>`: sketch options, then edit the mesh. |",
            "| Change the model's own proportions | Rebuild it in build123d using this report and the sections as a guide. |", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", type=Path, help=".3mf or .stl")
    ap.add_argument("--material", help="PLA, PETG, ASA, ASA-CF, PETG-CF ... (changes density in the weight estimate)")
    ap.add_argument("--write", type=Path, help="also save the report to this file")
    args = ap.parse_args()
    if not args.file.exists():
        sys.exit(f"{args.file}: no such file")
    text = build_report(args.file, args.material)
    print(text)
    if args.write:
        args.write.write_text(text)
        print(f"\n(saved {args.write})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
