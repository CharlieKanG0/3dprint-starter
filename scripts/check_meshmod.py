"""Self-check for the downloaded-model workflow (common/meshmod.py, common/printplan.py).

    ./venv/bin/python scripts/check_meshmod.py

Builds its own test models (no downloads) and proves, with positive and negative controls, that:
  - an STL made from an unrelated shape (a bracket) loads, edits, and passes the probes;
  - a 3MF in inches, with a mirrored build transform and a component in a separate file (the way
    Bambu Studio / Orca store models), comes out in millimetres with a valid, outward-facing mesh;
  - a hole probe really does fail when the hole is in the wrong place;
  - a mesh with a gap is reported as unusable, refused by apply_changes, and fixed by repair;
  - what write_3mf writes reads back unchanged;
  - the filament estimate behaves (fewer walls, less plastic; a solid wall ignores infill);
  - a sketch turned to its installed orientation (`Sketch(down=...)` / `turn=`) puts things where they should be
    and labels the axes right, for a mesh slice and a plain shape alike;
  - line_spans measures walls and gaps along a line, from outside or from inside the solid;
  - test_piece cuts a short closed slice where asked, from a mesh or a build123d shape;
  - snap makes an addition meant to be flush with a face exactly flush (no hairline step).
Run by scripts/build_all.py, so a change to common/ can't silently break the workflow.
"""

import io
import sys
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from build123d import Box, Cylinder, Pos, Rot, export_stl  # noqa: E402

from common import meshmod as mm  # noqa: E402
from common import printplan as pp  # noqa: E402
from common.sketch import Sketch, turn_for  # noqa: E402


