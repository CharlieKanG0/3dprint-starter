"""Print settings of a downloaded 3MF, and a first-order filament / time estimate for changing them.

Two jobs, both for "I want to print someone else's model on MY printer, with less plastic and less time":

  1. `read_profile(path)` -- what the creator sliced the file with (printer, filament, walls, infill,
     speeds) and what that cost (grams, seconds). Bambu Studio / Orca 3MFs carry this; plain STLs and
     geometry-only 3MFs return None.
  2. `estimate(mesh, ...)` -- grams and relative print time for a set of settings, from the mesh alone,
     so walls/infill/layer options can be compared before slicing. It is a ballpark (see `estimate`);
     the slicer's own number is the final word.

Nothing here is specific to one model or printer. Densities are typical datasheet values (ASSUMED --
check the spool).
"""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

# g/cm^3, typical datasheet values -- ASSUMED, check your spool.
DENSITY = {"PLA": 1.24, "PETG": 1.27, "ASA": 1.07, "ABS": 1.05, "TPU": 1.21, "PETG-CF": 1.30, "ASA-CF": 1.12, "PLA-CF": 1.30}


@dataclass(frozen=True)
class Profile:
    """Slicing settings (the fields that decide plastic use and time) plus the creator's result."""
    printer: str = ""
    nozzle: float = 0.4
    filament: str = ""  # material the sliced plate used, e.g. "PLA"
    layer_height: float = 0.2
    line_width: float = 0.42
    walls: int = 2
    top_layers: int = 5
    bottom_layers: int = 5
    infill: float = 0.15  # fraction
    infill_pattern: str = ""
    supports: bool = False
    outer_wall_speed: float = 0.0  # mm/s
    inner_wall_speed: float = 0.0
    infill_speed: float = 0.0
    acceleration: float = 0.0
    slicer: str = ""
    weight_g: float | None = None  # the creator's slice result, if the file has one
    time_s: float | None = None

    def summary(self) -> list[str]:
        lines = [
            f"sliced for {self.printer or '?'} ({self.nozzle:g} mm nozzle) in {self.filament or '?'} with {self.slicer or 'unknown slicer'}",
            f"{self.layer_height:g} mm layers, {self.walls} walls, {self.infill:.0%} {self.infill_pattern or ''} infill, "
            f"{self.top_layers} top / {self.bottom_layers} bottom layers, {'with' if self.supports else 'no'} supports",
        ]
        if self.outer_wall_speed:
            lines.append(f"speeds: outer wall {self.outer_wall_speed:g}, inner wall {self.inner_wall_speed:g}, "
                         f"infill {self.infill_speed:g} mm/s; acceleration {self.acceleration:g} mm/s^2")
        if self.weight_g is not None and self.time_s is not None:
            lines.append(f"their result: {self.weight_g:.0f} g, {self.time_s / 3600:.1f} h")
        return lines


def _num(settings: dict, key: str, default: float = 0.0) -> float:
    v = settings.get(key, default)
    if isinstance(v, list):
        v = v[0] if v else default
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else float(default)


def read_profile(path: str | Path) -> Profile | None:
    """The slicing settings stored in a Bambu Studio / Orca 3MF, or None if the file has none."""
    path = Path(path)
    if path.suffix.lower() != ".3mf":
        return None
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if "Metadata/project_settings.config" not in names:
            return None
        s = json.loads(zf.read("Metadata/project_settings.config"))
        app = ""
        if "3D/3dmodel.model" in names:
            m = re.search(rb'<metadata name="Application">([^<]*)<', zf.read("3D/3dmodel.model")[:4000])
            app = m.group(1).decode() if m else ""
        weight = seconds = None
        filament = ""
        if "Metadata/slice_info.config" in names:
            root = ET.fromstring(zf.read("Metadata/slice_info.config"))
            for meta in root.iter("metadata"):
                if meta.get("key") == "weight":
                    weight = float(meta.get("value"))
                if meta.get("key") == "prediction":
                    seconds = float(meta.get("value"))
            fil = root.find(".//filament")
            if fil is not None:
                filament = fil.get("type", "")
        if not filament:
            types = s.get("filament_type") or [""]
            filament = types[0] if isinstance(types, list) else str(types)
    return Profile(
        printer=str(s.get("printer_settings_id") or s.get("printer_model") or ""),
        nozzle=_num(s, "nozzle_diameter", 0.4),
        filament=filament,
        layer_height=_num(s, "layer_height", 0.2),
        line_width=_num(s, "outer_wall_line_width", _num(s, "line_width", 0.42)),
        walls=int(_num(s, "wall_loops", 2)),
        top_layers=int(_num(s, "top_shell_layers", 5)),
        bottom_layers=int(_num(s, "bottom_shell_layers", 5)),
        infill=_num(s, "sparse_infill_density", 15) / 100,
        infill_pattern=str(s.get("sparse_infill_pattern", "")),
        supports=bool(int(_num(s, "enable_support", 0))),
        outer_wall_speed=_num(s, "outer_wall_speed"),
        inner_wall_speed=_num(s, "inner_wall_speed"),
        infill_speed=_num(s, "sparse_infill_speed"),
        acceleration=_num(s, "default_acceleration"),
        slicer=app,
        weight_g=weight,
        time_s=seconds,
    )


