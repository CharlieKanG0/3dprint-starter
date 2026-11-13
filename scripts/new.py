"""Start a new part or assembly from its template.

    ./venv/bin/python scripts/new.py part <name>        # parts/<name>/<name>.py + layout.py
    ./venv/bin/python scripts/new.py assembly <name>    # assemblies/<name>/<name>.py

<name> is snake_case and must not already be used by a part or an assembly
(scripts find either kind by name -- common/project.py). The part also gets a
layout.py for the "sketch before you model" step (CLAUDE.md step 0) and a
Backlog line in parts/BACKLOG.md.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.project import all_scripts  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("part", "assembly"):
        print(__doc__)
        return 2
    kind, name = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name == "templates":
        sys.exit(f"{name!r}: use snake_case, e.g. phone_holder")
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
