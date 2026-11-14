"""Start a new part or assembly from its template.

    ./venv/bin/python scripts/new.py part <name>        # parts/<name>/<name>.py + layout.py
    ./venv/bin/python scripts/new.py assembly <name>    # assemblies/<name>/<name>.py
    ./venv/bin/python scripts/new.py thing <name>       # things/<name>.py: a real object your parts fit
    ./venv/bin/python scripts/new.py mod <name> <file>  # modify a downloaded .3mf/.stl (docs/modifying.md)

<name> is snake_case and must not already be used by a part or an assembly
(scripts find either kind by name -- common/project.py). The part also gets a
layout.py for the "sketch before you model" step (CLAUDE.md step 0) and a
Backlog line in parts/BACKLOG.md.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.project import all_scripts  # noqa: E402


def new_thing(name: str) -> int:
    path = ROOT / "things" / f"{name}.py"
    if path.exists():
        sys.exit(f"things/{name}.py already exists -- add to it")
    text = (ROOT / "things/templates/thing_template.py").read_text()
    path.write_text(text.replace("<Thing name>", name.replace("_", " ").capitalize()).replace("<name>", name))
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts/things.py"), "--write"], check=True)
    print(f"created things/{name}.py -- fill in the numbers with their source tags; parts import from it")
    return 0


def new_mod(name: str, source: str) -> int:
    """parts/<name>/ for modifying a downloaded model: a copy of the file, an inspection report, a layout
    that already draws the model's slices, and a part script that loads it (docs/modifying.md)."""
    src = Path(source).expanduser().resolve()
    if not src.is_file() or src.suffix.lower() not in (".3mf", ".stl"):
        sys.exit(f"{source}: give the path of a downloaded .3mf or .stl file")
    if name in {s.stem for s in all_scripts()}:
        sys.exit(f"{name!r} already exists")
    folder = ROOT / "parts" / name
    (folder / "source").mkdir(parents=True)
    fname = re.sub(r"[^A-Za-z0-9_.-]+", "_", src.name)
    shutil.copy2(src, folder / "source" / fname)
    print(f"copied the download to {(folder / 'source' / fname).relative_to(ROOT)}")
    title = name.replace("_", " ").capitalize()
    for dst, tmpl in ((folder / f"{name}.py", "mod_template.py"), (folder / "layout.py", "mod_layout_template.py")):
        text = (ROOT / "parts/templates" / tmpl).read_text()
        for placeholder, value in (("<source_file>", fname), ("<part_name>", name), ("<name>", name), ("<Part name>", title), ("<Part>", title)):
            text = text.replace(placeholder, value)
        dst.write_text(text)
        print(f"created {dst.relative_to(ROOT)}")
    report = subprocess.run([sys.executable, str(ROOT / "scripts/inspect_model.py"), str(src), "--write", str(folder / "report.md")],
                            capture_output=True, text=True)
    if report.returncode != 0:
        print(f"could not inspect the file:\n{report.stderr.strip()[-600:]}")
    else:
        print(f"created {(folder / 'report.md').relative_to(ROOT)} (read it: size, condition, the creator's print settings)")
    backlog = ROOT / "parts/BACKLOG.md"
    text = backlog.read_text()
    if "## Backlog\n" in text:
        line = f"- **{name}** -- TODO modify downloaded `{fname}`. `parts/{name}/`\n"
        backlog.write_text(text.replace("## Backlog\n\n", f"## Backlog\n\n{line}", 1))
        print(f"added {name} to parts/BACKLOG.md")
    print(f"\nnext: run parts/{name}/layout.py (it draws the model's slices), then sketch lettered options for the change, "
          f"get the user's letter + corrections, set CONFIRMED -- the part script won't build until then")
    return 0


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "mod":
        if not re.fullmatch(r"[a-z][a-z0-9_]*", sys.argv[2]) or sys.argv[2] == "templates":
            sys.exit(f"{sys.argv[2]!r}: use snake_case, e.g. pole_clamp")
        return new_mod(sys.argv[2], sys.argv[3])
    if len(sys.argv) != 3 or sys.argv[1] not in ("part", "assembly", "thing"):
        print(__doc__)
        return 2
    kind, name = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name == "templates":
        sys.exit(f"{name!r}: use snake_case, e.g. phone_holder")
    if kind == "thing":
        return new_thing(name)
    if name in {s.stem for s in all_scripts()}:
        sys.exit(f"{name!r} already exists")

    folder = ROOT / ("parts" if kind == "part" else "assemblies") / name
    title = name.replace("_", " ").capitalize()
    folder.mkdir(parents=True)
    if kind == "part":
        files = {
            folder / f"{name}.py": ROOT / "parts/templates/part_template.py",
            folder / "layout.py": ROOT / "parts/templates/layout_template.py",
        }
    else:
        files = {folder / f"{name}.py": ROOT / "assemblies/templates/assembly_template.py"}
    for dst, src in files.items():
        text = src.read_text()
        for placeholder in ("<part_name>", "<name>"):
            text = text.replace(placeholder, name)
        for placeholder in ("<Part name>", "<Assembly name>", "<Part>"):
            text = text.replace(placeholder, title)
        dst.write_text(text)
        print(f"created {dst.relative_to(ROOT)}")

    if kind == "part":
        backlog = ROOT / "parts/BACKLOG.md"
        text = backlog.read_text()
        line = f"- **{name}** -- TODO one-line description. `parts/{name}/`\n"
        if "## Backlog\n" in text:
            text = text.replace("## Backlog\n\n", f"## Backlog\n\n{line}", 1)
            backlog.write_text(text)
            print(f"added {name} to parts/BACKLOG.md")
        print(f"\nnext: sketch lettered layouts in parts/{name}/layout.py, run it, look at layout*.svg, get the user's "
              f"letter + corrections, set CONFIRMED there -- the part script won't build until then")
    return 0


if __name__ == "__main__":
    sys.exit(main())