@dataclass(frozen=True)
class Estimate:
    plastic_mm3: float
    shell_mm3: float  # walls + top/bottom skin
    infill_mm3: float
    grams: float
    seconds: float

    @property
    def solid_share(self) -> float:
        """How much of the plastic is walls and skin (infill cannot reduce this part)."""
        return self.shell_mm3 / self.plastic_mm3 if self.plastic_mm3 else 0.0


def estimate(mesh, profile: Profile, material: str | None = None, flow_mm3_s: float = 9.0) -> Estimate:
    """Plastic, grams and print time for `mesh` sliced with `profile`. A BALLPARK (about +-25%), for
    comparing settings against each other, not for quoting a number:

      walls    = surface area x (walls x line width), capped at the part's volume (a thin wall is
                 all perimeter: infill never happens)
      skin     = flat top/bottom area x (shell layers x layer height - wall depth), if positive
      infill   = what is left x infill density
      time     = plastic volume / `flow_mm3_s`, an AVERAGE rate that includes slow corners, travel and
                 layer changes. `calibrate_flow` derives it from a file that carries its own
                 result; otherwise 9 mm^3/s is a typical X1/P-series figure (ASSUMED).
    """
    volume = float(mesh.volume)
    area = float(mesh.area)
    wall_depth = profile.walls * profile.line_width
    shell = min(volume, area * wall_depth)
    flat = np.abs(mesh.face_normals[:, 2]) > 0.95  # faces that are (nearly) horizontal
    flat_area = float(mesh.area_faces[flat].sum())
    skin_depth = max(profile.top_layers, profile.bottom_layers) * profile.layer_height
    skin = min(volume - shell, flat_area * max(0.0, skin_depth - wall_depth))
    infill = max(0.0, volume - shell - skin) * profile.infill
    plastic = shell + skin + infill
    density = DENSITY.get(material or profile.filament, 1.24)
    return Estimate(plastic, shell + skin, infill, plastic * density / 1000.0, plastic / flow_mm3_s)


def calibrate_flow(mesh, profile: Profile) -> tuple[float, float]:
    """(average flow in mm^3/s, weight error) so `estimate` matches the creator's own slice of this
    mesh. The error is the estimate's grams versus the file's grams BEFORE calibration -- a quick
    check on how trustworthy the model-based estimate is for this shape."""
    if not (profile.weight_g and profile.time_s):
        raise ValueError("this file has no slice result to calibrate against")
    est = estimate(mesh, profile)
    mm3_real = profile.weight_g * 1000.0 / DENSITY.get(profile.filament, 1.24)
    return mm3_real / profile.time_s, est.grams / profile.weight_g - 1.0


def compare(mesh, base: Profile, options: list[tuple[str, Profile]], material: str | None = None,
            flow_mm3_s: float = 9.0) -> list[tuple[str, Estimate]]:
    """Estimate each (label, profile) option, baseline first. Use `replace(base, walls=2, infill=0.10)`."""
    rows = [("as downloaded", estimate(mesh, base, material, flow_mm3_s))]
    rows += [(label, estimate(mesh, p, material, flow_mm3_s)) for label, p in options]
    return rows


__all__ = ["DENSITY", "Profile", "Estimate", "read_profile", "estimate", "calibrate_flow", "compare", "replace"]