def raises(fn, what: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise SystemExit(f"FAIL: {what} should have been refused but was not")


def bracket_stl(path: Path) -> None:
    """An L-bracket, nothing to do with any particular model."""
    shape = Pos(0, 0, 2.5) * Box(60, 30, 5) + Pos(-27.5, 0, 22.5) * Box(5, 30, 45)  # upright overlaps the slab: 45 tall, 5 thick
    export_stl(shape, str(path))


def three_mf_inches(path: Path) -> None:
    """A 1 x 2 x 3 inch box in a component file, placed by a mirrored (det < 0) build transform."""
    box = trimesh.creation.box((1, 2, 3))
    box.apply_translation(box.extents / 2)  # corner at the origin, so faces/winding are plain
    v = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in box.vertices)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in box.faces)
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"'
    part = f'<model unit="inch" {ns}><resources><object id="1"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object></resources></model>'
    main = (f'<model unit="inch" {ns}><resources><object id="2"><components>'
            '<component p:path="/3D/Objects/o.model" objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object></resources>'
            '<build><item objectid="2" transform="-1 0 0 0 1 0 0 0 1 10 20 5"/></build></model>')  # mirror X, move
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("3D/3dmodel.model", main)
        zf.writestr("3D/Objects/o.model", part)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="meshmod_check_"))

    # 1. unrelated shape, end to end -------------------------------------------------
    stl = tmp / "bracket.stl"
    bracket_stl(stl)
    base = mm.load_model(stl)
    assert mm.health(base).usable and abs(base.volume - (60 * 30 * 5 + 5 * 30 * 40)) < 1, "bracket volume"
    mm.assert_mesh_bbox(base, (60, 30, 45))
    hole = Pos(10, 0, 2.5) * Cylinder(3, 20)
    boss = Pos(-27.5, 0, 22.5) * (Rot(0, 90, 0) * Cylinder(8, 12))  # a pad on the upright, away from the horizontal hole
    out = mm.apply_changes(base, add=[boss], cut=[hole])
    mm.assert_watertight(out)
    mm.assert_single_body(out)
    mm.assert_solid_at(base, (10, 0, 2.5))   # positive control: material there before the cut
    mm.assert_void_at(out, (10, 0, 2.5))     # the hole is open
    mm.assert_solid_at(out, (10 + 5, 0, 2.5))  # and only there
    raises(lambda: mm.assert_void_at(out, (10 + 15, 0, 2.5)), "a void probe where there is material")  # negative control
    assert out.extents[0] > base.extents[0] - 1e-6 and out.volume != base.volume
    assert mm.mesh_bed_fit(out).fits
    loops = mm.section_loops(base, "y")
    assert loops and max(len(lp) for lp in loops) >= 6, "section of an L profile"

    # 2. 3MF dialect: inches, component file, mirrored transform ------------------------
    f = tmp / "inches.3mf"
    three_mf_inches(f)
    m = mm.load_model(f)
    assert np.allclose(sorted(m.extents), [25.4, 50.8, 76.2], atol=1e-3), f"inch box extents {m.extents}"
    assert m.volume > 0 and m.is_watertight and m.is_winding_consistent, "mirrored transform must keep faces outward"
    assert abs(m.volume - 25.4 * 50.8 * 76.2) < 5, "inch box volume"

    # 3. write_3mf round trip ----------------------------------------------------------
    r = mm.load_model(mm.write_3mf(out, tmp / "out.3mf", name="out"))
    assert abs(r.volume - out.volume) < 0.5 and np.allclose(r.extents, out.extents, atol=1e-3), "3MF round trip"
    assert mm.source_info(tmp / "out.3mf").title == "out"
    # ...and it lands mid-bed, on the plate: a slicer puts (0, 0) at the bed's front-left corner
    on_bed = mm.load_model(tmp / "out.3mf", place=False)
    lo, hi = on_bed.bounds
    assert np.allclose((lo[:2] + hi[:2]) / 2, np.array(mm.printer.BED) / 2, atol=1e-3) and abs(lo[2]) < 1e-3, (lo, hi)
    raises(lambda: np.testing.assert_allclose(
        mm.load_model(mm.write_3mf(out, tmp / "raw.3mf", bed=None), place=False).bounds[0][:2], lo[:2], atol=1e-3),
        "a 3MF written with bed=None keeping the model's own place")

    # 4. a broken mesh -----------------------------------------------------------------
    holey = base.copy()
    holey.update_faces(np.arange(len(holey.faces)) != 3)  # drop one triangle: a gap in the skin
    assert not mm.health(holey).usable
    raises(lambda: mm.apply_changes(holey, cut=[hole]), "editing a mesh with a gap")
    assert mm.health(mm.repair(holey)).usable, "repair should close a one-triangle gap"

    # 5. the estimate -------------------------------------------------------------------
    thick = trimesh.creation.box((60, 60, 60))
    prof = pp.Profile(walls=3, infill=0.15)
    e3, e2 = pp.estimate(thick, prof), pp.estimate(thick, replace(prof, walls=2))
    assert e2.plastic_mm3 < e3.plastic_mm3, "fewer walls must use less plastic on a thick part"
    thin = trimesh.creation.box((60, 60, 1.0))  # thinner than the walls: all perimeter, infill irrelevant
    assert abs(pp.estimate(thin, replace(prof, infill=0.05)).plastic_mm3 - pp.estimate(thin, replace(prof, infill=0.5)).plastic_mm3) < 1e-6
    assert pp.read_profile(stl) is None and pp.read_profile(tmp / "out.3mf") is None

    # 6. sketches turned to the installed orientation ----------------------------------
    labels = {k: (Sketch("t", turn=k)._page_axis((1, 0)), Sketch("t", turn=k)._page_axis((0, 1))) for k in range(4)}
    assert labels == {0: ("+X", "+Y"), 1: ("-Y", "+X"), 2: ("-X", "-Y"), 3: ("+Y", "-X")}, labels
    sk = Sketch("t", turn=1)
    sk.circle(10, 0, 1, "part")       # a point on +X must land straight up the page
    sk.rect(0, -20, 4, 2, "part")     # a 4-wide rect on -Y must land to the right, 2 wide, 4 tall
    (b_circle, b_rect) = [b for _, b in sk._items]
    assert np.allclose(b_circle, (-1, 9, 1, 11)), b_circle
    assert np.allclose(b_rect, (19, -2, 21, 2)), b_rect
    raises(lambda: np.testing.assert_allclose(Sketch("t", turn=0)._t(10, 0), (0, 10)), "an unturned sketch moving a point")
    tube = trimesh.creation.annulus(r_min=8, r_max=10, height=30)  # an unrelated shape, sliced and turned
    sk = Sketch("t", axes=mm.section_axes("y"), turn=3, down=True)
    mm.draw_section(sk, tube, "y")
    xs0, ys0, xs1, ys1 = sk._bounds()
    assert abs((xs1 - xs0) - 30) < 0.5 and abs((ys1 - ys0) - 20) < 0.5, "a turned tube slice is 30 wide, 20 tall"
    assert "down</text>" in sk.to_svg()
    # down= picks the turn per view: in the view, down points down the page; looking along it, nothing turns
    assert (turn_for(("X", "Y"), "-X"), turn_for(("X", "Z"), "+Z"), turn_for(("Y", "Z"), "+Y")) == (1, 2, 3)
    assert turn_for(("X", "Y"), "-Z") is None and Sketch("t", axes=("X", "Y"), down="-Z").turn == 0
    for axes, d in ((("X", "Y"), "-X"), (("X", "Z"), "-Z"), (("Y", "Z"), "+Y")):
        sk = Sketch("t", axes=axes, down=d)
        assert sk.down and sk._page_axis((0, -1)) == ("-" if d[0] == "-" else "+") + d[1], (axes, d, sk.turn)
    assert "down</text>" not in Sketch("t", down="").to_svg() and not Sketch("t", down="-Z").down

    # 7. measuring along a line -------------------------------------------------------
    spans = mm.line_spans(tube, (0, 0, 0), (1, 0, 0))   # from the bore's centre (in air), across both walls
    assert np.allclose(spans, [(-10, -8), (8, 10)], atol=0.05), spans
    spans = mm.line_spans(tube, (9, 0, 0), (0, 0, 1))   # from inside the wall, along the tube's length
    assert np.allclose(spans, [(-15, 15)], atol=1e-6), spans
    assert mm.line_spans(tube, (50, 0, 0), (0, 1, 0)) == [], "a line that misses the part has no spans"
    raises(lambda: np.testing.assert_allclose(mm.line_spans(tube, (0, 0, 0), (1, 0, 0))[1], (7, 10), atol=0.05),
           "a wall measured 3 mm thick when it is 2")

    # 8. a test piece -------------------------------------------------------------------
    piece = mm.test_piece(tube, "z", 6.0, at=-12.0)            # 6 mm of the tube, near its bottom end
    assert np.allclose(piece.bounds[:, 2], (-15, -9), atol=1e-6), piece.bounds
    assert abs(piece.volume - tube.volume * 6 / 30) < 1.0 and len(piece.split(only_watertight=False)) == 1
    side = mm.test_piece(Box(40, 20, 10), "x", 4.0)              # a build123d shape, default: the middle
    assert np.allclose(side.extents, (4, 20, 10), atol=1e-6), side.extents
    raises(lambda: mm.test_piece(tube, "z", 5.0, at=100.0), "a test piece cut where there is no part")

    # 9. snapping an addition flush with the original -----------------------------------
    block = trimesh.creation.box((20, 20, 10.0))                  # top face at z = 5
    tab = trimesh.creation.box((20, 10, 10.0 + 2e-4))             # a tab lengthening it, a rounding error too tall
    tab.apply_translation((19, 0, 1e-4))                          # overlaps the block 1 mm, top at 5.0002

    def top_levels(m):
        return sorted({round(float(z), 6) for z in m.vertices[:, 2] if z > 4})
    assert top_levels(mm.apply_changes(block, add=[tab], snap=0.001)) == [5.0], "snapped: one flat top"
    raises(lambda: np.testing.assert_equal(top_levels(mm.apply_changes(block, add=[tab])), [5.0]),
           "an unsnapped addition a rounding error proud of the face")
    step = trimesh.creation.box((20, 10, 11.0))                    # a real 0.5 mm step must stay a step
    step.apply_translation((19, 0, 0.5))
    assert top_levels(mm.apply_changes(block, add=[step], snap=0.001)) == [5.0, 6.0]

    print("meshmod ok: bracket STL edit + probes, inch/mirrored 3MF, round trip, broken-mesh refusal, estimates, "
          "turned sketches, line spans, test piece, snap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
