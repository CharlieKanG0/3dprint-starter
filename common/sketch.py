"""Labelled 2D layout schematics (SVG) for the "sketch before you model" step.

Work in millimetres, +X right, +Y up (the same axes as the part). The helper
handles scale, the flipped SVG Y axis, arrowheads, label halos and a legend, so
a schematic is a few lines of positions and dimensions:

    sk = Sketch("Bracket -- top view")
    sk.rect(0, 0, 70, 230, "existing", label="rail (runs along Y)")
    sk.circle(-135, 0, 5, "hardware")
    sk.dim((-135, 0), (135, 0), "270 pin spacing", offset=40)
    sk.save("layout.svg")

View it by opening the .svg in a browser (`open layout.svg` on macOS).
Roles (colours) are defined in ROLES; add a role there rather than passing colours.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

# role -> (legend label, fill/stroke colour, fill opacity)
ROLES: dict[str, tuple[str, str, float]] = {
    "existing": ("existing structure (not printed)", "#9aa0a6", 0.55),
    "feature": ("feature on existing structure (channel, slot, hole)", "#5f6368", 0.9),
    "part": ("printed part", "#2563eb", 0.35),
    "cutout": ("hole / slot in printed part", "#1e3a8a", 0.9),
    "hardware": ("mating hardware (bolt, pin, nut)", "#dc2626", 0.9),
    "carried": ("item the part holds or carries", "#16a34a", 0.25),
    "guide": ("axis / reference line", "#059669", 1.0),
}


class Sketch:
    def __init__(self, title: str, size: float = 300.0, axes: tuple[str, str] = ("X", "Y")):
        """`size` = rough overall extent of the drawing in mm; it sets the text size.
        `axes` names the horizontal and vertical axes of this view, e.g. ("X", "Z") for a side view."""
        self.axes = axes
        self._notes: list[str] = []
        self.title = title
        self.fs = size / 55  # text height in mm
        self._items: list[tuple[str, tuple[float, float, float, float] | None]] = []  # (svg, bbox)
        self._roles_used: list[str] = []

    # -- coordinate + bookkeeping helpers ---------------------------------
    @staticmethod
    def _p(x: float, y: float) -> str:
        return f"{x:.2f},{-y:.2f}"

    def _use(self, role: str) -> tuple[str, float]:
        if role not in ROLES:
            raise KeyError(f"unknown role {role!r}; add it to ROLES in common/sketch.py")
        if role not in self._roles_used:
            self._roles_used.append(role)
        return ROLES[role][1], ROLES[role][2]

    def _add(self, svg: str, bbox) -> None:
        self._items.append((svg, bbox))

    def _bounds(self) -> tuple[float, float, float, float]:
        boxes = [b for _, b in self._items if b]
        if not boxes:
            return (-50, -50, 50, 50)
        return (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes))

    # -- shapes -----------------------------------------------------------
    def rect(self, cx, cy, w, h, role, label=None, angle=0.0, dashed=False, r=0.0):
        col, op = self._use(role)
        rot = f' transform="rotate({-angle:.2f} {cx:.2f} {-cy:.2f})"' if angle else ""
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self._add(
            f'<rect x="{cx - w / 2:.2f}" y="{-cy - h / 2:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="{r:.2f}" fill="{col}" fill-opacity="{op}" stroke="{col}" stroke-width="0.8"{dash}{rot}/>',
            (cx - math.hypot(w, h) / 2, cy - math.hypot(w, h) / 2, cx + math.hypot(w, h) / 2, cy + math.hypot(w, h) / 2)
            if angle else (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
        )
        if label:
            self.text(cx, cy, label)

    def slot(self, cx, cy, length, width, role, angle=0.0, label=None):
        """Rounded slot, `length` along its axis (angle 0 = along X)."""
        self.rect(cx, cy, length, width, role, label=label, angle=angle, r=width / 2)

    def circle(self, cx, cy, r, role, label=None):
        col, op = self._use(role)
        self._add(
            f'<circle cx="{cx:.2f}" cy="{-cy:.2f}" r="{r:.2f}" fill="{col}" fill-opacity="{op}" '
            f'stroke="{col}" stroke-width="0.8"/>',
            (cx - r, cy - r, cx + r, cy + r),
        )
        if label:
            self.text(cx, cy - r - self.fs, label)

    def bar(self, a, b, width, role):
        """Thick line with round ends (an arm, a strap)."""
        col, op = self._use(role)
        self._add(
            f'<line x1="{a[0]:.2f}" y1="{-a[1]:.2f}" x2="{b[0]:.2f}" y2="{-b[1]:.2f}" stroke="{col}" '
            f'stroke-opacity="{op}" stroke-width="{width:.2f}" stroke-linecap="round"/>',
            (min(a[0], b[0]) - width / 2, min(a[1], b[1]) - width / 2,
             max(a[0], b[0]) + width / 2, max(a[1], b[1]) + width / 2),
        )

    def line(self, a, b, role="guide", dashed=True):
        col, _ = self._use(role)
        dash = ' stroke-dasharray="8 5"' if dashed else ""
        self._add(
            f'<line x1="{a[0]:.2f}" y1="{-a[1]:.2f}" x2="{b[0]:.2f}" y2="{-b[1]:.2f}" '
            f'stroke="{col}" stroke-width="1"{dash}/>',
            (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])),
        )

    def text(self, x, y, s, anchor="middle", bold=False, size=None):
        fs = size or self.fs
        w = len(s) * fs * 0.55
        x0 = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
        weight = ' font-weight="700"' if bold else ""
        self._add(
            f'<text x="{x:.2f}" y="{-y + fs * 0.35:.2f}" font-size="{fs:.2f}" text-anchor="{anchor}"{weight} '
            f'font-family="Helvetica, Arial, sans-serif" fill="#111" paint-order="stroke" stroke="#fff" '
            f'stroke-width="{fs * 0.3:.2f}" stroke-linejoin="round">{escape(s)}</text>',
            (x0, y - fs, x0 + w, y + fs),
        )

    def dim(self, a, b, text, offset=20.0):
        """Dimension from point a to b, drawn `offset` mm to the left of the a->b direction."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        sgn = 1 if offset >= 0 else -1
        a2 = (a[0] + nx * offset, a[1] + ny * offset)
        b2 = (b[0] + nx * offset, b[1] + ny * offset)
        ext = self.fs * 0.6 * sgn
        ah = self.fs * 0.9  # arrowhead length

        def arrow(tip, direction):
            tx, ty = tip
            ux_, uy_ = direction
            bx, by = tx - ux_ * ah, ty - uy_ * ah
            px, py = -uy_ * ah * 0.3, ux_ * ah * 0.3
            return f"{self._p(tx, ty)} {self._p(bx + px, by + py)} {self._p(bx - px, by - py)}"

        parts = [
            f'<g stroke="#111" stroke-width="0.7" fill="#111">',
            f'<line x1="{a[0]:.2f}" y1="{-a[1]:.2f}" x2="{a2[0] + nx * ext:.2f}" y2="{-(a2[1] + ny * ext):.2f}" fill="none"/>',
            f'<line x1="{b[0]:.2f}" y1="{-b[1]:.2f}" x2="{b2[0] + nx * ext:.2f}" y2="{-(b2[1] + ny * ext):.2f}" fill="none"/>',
            f'<line x1="{a2[0]:.2f}" y1="{-a2[1]:.2f}" x2="{b2[0]:.2f}" y2="{-b2[1]:.2f}" fill="none"/>',
            f'<polygon points="{arrow(a2, (-ux, -uy))}"/>',
            f'<polygon points="{arrow(b2, (ux, uy))}"/>',
            "</g>",
        ]
        mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
        # keep the label horizontal and nudge it off the line, away from the part
        self._add("".join(parts), (min(a2[0], b2[0]) - ah, min(a2[1], b2[1]) - ah, max(a2[0], b2[0]) + ah, max(a2[1], b2[1]) + ah))
        horiz = abs(dx) >= abs(dy)
        tx, ty = (mx, my + sgn * self.fs * 1.1) if horiz else (mx + sgn * -1 * self.fs * 0.2, my)
        if horiz:
            self.text(tx, ty, text, bold=True)
        else:
            # vertical dimension: label to the side of the line
            side = 1 if nx * sgn >= 0 else -1
            self.text(mx + side * self.fs * 0.8, my, text, anchor="start" if side > 0 else "end", bold=True)

    def notes(self, *lines: str) -> None:
        """Lines printed under the legend. Use them to state where each dimension came from
        (measured / datasheet / assumed) and what is still unknown."""
        self._notes += list(lines)

    # -- output -----------------------------------------------------------
    def to_svg(self) -> str:
        fs = self.fs
        x0, y0, x1, y1 = self._bounds()
        pad = fs * 3
        legend_h = fs * 1.7 * (len(self._roles_used) + len(self._notes) + 2)
        vx, vy = x0 - pad, -(y1 + pad + fs * 2.5)  # extra top room for the title
        vw = (x1 - x0) + 2 * pad
        text_w = max((len(n) for n in self._notes + [self.title]), default=0) * fs * 0.62 + 2 * fs
        vw = max(vw, text_w + fs)  # long notes/title must not run off the right edge
        vh = (y1 - y0) + 2 * pad + fs * 2.5 + legend_h

        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}" '
            f'preserveAspectRatio="xMidYMid meet" style="width:100vw;height:100vh;display:block">',
            f'<rect x="{vx:.2f}" y="{vy:.2f}" width="{vw:.2f}" height="{vh:.2f}" fill="#fff"/>',
            f'<text x="{x0 - pad + fs:.2f}" y="{-(y1 + pad) - fs * 0.6:.2f}" font-size="{fs * 1.4:.2f}" font-weight="700" '
            f'font-family="Helvetica, Arial, sans-serif" fill="#111">{escape(self.title)}</text>',
        ]
        out += [svg for svg, _ in self._items]

        # axes indicator, bottom-right of the drawing
        ax, ay, L = x1 - fs * 2, y0 - pad * 0.2, fs * 4
        out.append(
            f'<g stroke="#111" stroke-width="0.8" font-family="Helvetica, Arial, sans-serif" font-size="{fs:.2f}" fill="#111">'
            f'<line x1="{ax:.2f}" y1="{-ay:.2f}" x2="{ax + L:.2f}" y2="{-ay:.2f}"/>'
            f'<line x1="{ax:.2f}" y1="{-ay:.2f}" x2="{ax:.2f}" y2="{-(ay + L):.2f}"/>'
            f'<text x="{ax + L + fs * 0.4:.2f}" y="{-ay + fs * 0.35:.2f}" stroke="none">+{self.axes[0]}</text>'
            f'<text x="{ax - fs * 0.6:.2f}" y="{-(ay + L) - fs * 0.5:.2f}" stroke="none">+{self.axes[1]}</text></g>'
        )

        # legend, below the drawing
        ly = -(y0 - pad) + fs
        for i, role in enumerate(self._roles_used):
            label, col, op = ROLES[role]
            yy = ly + i * fs * 1.7
            out.append(
                f'<rect x="{x0 - pad + fs:.2f}" y="{yy:.2f}" width="{fs * 1.6:.2f}" height="{fs:.2f}" fill="{col}" '
                f'fill-opacity="{op}" stroke="{col}" stroke-width="0.6"/>'
                f'<text x="{x0 - pad + fs * 3.2:.2f}" y="{yy + fs * 0.85:.2f}" font-size="{fs:.2f}" '
                f'font-family="Helvetica, Arial, sans-serif" fill="#111">{escape(label)}</text>'
            )
        ny = ly + len(self._roles_used) * fs * 1.7 + fs * 0.6
        for k, line in enumerate(self._notes):
            out.append(
                f'<text x="{x0 - pad + fs:.2f}" y="{ny + k * fs * 1.6 + fs * 0.85:.2f}" font-size="{fs:.2f}" '
                f'font-family="Helvetica, Arial, sans-serif" fill="#444">{escape(line)}</text>'
            )
        out.append("</svg>")
        return "\n".join(out)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.to_svg())
        return path
