"""Where part and assembly scripts live -- one lookup shared by the scripts/ tools.

A *part* is parts/<name>/<name>.py (one printable thing, possibly several
variants). An *assembly* is assemblies/<name>/<name>.py (several parts placed
together with reference geometry, checked for fit -- common/assembly.py).
Names are unique across both, so `render.py`, `view.py` and `build_all.py`
take either kind by name.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("parts", "assemblies")


def all_scripts() -> list[Path]:
    """Every part and assembly script, parts first; `templates/` folders excluded."""
    out = []
    for kind in KINDS:
        for s in sorted((ROOT / kind).glob("*/*.py")):
            if s.stem == s.parent.name and s.parent.name != "templates":
                out.append(s)
    names = [s.stem for s in out]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"name used by both a part and an assembly: {sorted(dupes)}"
    return out


def find_script(name: str) -> Path:
    for s in all_scripts():
        if s.stem == name:
            return s
    raise SystemExit(f"no part or assembly named {name!r} (looked in {', '.join(KINDS)}/)")


def kind_of(script: Path) -> str:
    return script.parent.parent.name  # "parts" or "assemblies"
